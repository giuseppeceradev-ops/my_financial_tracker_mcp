
import logging
from fastmcp.exceptions import ToolError
from datetime import datetime
import os

from my_financial_tracker_mcp.llm.llm import llm_call, parse_llm_json
from my_financial_tracker_mcp.database.receipts import ReceiptsDatabase
from my_financial_tracker_mcp.database.categories import CategoriesDatabase
from my_financial_tracker_mcp.prompt.categories import build_category_prompt
from my_financial_tracker_mcp.prompt.receipts import build_receipt_prompt
from my_financial_tracker_mcp.validators.receipts import validate_receipt
from my_financial_tracker_mcp.services.google_vision import get_text
from my_financial_tracker_mcp.services.google_drive import DriveService

logger = logging.getLogger(__name__)
DRIVE_RECEIPTS_FOLDER = os.getenv("DRIVE_RECEIPTS_FOLDER")

class Receipts:

    def __init__(
        self, 
        drive_service: DriveService, 
        receipts_database: ReceiptsDatabase,
        categories_database: CategoriesDatabase
    ):

        self.drive_service = drive_service
        self.receipts_database = receipts_database
        self.categories_database = categories_database

    async def prepare_transation(
        self,
        amount: float,
        description: str,
        company: str | None = None,
        timestamp: str | None = None
    ):

        # -------------------------
        # Category
        # -------------------------

        category = await llm_call(build_category_prompt(description))

        logger.info(f"Prepared transaction \"{description}\" of {amount} euro, cagory found {category}")
        
        return {
            "amount": amount,
            "description": description,
            "category": category,
            "company": company,
            "timestamp": timestamp,
            "required_confirmation_by_user": True,
        }

    async def commit_transation(
        self,
        amount: float,
        description: str,
        company: str | None = None,
        timestamp: str | None = None,
        category: str | None = None
    ):

        category_id = await self.categories_database.resolve_category_id(category)
        category = self.categories_database.get_category(category_id)

        category_desc = category[1]

        receipt_id = self.receipts_database.create_receipt(
            company=company,
            timestamp=timestamp,
            amount=amount,
            description=description
        )

        tx_id, receipt_id = self.receipts_database.add_receipt_item(
            amount=amount,
            description=description,
            category_id=category_id,
            receipt_id=receipt_id
        )

        logger.info(f"Committed transaction {tx_id} with category {category_desc}")

        return {
            "id": tx_id,
            "amount": amount,
            "description": description,
            "category": category,
            "company": company,
            "invoice_id": receipt_id,
        }

    async def update_receipt_item(
        self,
        id: int,
        amount: float,
        description: str,
        category: str
    ):

        category_id = self.receipts_database.resolve_category_id(category)

        updated = self.receipts_database.update_transaction(
            id=id,
            amount=amount,
            description=description,
            category_id=category_id
        )

        logger.info(f"Updated receipt item (id->{id}, description->{description}, amount->{amount}")

        return {
            "id": id,
            "updated": bool(updated)
        }

    async def get_receipt_items(
        self,
        id:int = None,
        receipt_id: int = None,
        category: str = None,
        start_date: str = None,
        end_date: str = None
    ):

        category_id = (
            await self.categories_database.resolve_category_id(category)
            if category else None
        )

        logger.info(f"Fetching receipts items: id->{id}, receipt_id->{receipt_id}, category->{category}-{category_id}, start_date->{start_date}, end_date->{end_date}")

        rows = self.receipts_database.filter_transactions(
            id=id,
            receipt_id=receipt_id,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date
        )

        return [
            {
                "transaction_id": r[0],
                "amount": r[1],
                "description": r[2],
                "category_id": r[3],
                "receipt_id": r[4],
                "company": r[5],
                "currency": r[6],
                "timestamp": r[7],
                "receipt_total": r[8],
            }
            for r in rows
        ]

    async def prepare_receipt(
        self,
        image_path: str,
        description: str
    ):

        # -------------------------
        # 1. OCR
        # -------------------------
        text = await get_text(image_path)

        logger.info("OCR completed")

        if not text or not text.strip():
            raise ToolError("OCR returned empty text")

        # -------------------------
        # 2. LLM
        # -------------------------
        ai_response = await llm_call(build_receipt_prompt(text, description))

        logger.info(f"LLM RAW:\n{ai_response}")

        # -------------------------
        # 3. PARSING JSON
        # -------------------------
        try:
            data = parse_llm_json(ai_response)
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            raise ToolError("Failed to parse LLM output")

        # -------------------------
        # 4. VALIDAZIONE
        # -------------------------
        data = validate_receipt(data)

        timestamp=datetime.now().isoformat()

        if not data.get("items"):
            raise ToolError("No valid items extracted")

        if data.get("date"):
            timestamp = data.get("date")

        logger.info(f"Prepared receipt of {data.get("company")} on {timestamp}")

        return {
            "data": data,
            "timestamp": timestamp,
            "image_path": image_path,
            "required_confirmation_by_user": True,
        }

    async def commit_receipt(
        self,
        data,
        timestamp: str,
        image_path: str
    ):
    # -------------------------
        # 5. CREATE RECEIPT
        # -------------------------
        receipt_id = self.receipts_database.create_receipt(
            company=data.get("company"),
            description=data.get("description"),
            timestamp = timestamp,
            amount=data.get("total")
        )

        results = []

        # -------------------------
        # 6. INSERT TRANSACTIONS
        # -------------------------
        for item in data["items"]:
            category_id = self.receipts_database.resolve_category_id(item.get("category"))

            tx_id, _ = self.receipts_database.add_receipt_item(
                amount=item["amount"],
                description=item["description"],
                category_id=category_id,
                receipt_id=receipt_id
            )

            results.append(tx_id)
        
        # 
        
        self.drive_service.upload_file(str(image_path), DRIVE_RECEIPTS_FOLDER, datetime.fromisoformat(timestamp))

        logger.info(f"Committed receipt of {data.get("company")} on {timestamp}")

        # -------------------------
        # 7. OUTPUT
        # -------------------------
        return {
            "receipt_id": receipt_id,
            "transactions": results,
            "parsed": data,
        }
        
    def filter_receipts(
            self,
            id:int = None, 
            start_date: str = None, 
            end_date: str = None
    ):
        rows = self.receipts_database.filter_receipts(id, start_date, end_date)
        logger.info(f"Getting receipts: id -> {id}, start_date = {start_date}, end_date= {end_date}")

        return [
            {
                "id": r[0], 
                "description": r[1], 
                "company": r[2], 
                "total_amount": r[3],
                "currency": r[4], 
                "timestamp": r[5]
            }
            for r in rows
        ]       

    def update_receipt(
        self,
        id: int,
        description:str,
        company:str,
        amount: float,
        timestamp: str
    ):
        self.receipts_database.update_receipt(id, description, company, amount, timestamp)
        logger.info(f"Updated receipt (id->{id}, description->{description}, company->{company}, amount->{amount}, timestamp->{timestamp}")

    def add_receipt_item(
        self,
        description: str,
        amount: float,
        category_id: float,
        receipt_id: int,
        category: str
    ):
        category_id = self.receipts_database.resolve_category_id(category)
        self.receipts_database.add_receipt_item(amount, description, category_id, receipt_id)
        logger.info(f"Added receipt item (description->{description}, amount->{amount}, category->{category}")
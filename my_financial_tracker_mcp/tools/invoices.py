import logging
from fastmcp.exceptions import ToolError
from datetime import datetime
import os 

from my_financial_tracker_mcp.llm.llm import llm_call, parse_llm_json
from my_financial_tracker_mcp.prompt.invoices import build_invoice_prompt
from my_financial_tracker_mcp.validators.invoices import validate_invoice
from my_financial_tracker_mcp.database.invoices import InvoicesDatabase

from my_financial_tracker_mcp.services.google_vision import get_text
from my_financial_tracker_mcp.services.google_drive import DriveService
from my_financial_tracker_mcp.services.google_calendar import CalendarService
from my_financial_tracker_mcp.services.financial_events import FinancialEventsService

logger = logging.getLogger(__name__)
DRIVE_INVOICES_FOLDER = os.getenv("DRIVE_INVOICES_FOLDER")

class Invoices:
    def __init__(
        self, 
        drive_service: DriveService, 
        calendar_service: CalendarService,
        invoices_database: InvoicesDatabase,
        financial_events_service: FinancialEventsService):
        self.invoices_database = invoices_database
        self.drive_service = drive_service
        self.calendar_service = calendar_service
        self.financial_events_service = financial_events_service

    async def prepare_invoice(
        self,
        image_path: str,
        description: str = ""
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
        ai_response = await llm_call(build_invoice_prompt(text, description))

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
        data = validate_invoice(data)

        emission_date = due_date = datetime.now().isoformat()

        if not data.get("items"):
            raise ToolError("No valid items extracted")

        if data.get("emission_date"):
            emission_date = data.get("emission_date")

        if data.get("due_date"):
            due_date = data.get("due_date")

        logger.info(f"Prepared invoice of {data.get("company")} on {emission_date} - {due_date}")

        return {
            "data": data,
            "image_path": image_path,
            "required_confirmation_by_user": True,
        }

    async def commit_invoice(
        self,
        data,
        image_path: str
    ):
    # -------------------------
        # 5. CREATE RECEIPT
        # -------------------------
        emission_date = data.get("emission_date")
        due_date=data.get("due_date")
        is_incoming=data.get("incoming")
        total_amount=data.get("total")

        invoice_id = self.invoices_database.create_invoice(
            company=data.get("company"),
            description=data.get("description"),
            total_amount=total_amount,
            emission_date= emission_date,
            due_date=due_date,
            currency="EUR",
            closed=False,
            incoming=is_incoming
        )

        results = []

        # -------------------------
        # 6. INSERT TRANSACTIONS
        # -------------------------
        for item in data["items"]:

            tx_id, _ = self.invoices_database.add_invoice_item(
                amount=item["amount"],
                description=item["description"],
                invoice_id=invoice_id
            )

            results.append(tx_id)
        
        # 
        
        self.drive_service.upload_file(str(image_path), DRIVE_INVOICES_FOLDER, datetime.fromisoformat(emission_date))

        if data.get("incoming"):
            await self.financial_events_service.add_supplier_invoice_to_calendar(amount=total_amount, due_date=due_date, invoice_id=invoice_id)
        else:
            await self.financial_events_service.add_customer_invoice_to_calendar(amount=total_amount, due_date=due_date, invoice_id=invoice_id)

        logger.info(f"Committed invoice of {data.get("company")} on {emission_date} - {due_date}")

        # -------------------------
        # 7. OUTPUT
        # -------------------------
        return {
            "receipt_id": invoice_id,
            "transactions": results,
            "parsed": data,
        }

    def update_invoice(
            self,
            id: int,
            amount: float,
            incoming: bool,
            closed: bool
        ):
            self.invoices_database.update_invoice(id, amount, incoming, closed)
            logger.info(f"Updated invoice -> {id}")    

    def filter_invoices(
            self,
            id:int = None, 
            incoming: bool = None,
            closed:bool = None, 
            start_date: str = None, 
            end_date: str = None
    ):
        rows = self.invoices_database.filter_invoices(id, incoming, closed, start_date, end_date)
        logger.info(f"Getting invoices: id -> {id}, incoming -> {incoming}, closed-> {closed}, start_date = {start_date}, end_date= {end_date}")

        return [
            {
                "id": r[0], 
                "description": r[1], 
                "company": r[2], 
                "total_amount": r[3],
                "currency": r[4], 
                "emission_date": r[5], 
                "due_date": r[6], 
                "incoming": r[7], 
                "closed": r[8]
            }
            for r in rows
        ]
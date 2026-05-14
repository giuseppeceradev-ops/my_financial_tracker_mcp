import logging
from datetime import datetime
import json

from my_financial_tracker_mcp.database.receipts import ReceiptsDatabase
from my_financial_tracker_mcp.services.financial_events import FinancialEventsService
from my_financial_tracker_mcp.services.google_calendar import CalendarService
from my_financial_tracker_mcp.database.invoices import InvoicesDatabase

logger = logging.getLogger(__name__)

class Payments:
        def __init__(
                self,
                receipts_database: ReceiptsDatabase,
                invoices_database: InvoicesDatabase,
                financial_events_service: FinancialEventsService,
                calendar_service: CalendarService
        ):
                self.receipt_database = receipts_database
                self.invoices_database = invoices_database
                self.financial_events_service = financial_events_service
                self.calendar_service = calendar_service
                
        async def confirm_purchase_payment(
                self,
                id: str
                ):

                logger.info(f"Confirming purchase called with id: {id}")
                event = self.financial_events_service.remove_event(id)

                category_id = self.receipt_database.resolve_category_id(event.description)
                self.receipt_database.create_receipt(description = event.description, timestamp=datetime.now().isoformat(), amount =event.amount )
                id = self.receipt_database.add_receipt_item(event.amount, event.description, category_id, id)
                logger.info(f"Created receipt item {id}")
                
                self.calendar_service.remove_payment_event(event.id, event.google_id)

                return {"ok": True}

        async def confirm_customer_invoice_payment(
                self,
                id: str):
                logger.info(f"Confirming payment from customer with id: {id}")
                event = self.financial_events_service.remove_event(id)

                invoice_id = None

                if event.context:
                        invoice_id = json.loads(event.context)["invoice_id"]

                id = self.invoices_database.update_invoice(id=invoice_id, closed=True, amount=event.amount, incoming=True)
                logger.info(f"Created transaction {id}")

                self.calendar_service.remove_payment_event(event.id, event.google_id)

                return {"ok": True}

        async def confirm_supplier_invoice_payment(
                self,
                id: str):
                logger.info(f"Confirming payment for supplier with id: {id}")
                event = self.financial_events_service.remove_event(id)

                invoice_id = None

                if event.context:
                        invoice_id = json.loads(event.context)["invoice_id"]

                id = self.invoices_database.update_invoice(id=invoice_id, closed=True, amount=event.amount, incoming=False)
                logger.info(f"Closed invoice ({invoice_id})")

                self.calendar_service.remove_payment_event(event.id ,event.google_id)

                return {"ok": True}
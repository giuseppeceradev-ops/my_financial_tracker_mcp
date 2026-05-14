import os
import logging

from my_financial_tracker_mcp.database.financial_event import FinancialEventsDatabase
from my_financial_tracker_mcp.services.google_calendar import CalendarService
from my_financial_tracker_mcp.models.event import Event

logger = logging.getLogger(__name__)

CALENDAR_SCOPES  = ["https://www.googleapis.com/auth/calendar"]
GMAIL_CREDS = os.getenv("GOOGLE_CREDENTIALS_PATH")
BASE_URL = os.getenv("PUBLIC_BASE_URL")

class FinancialEventsService:

    def __init__(
        self, 
        calendar_service: CalendarService,
        database: FinancialEventsDatabase):
        self.database = database
        self.calendar_service = calendar_service

    async def add_event_to_calendar(
            self,
            id:int,
            due_date_str:str,
            title: str,
            amount: float,
            context: str,
            body: str,
        ):    
            event = self.calendar_service.create_payment_event(title, body, amount, due_date_str)
            self.database.update_event(id, title, amount, due_date_str, event["id"], context)

            logger.info(f"Added event {title} - €{amount} - in scadenza {due_date_str}")

            return {"title": title, "amount": amount, "due_date": due_date_str, "google_id": event["id"]} 
    
    async def add_supplier_invoice_to_calendar(
        self,
        amount: float,
        due_date: str,
        invoice_id: int
    ):
        id = self.database.add_event("Conferma pagamento effettuato", amount, due_date)

        payment_url = (
            f"http://{BASE_URL}/api/payments/confirm/supplier_invoice"
            f"?id={id}"
        )

        body = (f'Scadenza fattura fornitore: {invoice_id} di euro {amount}\n\n'
            f'Conferma pagamento effettuato:\n'
            f'{payment_url}')

        return await self.add_event_to_calendar(id, due_date, "Scadenza fattura fornitore", amount, '{"invoice_id":'+ str(invoice_id) + '}', body)


    async def add_customer_invoice_to_calendar(
        self,
        amount: float,
        due_date: str,
        invoice_id: int
    ):
        BASE_URL = os.getenv("PUBLIC_BASE_URL")

        id = self.database.add_event("Conferma pagamento ricevuto", amount, due_date)

        payment_url = (
            f"http://{BASE_URL}/api/payments/confirm/customer_invoice"
            f"?id={id}"
        )

        body = (f'Scadenza fattura cliente: {invoice_id} di euro {amount}\n\n'
            f'Conferma pagamento ricevuto:\n'
            f'{payment_url}')

        return await self.add_event_to_calendar(id, due_date, "Scadenza fattura cliente", amount, '{"invoice_id":'+ str(invoice_id) + '}', body)

    def remove_event(
        self,
        id: int
        )->Event:
        
        rec = self.database.get_event(id)
        event = Event(id=rec[0], description=rec[1], amount=rec[2], due_date=rec[3], google_id=rec[4], context=rec[5])
        logger.info(f"Event->{event}")
        self.database.remove_event(id)
        logger.info(f"Event {id} removed")
        return event
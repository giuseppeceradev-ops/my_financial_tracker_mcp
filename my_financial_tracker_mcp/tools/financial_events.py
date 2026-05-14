import datetime
import os
import logging

from  my_financial_tracker_mcp.services.financial_events import FinancialEventsService
from  my_financial_tracker_mcp.database.financial_event import FinancialEventsDatabase

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("PUBLIC_BASE_URL")

class FinancialEvents:
    def __init__(
        self, 
        financial_events: FinancialEventsService,
        database: FinancialEventsDatabase
        ):
        self.financial_events = financial_events
        self.database = database

    async def add_future_purchase_to_calendar(
        self,
        title: str,
        amount: float,
        due_date: datetime,
    ):
        BASE_URL = os.getenv("PUBLIC_BASE_URL")

        due_date_str = due_date.strftime("%Y-%m-%d")
        id = self.database.add_event(title, amount, due_date_str)

        payment_url = (
            f"http://{BASE_URL}/api/payments/confirm/purchase"
            f"?id={id}"
        )

        body = (f'Scadenza pagamento: {title} di euro {amount}\n\n'
            f'Conferma pagamento effettuato:\n'
            f'{payment_url}')
            
        return await self.financial_events.add_event_to_calendar(id, due_date_str, title, amount, "", body)

    async def get_events(
        self,
        id: str,
        start_date: str,
        end_date: datetime
    ):
        events = self.database.get_events(id, start_date, end_date)

        logger.info(f"Getting events, {start_date} - {end_date}")

        return [
        {
            "id": r[0],
            "description": r[1],
            "amount": r[2],
            "due_date": r[3],
        }
        for r in events
        ]
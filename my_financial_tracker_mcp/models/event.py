from datetime import datetime
from dataclasses import dataclass

@dataclass
class Event:
    id: int
    description: str
    amount: float
    due_date: datetime
    google_id: str
    context:str = ""
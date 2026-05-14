from dataclasses import dataclass

@dataclass
class Transaction:
    id: int
    amount: float
    currency: str
    description: str
    timestamp: str
    category: str
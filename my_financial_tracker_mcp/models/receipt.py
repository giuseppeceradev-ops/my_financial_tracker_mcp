from dataclasses import dataclass

@dataclass
class Item:
    id: int
    amount: float
    description: str
    category: int


@dataclass
class Receipt:
    id: int
    description: str
    company: str
    amount: float
    timestamp: str
    items: list[Item]



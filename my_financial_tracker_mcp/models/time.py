from pydantic import BaseModel, Field

class TimeResult(BaseModel):
    timezone: str
    datetime_iso: str = Field(description="ISO-8601 with timezone offset")
    unix_timestamp: float
    day_of_week: str
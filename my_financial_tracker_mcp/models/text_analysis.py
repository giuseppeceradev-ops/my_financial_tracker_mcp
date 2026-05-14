from pydantic import BaseModel, Field

class TextAnalysis(BaseModel):
    word_count: int
    char_count: int
    sentence_count: int
    avg_word_length: float
    language_hint: str = Field(description="'latin-script' or 'non-latin'")
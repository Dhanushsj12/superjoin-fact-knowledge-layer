from typing import Optional
from pydantic import BaseModel


class Fact(BaseModel):
    entity: Optional[str] = None
    metric: str
    value: Optional[float] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    scope: Optional[str] = None
    evidence: str
    page_number: int
    source_document: str
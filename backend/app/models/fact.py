from typing import Optional, Union

from pydantic import BaseModel


class Fact(BaseModel):
    entity: Optional[str] = None
    metric: str
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    scope: Optional[str] = None

    evidence: str
    page_number: int
    source_document: str
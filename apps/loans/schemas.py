from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LoanApplyIn(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"), le=Decimal("50000000"), decimal_places=2)
    term_months: int = Field(ge=1, le=360)
    purpose: str = Field(min_length=5, max_length=500)

    @field_validator("purpose")
    @classmethod
    def purpose_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("Invalid characters in purpose")
        return v.strip()


class DecisionIn(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED)$")
    comment: str = Field(default="", max_length=1000)

    @field_validator("comment")
    @classmethod
    def comment_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("Invalid characters in comment")
        return v.strip()


class LoanOut(BaseModel):
    id: int
    amount: Decimal
    term_months: int
    purpose: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

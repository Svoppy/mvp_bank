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

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "amount": "350000.00",
                    "term_months": 24,
                    "purpose": "Home renovation",
                }
            ]
        }


class DecisionIn(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED)$")
    comment: str = Field(default="", max_length=1000)

    @field_validator("comment")
    @classmethod
    def comment_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("Invalid characters in comment")
        return v.strip()

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "APPROVED",
                    "comment": "Stable income and positive credit history.",
                }
            ]
        }


class LoanOut(BaseModel):
    id: int
    amount: Decimal
    term_months: int
    purpose: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "amount": "350000.00",
                "term_months": 24,
                "purpose": "Home renovation",
                "status": "PENDING",
                "created_at": "2026-04-11T10:00:00Z",
                "updated_at": "2026-04-11T10:00:00Z",
            }
        }
        from_attributes = True


class LoanDocumentOut(BaseModel):
    id: int
    loan_id: int
    original_name: str
    content_type: str
    size_bytes: int
    sha256: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "loan_id": 10,
                "original_name": "income.pdf",
                "content_type": "application/pdf",
                "size_bytes": 128000,
                "sha256": "a" * 64,
                "created_at": "2026-04-20T10:00:00Z",
            }
        }
        from_attributes = True

from pydantic import BaseModel


class ErrorOut(BaseModel):
    detail: str

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Forbidden: insufficient permissions",
            }
        }

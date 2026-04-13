from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    ip_address: Optional[str]
    timestamp: datetime
    details: Any

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12,
                "user_id": 3,
                "action": "LOAN_APPROVED",
                "entity_type": "CreditApplication",
                "entity_id": 8,
                "ip_address": "127.0.0.1",
                "timestamp": "2026-04-11T10:15:00Z",
                "details": {
                    "new_status": "APPROVED",
                    "client_id": 5,
                },
            }
        }
        from_attributes = True

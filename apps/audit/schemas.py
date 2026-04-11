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
        from_attributes = True

"""
Audit Log Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import uuid4


class AuditAction(str, Enum):
    SUBMIT_CASE = "submit_case"
    UPLOAD_FILE = "upload_file"
    VIEW_RESULT = "view_result"
    SELECT_CODE = "select_code"
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"


class AuditLogEntry(BaseModel):
    """Individual audit log entry"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: AuditAction
    clinical_text_hash: Optional[str] = None  # SHA-256 hash, not actual text
    clinical_text_length: Optional[int] = None
    filename: Optional[str] = None
    suggested_code: Optional[str] = None
    suggested_descriptor: Optional[str] = None
    complexity: Optional[int] = None
    accepted_code: Optional[str] = None  # If user selected different code
    candidate_count: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Response for audit log queries"""
    total: int
    page: int
    page_size: int
    entries: List[AuditLogEntry]

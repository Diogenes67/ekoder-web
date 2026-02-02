"""
Audit Log Routes
View and export audit logs (admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from datetime import datetime
from typing import Optional
import logging

from app.audit.models import AuditLogResponse, AuditAction
from app.audit.logger import get_logs, get_user_stats, export_logs_csv
from app.auth.utils import get_current_user
from app.auth.models import UserRole

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])
logger = logging.getLogger(__name__)


def require_admin(current_user = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    user_id: Optional[str] = None,
    action: Optional[AuditAction] = None,
    current_user = Depends(require_admin)
) -> AuditLogResponse:
    """
    Get audit logs (admin only)
    """
    entries, total = get_logs(
        page=page,
        page_size=min(page_size, 100),  # Max 100 per page
        user_id=user_id,
        action=action
    )

    return AuditLogResponse(
        total=total,
        page=page,
        page_size=page_size,
        entries=entries
    )


@router.get("/stats/{user_id}")
async def get_user_audit_stats(
    user_id: str,
    current_user = Depends(require_admin)
) -> dict:
    """
    Get coding statistics for a specific user (admin only)
    """
    return get_user_stats(user_id)


@router.get("/export", response_class=PlainTextResponse)
async def export_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(require_admin)
):
    """
    Export audit logs as CSV (admin only)
    """
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    csv_content = export_logs_csv(start_date=start, end_date=end)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ekoder_audit_log.csv"}
    )


@router.get("/my-stats")
async def get_my_stats(current_user = Depends(get_current_user)) -> dict:
    """
    Get your own coding statistics
    """
    return get_user_stats(current_user.id)

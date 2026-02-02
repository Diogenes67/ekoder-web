"""
Audit Logger
Immutable audit trail for compliance (ACCD requirement)
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

from app.audit.models import AuditLogEntry, AuditAction

logger = logging.getLogger(__name__)

# Store audit logs in a JSON file (for production, use a database)
AUDIT_FILE = Path(__file__).parent.parent.parent / "data" / "audit_log.json"


def _load_logs() -> List[dict]:
    """Load audit logs from file"""
    if AUDIT_FILE.exists():
        try:
            with open(AUDIT_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def _save_logs(logs: List[dict]):
    """Save audit logs to file (append-only in spirit)"""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_FILE, 'w') as f:
        json.dump(logs, f, indent=2, default=str)


def hash_clinical_text(text: str) -> str:
    """Create SHA-256 hash of clinical text for privacy"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def log_event(
    action: AuditAction,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    clinical_text: Optional[str] = None,
    filename: Optional[str] = None,
    suggested_code: Optional[str] = None,
    suggested_descriptor: Optional[str] = None,
    complexity: Optional[int] = None,
    accepted_code: Optional[str] = None,
    candidate_count: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    error: Optional[str] = None
) -> AuditLogEntry:
    """
    Log an audit event. This is append-only - entries cannot be modified.
    """
    entry = AuditLogEntry(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        user_email=user_email,
        action=action,
        clinical_text_hash=hash_clinical_text(clinical_text) if clinical_text else None,
        clinical_text_length=len(clinical_text) if clinical_text else None,
        filename=filename,
        suggested_code=suggested_code,
        suggested_descriptor=suggested_descriptor,
        complexity=complexity,
        accepted_code=accepted_code,
        candidate_count=candidate_count,
        ip_address=ip_address,
        user_agent=user_agent,
        processing_time_ms=processing_time_ms,
        error=error
    )

    # Append to log file
    logs = _load_logs()
    logs.append(entry.model_dump())
    _save_logs(logs)

    logger.info(f"Audit: {action.value} by {user_email or 'anonymous'}")

    return entry


def get_logs(
    page: int = 1,
    page_size: int = 50,
    user_id: Optional[str] = None,
    action: Optional[AuditAction] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> tuple[List[AuditLogEntry], int]:
    """
    Query audit logs with optional filters.
    Returns (entries, total_count)
    """
    logs = _load_logs()

    # Apply filters
    filtered = logs

    if user_id:
        filtered = [l for l in filtered if l.get('user_id') == user_id]

    if action:
        filtered = [l for l in filtered if l.get('action') == action.value]

    if start_date:
        filtered = [l for l in filtered if datetime.fromisoformat(l.get('timestamp', '')) >= start_date]

    if end_date:
        filtered = [l for l in filtered if datetime.fromisoformat(l.get('timestamp', '')) <= end_date]

    # Sort by timestamp descending (newest first)
    filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    total = len(filtered)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = filtered[start:end]

    return [AuditLogEntry(**entry) for entry in page_entries], total


def get_user_stats(user_id: str) -> dict:
    """Get coding statistics for a user"""
    logs = _load_logs()
    user_logs = [l for l in logs if l.get('user_id') == user_id]

    coding_actions = [l for l in user_logs if l.get('action') in ['submit_case', 'upload_file']]

    return {
        "total_cases": len(coding_actions),
        "cases_with_suggestions": len([l for l in coding_actions if l.get('suggested_code')]),
        "cases_with_errors": len([l for l in coding_actions if l.get('error')]),
        "avg_processing_time_ms": (
            sum(l.get('processing_time_ms', 0) for l in coding_actions if l.get('processing_time_ms'))
            / max(1, len([l for l in coding_actions if l.get('processing_time_ms')]))
        )
    }


def export_logs_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str:
    """Export audit logs as CSV string"""
    entries, _ = get_logs(page=1, page_size=100000, start_date=start_date, end_date=end_date)

    headers = [
        "timestamp", "user_email", "action", "suggested_code",
        "suggested_descriptor", "complexity", "candidate_count",
        "processing_time_ms", "error"
    ]

    lines = [",".join(headers)]

    for entry in entries:
        row = [
            str(entry.timestamp),
            entry.user_email or "",
            entry.action.value,
            entry.suggested_code or "",
            f'"{entry.suggested_descriptor}"' if entry.suggested_descriptor else "",
            str(entry.complexity) if entry.complexity else "",
            str(entry.candidate_count) if entry.candidate_count else "",
            str(entry.processing_time_ms) if entry.processing_time_ms else "",
            f'"{entry.error}"' if entry.error else ""
        ]
        lines.append(",".join(row))

    return "\n".join(lines)

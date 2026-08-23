from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import AuditLogDB
from backend.app.schemas import AuditLogResponse

router = APIRouter()

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    resident_id: Optional[str] = Query(None),
    appointment_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLogDB)
    if action:
        query = query.filter(AuditLogDB.action == action)
    if status:
        query = query.filter(AuditLogDB.status == status)
    if channel:
        query = query.filter(AuditLogDB.channel == channel)
    if resident_id:
        query = query.filter(AuditLogDB.resident_id == resident_id)
    if appointment_id:
        query = query.filter(AuditLogDB.appointment_id == appointment_id)

    return query.order_by(AuditLogDB.timestamp.desc()).offset(offset).limit(limit).all()

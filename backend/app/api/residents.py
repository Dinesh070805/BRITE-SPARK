from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import ResidentDB
from backend.app.schemas import ResidentResponse

router = APIRouter()

@router.get("/residents", response_model=List[ResidentResponse])
def get_residents(
    language: Optional[str] = Query(None),
    sms_optout: Optional[bool] = Query(None),
    voice_optout: Optional[bool] = Query(None),
    email_optout: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(ResidentDB)
    if language:
        query = query.filter(ResidentDB.language == language)
    if sms_optout is not None:
        query = query.filter(ResidentDB.sms_optout == sms_optout)
    if voice_optout is not None:
        query = query.filter(ResidentDB.voice_optout == voice_optout)
    if email_optout is not None:
        query = query.filter(ResidentDB.email_optout == email_optout)

    return query.offset(offset).limit(limit).all()

@router.get("/residents/{resident_id}", response_model=ResidentResponse)
def get_resident_by_id(resident_id: str, db: Session = Depends(get_db)):
    resident = db.query(ResidentDB).filter(ResidentDB.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail=f"Resident {resident_id} not found")
    return resident

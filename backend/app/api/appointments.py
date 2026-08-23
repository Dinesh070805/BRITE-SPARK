from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import AppointmentDB
from backend.app.schemas import AppointmentResponse

router = APIRouter()

@router.get("/appointments", response_model=List[AppointmentResponse])
def get_appointments(
    status: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AppointmentDB)
    if status:
        query = query.filter(AppointmentDB.status == status)
    if location:
        query = query.filter(AppointmentDB.location == location)
    if service_type:
        query = query.filter(AppointmentDB.service_type == service_type)
        
    return query.offset(offset).limit(limit).all()

@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_by_id(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(AppointmentDB).filter(AppointmentDB.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return appointment

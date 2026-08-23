from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import ReminderDB, AppointmentDB, ResidentDB
from backend.app.schemas import ReminderResponse
from backend.app.services.reminder_engine import ReminderEngineService

router = APIRouter()

@router.get("/reminders", response_model=List[ReminderResponse])
def get_reminders(
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    reached: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(ReminderDB)
    if status:
        query = query.filter(ReminderDB.status == status)
    if channel:
        query = query.filter(ReminderDB.channel == channel)
    if reached is not None:
        query = query.filter(ReminderDB.reached == reached)

    return query.offset(offset).limit(limit).all()

@router.get("/reminders/{reminder_id}", response_model=ReminderResponse)
def get_reminder_by_id(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(ReminderDB).filter(ReminderDB.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail=f"Reminder {reminder_id} not found")
    return reminder

@router.post("/reminders/run")
def run_reminder_engine(db: Session = Depends(get_db)):
    engine = ReminderEngineService(db)
    summary = engine.run_engine_for_all()
    return {"message": "Reminder engine run completed successfully", "summary": summary}

@router.post("/reminders/{reminder_id}/retry")
def retry_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(ReminderDB).filter(ReminderDB.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail=f"Reminder {reminder_id} not found")
    
    appointment = db.query(AppointmentDB).filter(AppointmentDB.id == reminder.appointment_id).first()
    resident = db.query(ResidentDB).filter(ResidentDB.id == reminder.resident_id).first()
    
    if not appointment or not resident:
        raise HTTPException(status_code=400, detail="Missing appointment or resident data")

    engine = ReminderEngineService(db)
    from datetime import datetime
    result = engine.process_appointment(appointment, resident, force_now=datetime.utcnow())
    return {"message": f"Reminder {reminder_id} retried successfully", "result": result}

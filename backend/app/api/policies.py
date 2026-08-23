from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import PolicyDB
from backend.app.schemas import PolicyResponse, PolicyUpdate

router = APIRouter()

@router.get("/policies", response_model=PolicyResponse)
def get_policy(db: Session = Depends(get_db)):
    policy = db.query(PolicyDB).filter(PolicyDB.id == 1).first()
    if not policy:
        policy = PolicyDB(id=1, quiet_hours_start=20, quiet_hours_end=8, max_attempts=3, channel_priority="SMS,Voice,Email")
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy

@router.put("/policies", response_model=PolicyResponse)
def update_policy(policy_data: PolicyUpdate, db: Session = Depends(get_db)):
    policy = db.query(PolicyDB).filter(PolicyDB.id == 1).first()
    if not policy:
        policy = PolicyDB(id=1)
        db.add(policy)

    policy.quiet_hours_start = policy_data.quiet_hours_start
    policy.quiet_hours_end = policy_data.quiet_hours_end
    policy.max_attempts = policy_data.max_attempts
    policy.channel_priority = policy_data.channel_priority

    db.commit()
    db.refresh(policy)
    return policy

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/metrics")
def get_operational_metrics(db: Session = Depends(get_db)):
    service = MetricsService(db)
    return service.get_dashboard_metrics()

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    metrics_service = MetricsService(db)
    return metrics_service.get_dashboard_metrics()

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Reminder That Reaches API", "version": "1.0.0"}

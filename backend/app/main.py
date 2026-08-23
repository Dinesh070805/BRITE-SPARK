from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database import engine, Base
from backend.app.api import (
    health, dashboard, appointments, residents, reminders, metrics, audit, policies
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Reminder That Reaches API",
    description="Policy-Driven Appointment Reminder System Backend API",
    version="1.0.0"
)

# Enable CORS for local React frontend (http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(appointments.router, prefix="/api", tags=["Appointments"])
app.include_router(residents.router, prefix="/api", tags=["Residents"])
app.include_router(reminders.router, prefix="/api", tags=["Reminders"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(audit.router, prefix="/api", tags=["Audit Logs"])
app.include_router(policies.router, prefix="/api", tags=["Policies"])

@app.get("/")
def root():
    return {"message": "Reminder That Reaches API is running", "docs_url": "/docs"}

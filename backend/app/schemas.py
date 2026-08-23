from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

# Resident Schemas
class ResidentBase(BaseModel):
    id: str
    name: str
    mobile: Optional[str] = ""
    landline: Optional[str] = ""
    email: Optional[str] = ""
    language: Optional[str] = "en"
    sms_optout: bool = False
    voice_optout: bool = False
    email_optout: bool = False
    number_last_verified: Optional[datetime] = None

class ResidentResponse(ResidentBase):
    class Config:
        from_attributes = True

# Appointment Schemas
class AppointmentBase(BaseModel):
    id: str
    resident_id: str
    scheduled_at: datetime
    location: str
    service_type: str
    status: str = "Booked"

class AppointmentResponse(AppointmentBase):
    resident: Optional[ResidentResponse] = None
    class Config:
        from_attributes = True

# Reminder Attempt Schemas
class ReminderAttemptResponse(BaseModel):
    id: int
    reminder_id: int
    channel: str
    contact: str
    attempt_number: int
    timestamp: datetime
    status: str
    provider_detail: str
    reached: bool
    failure_reason: str

    class Config:
        from_attributes = True

# Reminder Schemas
class ReminderResponse(BaseModel):
    id: int
    appointment_id: str
    resident_id: str
    scheduled_at: datetime
    status: str
    language: str
    channel: str
    reached: bool
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    resident: Optional[ResidentResponse] = None
    appointment: Optional[AppointmentResponse] = None
    attempts: List[ReminderAttemptResponse] = []

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    resident_id: Optional[str] = None
    appointment_id: Optional[str] = None
    action: str
    channel: str
    status: str
    reason: str
    details: str

    class Config:
        from_attributes = True

# Policy Schemas
class PolicyUpdate(BaseModel):
    quiet_hours_start: int = Field(ge=0, le=23)
    quiet_hours_end: int = Field(ge=0, le=23)
    max_attempts: int = Field(ge=1, le=10)
    channel_priority: str = "SMS,Voice,Email"

class PolicyResponse(PolicyUpdate):
    id: int = 1
    class Config:
        from_attributes = True

# Metrics & Dashboard Schemas
class MetricsSummaryResponse(BaseModel):
    appointments: int
    reminders_attempted: int
    residents_reached: int
    reach_rate: float
    delivery_rate: float
    failed: int
    deferred: int
    blocked: int
    duplicates_prevented: int
    channel_stats: Dict[str, Any]
    language_stats: Dict[str, Any]

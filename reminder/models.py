from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class ChannelType(str, Enum):
    SMS = "sms"
    VOICE = "voice"
    EMAIL = "email"

class CommunicationStatus(str, Enum):
    ATTEMPTED = "attempted"
    DELIVERED = "delivered"
    REACHED = "reached"
    FAILED = "failed"
    DEFERRED = "deferred"
    BLOCKED = "blocked"
    STOPPED = "stopped"

@dataclass
class Resident:
    resident_id: str
    name: str
    mobile: str
    landline: str
    email: str
    language: str
    sms_optout: bool
    voice_optout: bool
    email_optout: bool
    number_last_verified: Optional[datetime] = None

    def get_clean_mobile(self) -> str:
        return self.mobile.strip()

    def get_clean_landline(self) -> str:
        return self.landline.strip()

    def get_clean_email(self) -> str:
        return self.email.strip().lower()

@dataclass
class Appointment:
    appointment_id: str
    resident_id: str
    scheduled_at: datetime
    location: str
    service_type: str
    status: str

@dataclass
class ReminderAttempt:
    appointment_id: str
    resident_id: str
    channel: ChannelType
    to_contact: str
    language: str
    timestamp: datetime
    attempt_number: int
    status: CommunicationStatus
    detail: str
    reached: bool = False
    deferred: bool = False
    reason: str = ""
    fallback_used: bool = False

@dataclass
class AuditRecord:
    appointment_id: str
    resident_id: str
    channel: str
    contact: str
    language: str
    timestamp: str
    status: str
    outcome: str
    reason: str
    attempt_number: int
    fallback_used: bool
    reached: bool
    deferred: bool
    duplicate_prevented: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "appointment_id": self.appointment_id,
            "resident_id": self.resident_id,
            "channel": self.channel,
            "contact": self.contact,
            "language": self.language,
            "timestamp": self.timestamp,
            "status": self.status,
            "outcome": self.outcome,
            "reason": self.reason,
            "attempt_number": self.attempt_number,
            "fallback_used": self.fallback_used,
            "reached": self.reached,
            "deferred": self.deferred,
            "duplicate_prevented": self.duplicate_prevented,
        }

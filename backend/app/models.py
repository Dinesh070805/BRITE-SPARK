from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class ResidentDB(Base):
    __tablename__ = "residents"

    id = Column(String, primary_key=True, index=True) # e.g. RS-4000
    name = Column(String, nullable=False)
    mobile = Column(String, default="")
    landline = Column(String, default="")
    email = Column(String, default="")
    language = Column(String, default="en")
    sms_optout = Column(Boolean, default=False)
    voice_optout = Column(Boolean, default=False)
    email_optout = Column(Boolean, default=False)
    number_last_verified = Column(DateTime, nullable=True)

    appointments = relationship("AppointmentDB", back_populates="resident")
    reminders = relationship("ReminderDB", back_populates="resident")

class AppointmentDB(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, index=True) # e.g. AP-70238
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    service_type = Column(String, nullable=False)
    status = Column(String, default="Booked")

    resident = relationship("ResidentDB", back_populates="appointments")
    reminders = relationship("ReminderDB", back_populates="appointment")

class ReminderDB(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(String, ForeignKey("appointments.id"), nullable=False)
    resident_id = Column(String, ForeignKey("residents.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String, default="Pending") # Pending, Delivered, Reached, Failed, Deferred, Blocked
    language = Column(String, default="en")
    channel = Column(String, default="none")
    reached = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resident = relationship("ResidentDB", back_populates="reminders")
    appointment = relationship("AppointmentDB", back_populates="reminders")
    attempts = relationship("ReminderAttemptDB", back_populates="reminder")

class ReminderAttemptDB(Base):
    __tablename__ = "reminder_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    channel = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    attempt_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)
    provider_detail = Column(String, default="")
    reached = Column(Boolean, default=False)
    failure_reason = Column(String, default="")

    reminder = relationship("ReminderDB", back_populates="attempts")

class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resident_id = Column(String, nullable=True)
    appointment_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    channel = Column(String, default="")
    status = Column(String, nullable=False)
    reason = Column(String, default="")
    details = Column(Text, default="")

class PolicyDB(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, default=1)
    quiet_hours_start = Column(Integer, default=20)
    quiet_hours_end = Column(Integer, default=8)
    max_attempts = Column(Integer, default=3)
    channel_priority = Column(String, default="SMS,Voice,Email") # Comma separated

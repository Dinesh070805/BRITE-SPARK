"""
Core Reminder Decision Engine (Part 2 + Direction CR-2026/11 Compliance)
Implements appointment reminder dispatch, contact policy evaluation, localization,
deduplication, multi-channel fallback (SMS -> Voice -> Email), outcome interpretation,
regulatory 7-day contact limit enforcement, and audit log recording.
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models import (
    ResidentDB, AppointmentDB, ReminderDB, ReminderAttemptDB, AuditLogDB, PolicyDB
)
from backend.app.services.contact_policy import ContactPolicyService
from backend.app.services.language_service import LanguageService
from backend.app.services.deduplication import DeduplicationService
from backend.app.services.dispatcher import ChannelDispatcher
from backend.app.services.outcome_interpreter import OutcomeInterpreter

class ReminderEngineService:
    def __init__(self, db: Session):
        self.db = db
        policy_config = db.query(PolicyDB).filter(PolicyDB.id == 1).first()
        if not policy_config:
            policy_config = PolicyDB(id=1, quiet_hours_start=20, quiet_hours_end=8, max_attempts=3, channel_priority="SMS,Voice,Email")
            db.add(policy_config)
            db.commit()
            db.refresh(policy_config)

        self.policy_config = policy_config
        self.policy_service = ContactPolicyService(policy_config)
        self.language_service = LanguageService()
        self.dedup_service = DeduplicationService()
        self.dispatcher = ChannelDispatcher()

    def run_engine_for_all(self) -> Dict[str, Any]:
        appointments = self.db.query(AppointmentDB).all()
        processed_count = 0
        reached_count = 0
        deferred_count = 0
        blocked_count = 0
        duplicates_prevented = 0

        for app in appointments:
            resident = self.db.query(ResidentDB).filter(ResidentDB.id == app.resident_id).first()
            if not resident:
                continue

            result = self.process_appointment(app, resident)
            processed_count += 1
            if result.get("reached"):
                reached_count += 1
            if result.get("status") == "Deferred":
                deferred_count += 1
            if result.get("status") == "Blocked":
                blocked_count += 1
            duplicates_prevented += result.get("duplicates_prevented", 0)

        return {
            "appointments_processed": processed_count,
            "residents_reached": reached_count,
            "deferred": deferred_count,
            "blocked": blocked_count,
            "duplicates_prevented": duplicates_prevented + self.dedup_service.duplicate_prevented_count
        }

    def process_appointment(self, appointment: AppointmentDB, resident: ResidentDB, force_now: Optional[datetime] = None) -> Dict[str, Any]:
        dispatch_time = force_now or (appointment.scheduled_at - timedelta(hours=24))

        # Check existing reminder record
        reminder = self.db.query(ReminderDB).filter(ReminderDB.appointment_id == appointment.id).first()
        if not reminder:
            reminder = ReminderDB(
                appointment_id=appointment.id,
                resident_id=resident.id,
                scheduled_at=dispatch_time,
                status="Pending",
                language=resident.language or "en",
                channel="none",
                reached=False,
                attempt_count=0
            )
            self.db.add(reminder)
            self.db.commit()
            self.db.refresh(reminder)

        # 1. Missing contact details check
        if not (resident.mobile or "").strip() and not (resident.landline or "").strip() and not (resident.email or "").strip():
            reminder.status = "Blocked"
            self.log_audit(resident.id, appointment.id, "BLOCKED", "none", "Blocked", "No phone or email contact details", "Missing contact details")
            self.db.commit()
            return {"status": "Blocked", "reached": False, "duplicates_prevented": 0}

        # 2. Opt-out check
        if resident.sms_optout and resident.voice_optout and resident.email_optout:
            reminder.status = "Blocked"
            self.log_audit(resident.id, appointment.id, "BLOCKED", "all", "Blocked", "All channels opted out", "Resident opted out of SMS, Voice, and Email")
            self.db.commit()
            return {"status": "Blocked", "reached": False, "duplicates_prevented": 0}

        # 3. Direction CR-2026/11 Regulatory 7-Day Contact Limit Pre-Check
        regulatory_eval = ContactPolicyService.evaluate_regulatory_limit(self.db, resident.id, dispatch_time, appointment.id)
        if not regulatory_eval["permitted"]:
            reminder.status = "Blocked"
            self.log_audit(
                resident.id,
                appointment.id,
                "REGULATORY_BLOCK",
                "all",
                "Blocked",
                regulatory_eval["reason"],
                json.dumps(regulatory_eval)
            )
            self.db.commit()
            return {"status": "Blocked", "reached": False, "duplicates_prevented": 0}

        # 4. Too close to appointment check
        if self.policy_service.is_too_close_to_appointment(dispatch_time, appointment.scheduled_at):
            reminder.status = "Stopped"
            self.log_audit(resident.id, appointment.id, "STOPPED", "none", "Stopped", "Too close to appointment", "Lead time less than safety threshold")
            self.db.commit()
            return {"status": "Stopped", "reached": False, "duplicates_prevented": 0}

        # 5. Eligible channels
        eligible = self.policy_service.get_eligible_channels(resident, dispatch_time)
        if not eligible:
            reminder.status = "Blocked"
            self.log_audit(resident.id, appointment.id, "BLOCKED", "none", "Blocked", "No eligible channels", "Failed policy eligibility")
            self.db.commit()
            return {"status": "Blocked", "reached": False, "duplicates_prevented": 0}

        body, used_lang, is_fallback = self.language_service.render_reminder(resident, appointment)
        reminder.language = used_lang

        attempt_count = reminder.attempt_count
        reached = False
        duplicates_count = 0

        for ch, contact_val, deferred_time, reason in eligible:
            if reached or attempt_count >= self.policy_config.max_attempts:
                break

            # Handle Quiet Hours deferral
            if deferred_time is not None:
                reminder.status = "Deferred"
                self.log_audit(
                    resident.id, appointment.id, "DEFERRED", ch, "Deferred",
                    "Quiet hours active", f"Scheduled during quiet hours. Deferred to {deferred_time.isoformat()}"
                )
                self.db.commit()
                return {"status": "Deferred", "reached": False, "duplicates_prevented": 0}

            # Handle Deduplication
            if self.dedup_service.is_duplicate(contact_val, ch, appointment.id):
                duplicates_count += 1
                self.dedup_service.duplicate_prevented_count += 1
                self.log_audit(
                    resident.id, appointment.id, "DUPLICATE_PREVENTED", ch, "Blocked",
                    "Duplicate prevented", f"Duplicate dispatch prevented for {contact_val}"
                )
                continue

            # Execute channel dispatch
            attempt_count += 1
            result = self.dispatcher.dispatch(ch, contact_val, body, dispatch_time, attempt=attempt_count)
            self.dedup_service.record_dispatch(contact_val, ch, appointment.id)

            status_str = result.get("status", "failed")
            detail_str = result.get("detail", "")
            is_landline = self.policy_service.is_landline_number(contact_val)

            comm_status, is_reached, failure_reason = OutcomeInterpreter.interpret(ch, contact_val, status_str, detail_str, is_landline)

            # Record Attempt DB
            attempt_db = ReminderAttemptDB(
                reminder_id=reminder.id,
                channel=ch,
                contact=contact_val,
                attempt_number=attempt_count,
                timestamp=dispatch_time,
                status=comm_status,
                provider_detail=detail_str,
                reached=is_reached,
                failure_reason=failure_reason
            )
            self.db.add(attempt_db)

            reminder.channel = ch
            reminder.attempt_count = attempt_count

            if is_reached:
                reached = True
                reminder.reached = True
                reminder.status = "Reached"
                self.log_audit(resident.id, appointment.id, "REACHED", ch, "Reached", "Confirmed Human Reach", f"Voice call answered by human ({contact_val})")
                break
            else:
                reminder.status = comm_status.capitalize() if comm_status != "failed" else "Failed"
                self.log_audit(resident.id, appointment.id, "ATTEMPTED", ch, comm_status, failure_reason or detail_str or status_str, f"Attempt {attempt_count} on {ch}")

        self.db.commit()
        return {"status": reminder.status, "reached": reached, "duplicates_prevented": duplicates_count}

    def log_audit(self, resident_id: str, appointment_id: str, action: str, channel: str, status: str, reason: str, details: str):
        audit = AuditLogDB(
            timestamp=datetime.utcnow(),
            resident_id=resident_id,
            appointment_id=appointment_id,
            action=action,
            channel=channel,
            status=status,
            reason=reason,
            details=details
        )
        self.db.add(audit)

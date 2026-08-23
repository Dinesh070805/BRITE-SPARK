from datetime import datetime, timedelta
from typing import Tuple, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import ResidentDB, PolicyDB, ReminderAttemptDB, AuditLogDB, ReminderDB

class ContactPolicyService:
    REGULATORY_MAX_CONTACTS = 2
    REGULATORY_WINDOW_DAYS = 7

    def __init__(self, policy_config: Optional[PolicyDB] = None):
        if policy_config:
            self.quiet_start = policy_config.quiet_hours_start
            self.quiet_end = policy_config.quiet_hours_end
            self.max_attempts = policy_config.max_attempts
            self.channel_priority = [c.strip().lower() for c in policy_config.channel_priority.split(",") if c.strip()]
        else:
            self.quiet_start = 20
            self.quiet_end = 8
            self.max_attempts = 3
            self.channel_priority = ["sms", "voice", "email"]

    @staticmethod
    def is_landline_number(number: str) -> bool:
        if not number:
            return False
        parts = number.strip().split('-')
        if len(parts) >= 2:
            try:
                middle = int(parts[1])
                return 200 <= middle <= 249
            except ValueError:
                pass
        return False

    def is_quiet_hour(self, at_time: datetime) -> bool:
        hour = at_time.hour
        if self.quiet_start > self.quiet_end:
            return hour >= self.quiet_start or hour < self.quiet_end
        else:
            return self.quiet_start <= hour < self.quiet_end

    def get_next_allowed_time(self, at_time: datetime) -> datetime:
        if not self.is_quiet_hour(at_time):
            return at_time
        
        if at_time.hour >= self.quiet_start:
            next_day = at_time.date() + timedelta(days=1)
            return datetime(next_day.year, next_day.month, next_day.day, self.quiet_end, 0)
        else:
            return datetime(at_time.year, at_time.month, at_time.day, self.quiet_end, 0)

    def is_too_close_to_appointment(self, current_time: datetime, scheduled_at: datetime, min_lead_minutes: int = 30) -> bool:
        lead_time = scheduled_at - current_time
        return lead_time < timedelta(minutes=min_lead_minutes)

    def evaluate_channel(
        self,
        resident: ResidentDB,
        channel: str,
        at_time: datetime
    ) -> Tuple[bool, str, Optional[str], Optional[datetime]]:
        ch = channel.lower()
        deferred_time = self.get_next_allowed_time(at_time) if self.is_quiet_hour(at_time) else None

        if ch == "sms":
            if resident.sms_optout:
                return False, "SMS opt-out enforced", None, None
            mobile = (resident.mobile or "").strip()
            if not mobile:
                return False, "No mobile number provided", None, None
            if self.is_landline_number(mobile):
                return False, "Mobile field contains landline number (SMS unroutable)", None, None
            return True, "Eligible", mobile, deferred_time

        elif ch == "voice":
            if resident.voice_optout:
                return False, "Voice opt-out enforced", None, None
            mobile = (resident.mobile or "").strip()
            landline = (resident.landline or "").strip()
            phone = mobile if mobile else landline
            if not phone:
                return False, "No phone number available for voice call", None, None
            return True, "Eligible", phone, deferred_time

        elif ch == "email":
            if resident.email_optout:
                return False, "Email opt-out enforced", None, None
            email = (resident.email or "").strip().lower()
            if not email:
                return False, "No email address provided", None, None
            return True, "Eligible", email, deferred_time

        return False, f"Unknown channel {channel}", None, None

    def get_eligible_channels(
        self,
        resident: ResidentDB,
        at_time: datetime
    ) -> List[Tuple[str, str, Optional[datetime], str]]:
        eligible = []
        for ch in self.channel_priority:
            is_eligible, reason, contact_val, deferred_time = self.evaluate_channel(resident, ch, at_time)
            if is_eligible:
                eligible.append((ch, contact_val, deferred_time, reason))
        return eligible

    # =========================================================================
    # DIRECTION CR-2026/11 REGULATORY COMPLIANCE METHODS
    # =========================================================================

    @classmethod
    def count_regulatory_contacts(
        cls,
        db: Session,
        resident_id: str,
        at_time: datetime,
        rolling_days: int = REGULATORY_WINDOW_DAYS
    ) -> int:
        """
        Calculates the number of regulatory contacts (outbound attempts across ALL channels)
        made to a specific resident within the rolling N-day period ending at at_time.
        Per Direction CR-2026/11: EVERY outbound attempt counts, regardless of channel,
        delivery outcome, or reach outcome.
        """
        window_start = at_time - timedelta(days=rolling_days)
        
        # Query attempts linked to reminders for this resident within the rolling window
        count = (
            db.query(ReminderAttemptDB)
            .join(ReminderDB, ReminderAttemptDB.reminder_id == ReminderDB.id)
            .filter(
                ReminderDB.resident_id == resident_id,
                ReminderAttemptDB.timestamp >= window_start,
                ReminderAttemptDB.timestamp <= at_time
            )
            .count()
        )
        return count

    @classmethod
    def evaluate_regulatory_limit(
        cls,
        db: Session,
        resident_id: str,
        at_time: datetime,
        appointment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a new outbound contact is permitted for resident_id at at_time under
        Direction CR-2026/11 (max 2 contacts per rolling 7 days).
        Returns detailed evaluation audit evidence.
        """
        prior_contacts_count = cls.count_regulatory_contacts(db, resident_id, at_time)
        max_allowed = cls.REGULATORY_MAX_CONTACTS
        window_start = at_time - timedelta(days=cls.REGULATORY_WINDOW_DAYS)

        permitted = prior_contacts_count < max_allowed
        withheld = not permitted

        if permitted:
            reason = f"PERMITTED: Prior contact count ({prior_contacts_count}) is below rolling 7-day limit ({max_allowed})."
        else:
            reason = f"WITHHELD: Prior contact count ({prior_contacts_count}) meets or exceeds rolling 7-day limit ({max_allowed})."

        evidence = {
            "resident_id": resident_id,
            "appointment_id": appointment_id,
            "evaluation_timestamp": at_time.isoformat(),
            "rolling_window_start": window_start.isoformat(),
            "rolling_window_end": at_time.isoformat(),
            "prior_contacts_count": prior_contacts_count,
            "max_allowed_contacts": max_allowed,
            "permitted": permitted,
            "withheld": withheld,
            "reason": reason,
            "prioritisation_basis": "First-come first-served by scheduled_at timestamp; strictly non-discriminatory and independent of protected characteristics."
        }

        return evidence

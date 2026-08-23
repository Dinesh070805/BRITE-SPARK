from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from reminder.models import Resident, ChannelType

class ContactPolicy:
    def __init__(
        self,
        quiet_start_hour: int = 20,
        quiet_end_hour: int = 8,
        min_lead_minutes: int = 30,
        max_attempts_per_appointment: int = 3
    ):
        self.quiet_start_hour = quiet_start_hour
        self.quiet_end_hour = quiet_end_hour
        self.min_lead_minutes = min_lead_minutes
        self.max_attempts_per_appointment = max_attempts_per_appointment

    @staticmethod
    def is_landline_number(number: str) -> bool:
        if not number:
            return False
        clean = number.strip()
        parts = clean.split('-')
        if len(parts) >= 2:
            try:
                middle = int(parts[1])
                return 200 <= middle <= 249
            except ValueError:
                pass
        return False

    def is_quiet_hour(self, at_time: datetime) -> bool:
        hour = at_time.hour
        if self.quiet_start_hour > self.quiet_end_hour:
            # Over-night quiet hours e.g. 20:00 to 08:00
            return hour >= self.quiet_start_hour or hour < self.quiet_end_hour
        else:
            # Daytime quiet hours e.g. 12:00 to 14:00
            return self.quiet_start_hour <= hour < self.quiet_end_hour

    def get_next_allowed_time(self, at_time: datetime) -> datetime:
        if not self.is_quiet_hour(at_time):
            return at_time
        
        # If quiet hours are 20:00 to 08:00
        next_time = at_time
        if at_time.hour >= self.quiet_start_hour:
            # Move to next day 08:00
            next_day = at_time.date() + timedelta(days=1)
            next_time = datetime(next_day.year, next_day.month, next_day.day, self.quiet_end_hour, 0)
        elif at_time.hour < self.quiet_end_hour:
            # Move to today 08:00
            next_time = datetime(at_time.year, at_time.month, at_time.day, self.quiet_end_hour, 0)
        return next_time

    def is_too_close_to_appointment(self, current_time: datetime, scheduled_at: datetime) -> bool:
        lead_time = scheduled_at - current_time
        return lead_time < timedelta(minutes=self.min_lead_minutes)

    def evaluate_channel(
        self,
        resident: Resident,
        channel: ChannelType,
        at_time: datetime
    ) -> Tuple[bool, str, Optional[str], Optional[datetime]]:
        """
        Evaluates eligibility of a specific channel for a resident at a given time.
        Returns (is_eligible, reason, contact_value, deferred_time)
        """
        deferred_time = None
        if self.is_quiet_hour(at_time):
            deferred_time = self.get_next_allowed_time(at_time)

        if channel == ChannelType.SMS:
            if resident.sms_optout:
                return False, "SMS opt-out enforced", None, None
            mobile = resident.get_clean_mobile()
            if not mobile:
                return False, "No mobile number provided", None, None
            if self.is_landline_number(mobile):
                return False, "Mobile field contains landline number (SMS unroutable)", None, None
            return True, "Eligible", mobile, deferred_time

        elif channel == ChannelType.VOICE:
            if resident.voice_optout:
                return False, "Voice opt-out enforced", None, None
            # Voice can use mobile (if not landline) or landline
            mobile = resident.get_clean_mobile()
            landline = resident.get_clean_landline()
            phone = mobile if mobile else landline
            if not phone:
                return False, "No phone number available for voice call", None, None
            return True, "Eligible", phone, deferred_time

        elif channel == ChannelType.EMAIL:
            if resident.email_optout:
                return False, "Email opt-out enforced", None, None
            email = resident.get_clean_email()
            if not email:
                return False, "No email address provided", None, None
            return True, "Eligible", email, deferred_time

        return False, f"Unknown channel {channel}", None, None

    def get_eligible_channels(
        self,
        resident: Resident,
        at_time: datetime
    ) -> List[Tuple[ChannelType, str, Optional[datetime], str]]:
        """
        Returns all eligible channels in priority order: SMS -> Voice -> Email
        Each entry: (channel_type, contact_value, deferred_time, reason)
        """
        eligible = []
        for ch in [ChannelType.SMS, ChannelType.VOICE, ChannelType.EMAIL]:
            is_eligible, reason, contact_val, deferred_time = self.evaluate_channel(resident, ch, at_time)
            if is_eligible:
                eligible.append((ch, contact_val, deferred_time, reason))
        return eligible

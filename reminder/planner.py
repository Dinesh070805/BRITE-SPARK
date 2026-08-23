from datetime import datetime, timedelta
from typing import Tuple
from reminder.models import Appointment, Resident
from reminder.policy import ContactPolicy

class ReminderPlanner:
    def __init__(self, policy: ContactPolicy, advance_hours: int = 24):
        self.policy = policy
        self.advance_hours = advance_hours

    def plan_reminder_time(self, appointment: Appointment) -> Tuple[datetime, bool]:
        """
        Determines the planned execution time for a reminder given an appointment.
        Defers to next allowed time if planned time falls in quiet hours.
        Returns (planned_time, was_deferred)
        """
        ideal_time = appointment.scheduled_at - timedelta(hours=self.advance_hours)
        
        if self.policy.is_quiet_hour(ideal_time):
            deferred_time = self.policy.get_next_allowed_time(ideal_time)
            return deferred_time, True
            
        return ideal_time, False

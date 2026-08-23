import unittest
from datetime import datetime
from unittest.mock import patch
from reminder.models import Resident, Appointment, ChannelType, CommunicationStatus
from reminder.policy import ContactPolicy
from reminder.language import LanguageSelector
from reminder.dedup import DeduplicationService
from reminder.dispatcher import ReminderDispatcher
from reminder.adapters import SMSChannel, VoiceChannel, EmailChannel

class TestStoppingRules(unittest.TestCase):
    def test_stopping_rule_max_attempts(self):
        policy = ContactPolicy()
        lang = LanguageSelector()
        dedup = DeduplicationService()
        dispatcher = ReminderDispatcher(policy, lang, dedup, max_attempts=2)

        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="555-888-5678", email="test@example.com",
            language="en", sms_optout=False, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 0),
            location="Weybridge", service_type="Housing options", status="Booked"
        )

        with patch.object(SMSChannel, 'send', return_value={'status': 'failed', 'detail': 'carrier_rejected'}):
            with patch.object(VoiceChannel, 'send', return_value={'status': 'no_answer', 'detail': ''}):
                with patch.object(EmailChannel, 'send') as mock_email:
                    attempts = dispatcher.dispatch_reminder(appointment, resident, datetime(2026, 3, 1, 10, 0))
                    self.assertEqual(len(attempts), 2)
                    mock_email.assert_not_called()

    def test_too_close_to_appointment_stops(self):
        policy = ContactPolicy(min_lead_minutes=30)
        lang = LanguageSelector()
        dedup = DeduplicationService()
        dispatcher = ReminderDispatcher(policy, lang, dedup)

        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="",
            language="en", sms_optout=False, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 10),
            location="Weybridge", service_type="Housing options", status="Booked"
        )

        attempts = dispatcher.dispatch_reminder(appointment, resident, datetime(2026, 3, 2, 10, 0))
        self.assertEqual(len(attempts), 0)
        self.assertEqual(len(dispatcher.audit_records), 1)
        self.assertEqual(dispatcher.audit_records[0].outcome, "too_close_to_appointment")

if __name__ == "__main__":
    unittest.main()

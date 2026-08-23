import unittest
from datetime import datetime
from unittest.mock import patch
from reminder.models import Resident, Appointment, ChannelType, CommunicationStatus
from reminder.policy import ContactPolicy
from reminder.language import LanguageSelector
from reminder.dedup import DeduplicationService
from reminder.dispatcher import ReminderDispatcher
from reminder.adapters import VoiceChannel, EmailChannel, SMSChannel

class TestReminderDispatcher(unittest.TestCase):
    def test_voice_human_answer_stops_fallback(self):
        policy = ContactPolicy()
        lang = LanguageSelector()
        dedup = DeduplicationService()
        dispatcher = ReminderDispatcher(policy, lang, dedup)

        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=True, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 0),
            location="Weybridge", service_type="Housing options", status="Booked"
        )

        with patch.object(VoiceChannel, 'send', return_value={'status': 'answered', 'detail': 'human'}):
            with patch.object(EmailChannel, 'send') as mock_email:
                attempts = dispatcher.dispatch_reminder(appointment, resident, datetime(2026, 3, 1, 10, 0))
                self.assertEqual(len(attempts), 1)
                self.assertEqual(attempts[0].channel, ChannelType.VOICE)
                self.assertEqual(attempts[0].status, CommunicationStatus.REACHED)
                self.assertTrue(attempts[0].reached)
                mock_email.assert_not_called()

    def test_voice_voicemail_does_not_count_as_human_reach_and_falls_back(self):
        policy = ContactPolicy()
        lang = LanguageSelector()
        dedup = DeduplicationService()
        dispatcher = ReminderDispatcher(policy, lang, dedup)

        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=True, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 0),
            location="Weybridge", service_type="Housing options", status="Booked"
        )

        with patch.object(VoiceChannel, 'send', return_value={'status': 'answered', 'detail': 'voicemail_left'}):
            with patch.object(EmailChannel, 'send', return_value={'status': 'delivered', 'detail': ''}):
                attempts = dispatcher.dispatch_reminder(appointment, resident, datetime(2026, 3, 1, 10, 0))
                self.assertEqual(len(attempts), 2)
                self.assertEqual(attempts[0].channel, ChannelType.VOICE)
                self.assertFalse(attempts[0].reached)
                self.assertEqual(attempts[1].channel, ChannelType.EMAIL)

    def test_sms_failure_triggers_fallback(self):
        policy = ContactPolicy()
        lang = LanguageSelector()
        dedup = DeduplicationService()
        dispatcher = ReminderDispatcher(policy, lang, dedup)

        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=False, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 0),
            location="Weybridge", service_type="Housing options", status="Booked"
        )

        with patch.object(SMSChannel, 'send', return_value={'status': 'failed', 'detail': 'unknown_subscriber'}):
            with patch.object(VoiceChannel, 'send', return_value={'status': 'answered', 'detail': 'human'}):
                attempts = dispatcher.dispatch_reminder(appointment, resident, datetime(2026, 3, 1, 10, 0))
                self.assertEqual(len(attempts), 2)
                self.assertEqual(attempts[0].channel, ChannelType.SMS)
                self.assertEqual(attempts[0].status, CommunicationStatus.FAILED)
                self.assertEqual(attempts[1].channel, ChannelType.VOICE)
                self.assertEqual(attempts[1].status, CommunicationStatus.REACHED)

if __name__ == "__main__":
    unittest.main()

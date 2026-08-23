import unittest
from datetime import datetime
from reminder.models import Resident, ChannelType
from reminder.policy import ContactPolicy

class TestContactPolicy(unittest.TestCase):
    def test_sms_optout_prevents_sms(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=True, voice_optout=False, email_optout=False
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = policy.evaluate_channel(resident, ChannelType.SMS, at_time)
        self.assertFalse(eligible)
        self.assertIn("SMS opt-out enforced", reason)

    def test_voice_optout_prevents_voice(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=False, voice_optout=True, email_optout=False
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = policy.evaluate_channel(resident, ChannelType.VOICE, at_time)
        self.assertFalse(eligible)
        self.assertIn("Voice opt-out enforced", reason)

    def test_email_optout_prevents_email(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="test@example.com",
            language="en", sms_optout=False, voice_optout=False, email_optout=True
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = policy.evaluate_channel(resident, ChannelType.EMAIL, at_time)
        self.assertFalse(eligible)
        self.assertIn("Email opt-out enforced", reason)

    def test_quiet_hours_blocks_and_defers_communication(self):
        policy = ContactPolicy(quiet_start_hour=20, quiet_end_hour=8)
        at_night = datetime(2026, 3, 2, 21, 30)
        self.assertTrue(policy.is_quiet_hour(at_night))
        deferred_time = policy.get_next_allowed_time(at_night)
        self.assertEqual(deferred_time, datetime(2026, 3, 3, 8, 0))

    def test_missing_contact_info_stops_cleanly(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="", landline="", email="",
            language="en", sms_optout=False, voice_optout=False, email_optout=False
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        channels = policy.get_eligible_channels(resident, at_time)
        self.assertEqual(len(channels), 0)

    def test_all_channels_opted_out_stops_cleanly(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="555-212-3456", email="test@example.com",
            language="en", sms_optout=True, voice_optout=True, email_optout=True
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        channels = policy.get_eligible_channels(resident, at_time)
        self.assertEqual(len(channels), 0)

    def test_landline_number_prevents_sms(self):
        policy = ContactPolicy()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-214-9004", landline="", email="",
            language="en", sms_optout=False, voice_optout=False, email_optout=False
        )
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = policy.evaluate_channel(resident, ChannelType.SMS, at_time)
        self.assertFalse(eligible)
        self.assertIn("landline number", reason)

if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import ResidentDB, AppointmentDB, ReminderDB, ReminderAttemptDB, PolicyDB
from backend.app.services.contact_policy import ContactPolicyService

class TestContactPolicyAndRegulatoryDirection(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.db = Session()

        self.config = PolicyDB(id=1, quiet_hours_start=20, quiet_hours_end=8, max_attempts=3, channel_priority="SMS,Voice,Email")
        self.policy = ContactPolicyService(self.config)

        # Setup sample residents
        self.resident1 = ResidentDB(id="RS-4001", name="Alice Smith", mobile="555-888-1001", email="alice@example.com")
        self.resident2 = ResidentDB(id="RS-4002", name="Bob Jones", mobile="555-888-1001", email="bob@example.com") # Shared phone number with RS-4001
        self.db.add_all([self.resident1, self.resident2])

        # Setup sample appointment
        self.app1 = AppointmentDB(id="AP-1001", resident_id="RS-4001", scheduled_at=datetime(2026, 3, 10, 10, 0), location="Northgate", service_type="Housing")
        self.app2 = AppointmentDB(id="AP-1002", resident_id="RS-4002", scheduled_at=datetime(2026, 3, 10, 11, 0), location="Ash Hill", service_type="Debt advice")
        self.db.add_all([self.app1, self.app2])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_sms_optout(self):
        res = ResidentDB(id="R1", name="Test", sms_optout=True, mobile="555-888-1234")
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = self.policy.evaluate_channel(res, "sms", at_time)
        self.assertFalse(eligible)
        self.assertIn("SMS opt-out", reason)

    def test_quiet_hours(self):
        at_night = datetime(2026, 3, 2, 21, 30)
        self.assertTrue(self.policy.is_quiet_hour(at_night))
        deferred = self.policy.get_next_allowed_time(at_night)
        self.assertEqual(deferred, datetime(2026, 3, 3, 8, 0))

    def test_landline_sms_safety(self):
        res = ResidentDB(id="R1", name="Test", mobile="555-214-9004")
        at_time = datetime(2026, 3, 2, 10, 0)
        eligible, reason, contact, _ = self.policy.evaluate_channel(res, "sms", at_time)
        self.assertFalse(eligible)
        self.assertIn("landline number", reason)

    # --- DIRECTION CR-2026/11 REGULATORY TESTS ---

    def test_zero_contacts_allowed(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertTrue(eval_res["permitted"])
        self.assertFalse(eval_res["withheld"])
        self.assertEqual(eval_res["prior_contacts_count"], 0)

    def test_one_contact_allowed(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        att = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 4, 10, 0), status="delivered")
        self.db.add(att)
        self.db.commit()

        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertTrue(eval_res["permitted"])
        self.assertEqual(eval_res["prior_contacts_count"], 1)

    def test_two_contacts_blocked(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        att1 = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 10, 0), status="delivered")
        att2 = ReminderAttemptDB(id=2, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=2, timestamp=datetime(2026, 3, 4, 10, 0), status="delivered")
        self.db.add_all([att1, att2])
        self.db.commit()

        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertFalse(eval_res["permitted"])
        self.assertTrue(eval_res["withheld"])
        self.assertEqual(eval_res["prior_contacts_count"], 2)

    def test_two_contacts_across_different_channels_blocked(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        att1 = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 10, 0), status="delivered")
        att2 = ReminderAttemptDB(id=2, reminder_id=1, channel="voice", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 4, 10, 0), status="answered")
        self.db.add_all([att1, att2])
        self.db.commit()

        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertFalse(eval_res["permitted"])

    def test_failed_attempts_count_towards_limit(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        # Both attempts failed
        att1 = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 10, 0), status="failed", provider_detail="carrier_rejected")
        att2 = ReminderAttemptDB(id=2, reminder_id=1, channel="email", contact="alice@example.com", attempt_number=1, timestamp=datetime(2026, 3, 4, 10, 0), status="failed", provider_detail="soft_bounce")
        self.db.add_all([att1, att2])
        self.db.commit()

        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertEqual(eval_res["prior_contacts_count"], 2)
        self.assertFalse(eval_res["permitted"])

    def test_unanswered_and_voicemail_attempts_count(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        att1 = ReminderAttemptDB(id=1, reminder_id=1, channel="voice", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 10, 0), status="no_answer", provider_detail="")
        att2 = ReminderAttemptDB(id=2, reminder_id=1, channel="voice", contact="555-888-1001", attempt_number=2, timestamp=datetime(2026, 3, 4, 10, 0), status="answered", provider_detail="voicemail_left")
        self.db.add_all([att1, att2])
        self.db.commit()

        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertEqual(eval_res["prior_contacts_count"], 2)
        self.assertFalse(eval_res["permitted"])

    def test_contacts_counted_per_resident_and_shared_contact(self):
        at_time = datetime(2026, 3, 5, 10, 0)

        # 2 attempts for RS-4001 (Alice)
        rem1 = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem1)
        self.db.commit()
        att1 = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 10, 0), status="delivered")
        att2 = ReminderAttemptDB(id=2, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=2, timestamp=datetime(2026, 3, 3, 10, 0), status="delivered")
        self.db.add_all([att1, att2])
        self.db.commit()

        # Alice is blocked
        eval_alice = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertFalse(eval_alice["permitted"])

        # Bob (RS-4002) shares same mobile number "555-888-1001" but has 0 attempts
        eval_bob = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4002", at_time, "AP-1002")
        self.assertTrue(eval_bob["permitted"])
        self.assertEqual(eval_bob["prior_contacts_count"], 0)

    def test_rolling_seven_day_window_boundary(self):
        at_time = datetime(2026, 3, 10, 10, 0)
        rem = ReminderDB(id=1, appointment_id="AP-1001", resident_id="RS-4001", scheduled_at=at_time)
        self.db.add(rem)
        self.db.commit()

        # Attempt 1 is 8 days ago (outside 7-day rolling window)
        att_old = ReminderAttemptDB(id=1, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=1, timestamp=datetime(2026, 3, 2, 9, 59), status="delivered")
        # Attempt 2 is 3 days ago (inside window)
        att_recent = ReminderAttemptDB(id=2, reminder_id=1, channel="sms", contact="555-888-1001", attempt_number=2, timestamp=datetime(2026, 3, 7, 10, 0), status="delivered")
        self.db.add_all([att_old, att_recent])
        self.db.commit()

        # Only recent attempt should count (count = 1)
        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")
        self.assertTrue(eval_res["permitted"])
        self.assertEqual(eval_res["prior_contacts_count"], 1)

    def test_audit_evidence_details_and_prioritisation(self):
        at_time = datetime(2026, 3, 5, 10, 0)
        eval_res = ContactPolicyService.evaluate_regulatory_limit(self.db, "RS-4001", at_time, "AP-1001")

        self.assertIn("prior_contacts_count", eval_res)
        self.assertIn("max_allowed_contacts", eval_res)
        self.assertEqual(eval_res["max_allowed_contacts"], 2)
        self.assertIn("prioritisation_basis", eval_res)
        self.assertIn("non-discriminatory", eval_res["prioritisation_basis"])

if __name__ == "__main__":
    unittest.main()

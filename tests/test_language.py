import unittest
from datetime import datetime
from reminder.models import Resident, Appointment
from reminder.language import LanguageSelector

class TestLanguageSelector(unittest.TestCase):
    def test_supported_languages(self):
        selector = LanguageSelector()
        for lang in ["en", "es", "vi", "so", "ru", "zh"]:
            res_lang, is_fallback = selector.select_template(lang)
            self.assertEqual(res_lang, lang)
            self.assertFalse(is_fallback)

    def test_unsupported_language_falls_back_to_english(self):
        selector = LanguageSelector()
        res_lang, is_fallback = selector.select_template("fr")
        self.assertEqual(res_lang, "en")
        self.assertTrue(is_fallback)
        self.assertEqual(selector.fallback_count, 1)

    def test_language_fallback_is_recorded(self):
        selector = LanguageSelector()
        resident = Resident(
            resident_id="R1", name="Test", mobile="555-888-1234", landline="", email="",
            language="de", sms_optout=False, voice_optout=False, email_optout=False
        )
        appointment = Appointment(
            appointment_id="A1", resident_id="R1", scheduled_at=datetime(2026, 3, 2, 10, 0),
            location="Weybridge", service_type="Housing options", status="Booked"
        )
        body, used_lang, is_fallback = selector.render_reminder(resident, appointment)
        self.assertEqual(used_lang, "en")
        self.assertTrue(is_fallback)
        self.assertEqual(selector.fallback_count, 1)
        self.assertIn("Hello Test", body)

if __name__ == "__main__":
    unittest.main()

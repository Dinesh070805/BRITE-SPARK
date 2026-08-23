import unittest
from reminder.models import ChannelType
from reminder.dedup import DeduplicationService

class TestDeduplicationService(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(DeduplicationService.normalize_phone("555-853-5210"), "5558535210")
        self.assertEqual(DeduplicationService.normalize_phone(" +1 (555) 853-5210 "), "15558535210")
        self.assertEqual(DeduplicationService.normalize_email(" Priya.Whitlock@Example.Net "), "priya.whitlock@example.net")

    def test_shared_contact_point_prevents_duplicate_reminder(self):
        dedup = DeduplicationService()
        contact = "555-853-5210"
        app_id = "AP-70238"
        
        self.assertFalse(dedup.is_duplicate(contact, ChannelType.SMS, app_id))
        dedup.record_dispatch(contact, ChannelType.SMS, app_id)

        self.assertTrue(dedup.is_duplicate(contact, ChannelType.SMS, app_id))
        self.assertTrue(dedup.is_duplicate("5558535210", ChannelType.SMS, app_id))

if __name__ == "__main__":
    unittest.main()

import re
from typing import Set, Tuple

class DeduplicationService:
    def __init__(self):
        # Stores (normalized_contact, channel, appointment_id)
        self._sent_keys: Set[Tuple[str, str, str]] = set()
        self.duplicate_prevented_count = 0

    @staticmethod
    def normalize_phone(phone: str) -> str:
        if not phone:
            return ""
        return re.sub(r'\D', '', phone.strip())

    @staticmethod
    def normalize_email(email: str) -> str:
        if not email:
            return ""
        return email.strip().lower()

    def normalize_contact(self, contact: str, channel: str) -> str:
        ch = channel.lower()
        if ch in ("sms", "voice"):
            return self.normalize_phone(contact)
        elif ch == "email":
            return self.normalize_email(contact)
        return contact.strip()

    def is_duplicate(self, contact: str, channel: str, appointment_id: str) -> bool:
        norm = self.normalize_contact(contact, channel)
        if not norm:
            return False
        key = (norm, channel.lower(), appointment_id)
        return key in self._sent_keys

    def record_dispatch(self, contact: str, channel: str, appointment_id: str) -> None:
        norm = self.normalize_contact(contact, channel)
        if norm:
            key = (norm, channel.lower(), appointment_id)
            self._sent_keys.add(key)

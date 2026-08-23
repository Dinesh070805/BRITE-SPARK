import re
from typing import Set, Tuple
from reminder.models import ChannelType

class DeduplicationService:
    """
    Dedicated deduplication layer.
    Normalizes contact points (phone numbers to digits-only, email to lowercased trimmed string)
    and tracks dispatched reminders to prevent sending duplicate messages to the same contact point
    for the same channel and appointment.
    """
    def __init__(self):
        # Stores (normalized_contact_point, channel_type, appointment_id)
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

    def normalize_contact(self, contact: str, channel: ChannelType) -> str:
        if channel in (ChannelType.SMS, ChannelType.VOICE):
            return self.normalize_phone(contact)
        elif channel == ChannelType.EMAIL:
            return self.normalize_email(contact)
        return contact.strip()

    def is_duplicate(self, contact: str, channel: ChannelType, appointment_id: str) -> bool:
        norm_contact = self.normalize_contact(contact, channel)
        if not norm_contact:
            return False
        key = (norm_contact, channel.value if isinstance(channel, ChannelType) else str(channel), appointment_id)
        return key in self._sent_keys

    def record_dispatch(self, contact: str, channel: ChannelType, appointment_id: str) -> None:
        norm_contact = self.normalize_contact(contact, channel)
        if norm_contact:
            key = (norm_contact, channel.value if isinstance(channel, ChannelType) else str(channel), appointment_id)
            self._sent_keys.add(key)

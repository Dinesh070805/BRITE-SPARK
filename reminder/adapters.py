from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from channels.channels import send_sms, send_voice, send_email
from reminder.models import ChannelType

class ChannelAdapter(ABC):
    @abstractmethod
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        pass

class SMSChannel(ChannelAdapter):
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        return send_sms(to=to_contact, body=body, at=at_time, attempt=attempt)

class VoiceChannel(ChannelAdapter):
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        return send_voice(to=to_contact, body=body, at=at_time, attempt=attempt)

class EmailChannel(ChannelAdapter):
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        return send_email(to=to_contact, body=body, at=at_time, attempt=attempt)

def get_channel_adapter(channel_type: ChannelType) -> ChannelAdapter:
    if channel_type == ChannelType.SMS:
        return SMSChannel()
    elif channel_type == ChannelType.VOICE:
        return VoiceChannel()
    elif channel_type == ChannelType.EMAIL:
        return EmailChannel()
    raise ValueError(f"Unsupported channel type: {channel_type}")

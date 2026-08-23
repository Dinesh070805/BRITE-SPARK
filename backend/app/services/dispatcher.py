from datetime import datetime
from typing import Dict, Any
from backend.app.channels.sms import SMSChannelAdapter
from backend.app.channels.voice import VoiceChannelAdapter
from backend.app.channels.email import EmailChannelAdapter

class ChannelDispatcher:
    def __init__(self):
        self.sms_adapter = SMSChannelAdapter()
        self.voice_adapter = VoiceChannelAdapter()
        self.email_adapter = EmailChannelAdapter()

    def dispatch(self, channel: str, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        ch = channel.lower()
        if ch == "sms":
            return self.sms_adapter.send(to_contact, body, at_time, attempt)
        elif ch == "voice":
            return self.voice_adapter.send(to_contact, body, at_time, attempt)
        elif ch == "email":
            return self.email_adapter.send(to_contact, body, at_time, attempt)
        raise ValueError(f"Unsupported channel: {channel}")

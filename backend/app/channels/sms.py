from datetime import datetime
from typing import Dict, Any
from channels.channels import send_sms

class SMSChannelAdapter:
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        return send_sms(to=to_contact, body=body, at=at_time, attempt=attempt)

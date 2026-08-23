from datetime import datetime
from typing import Dict, Any
from channels.channels import send_email

class EmailChannelAdapter:
    def send(self, to_contact: str, body: str, at_time: datetime, attempt: int = 1) -> Dict[str, Any]:
        return send_email(to=to_contact, body=body, at=at_time, attempt=attempt)

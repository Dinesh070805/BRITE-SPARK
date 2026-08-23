from typing import Tuple

class OutcomeInterpreter:
    """
    Interprets mock channel responses and classifies status vs confirmed human reach.
    """
    @staticmethod
    def interpret(channel: str, contact_val: str, status_str: str, detail_str: str, is_landline: bool) -> Tuple[str, bool, str]:
        """
        Returns (comm_status, is_reached, failure_reason)
        """
        ch = channel.lower()
        if ch == "sms":
            if status_str == "delivered":
                if detail_str == "accepted_by_carrier" and is_landline:
                    return "failed", False, "accepted_by_carrier_landline_unreachable"
                return "delivered", False, ""
            return "failed", False, detail_str or "sms_carrier_failed"

        elif ch == "voice":
            if status_str == "answered":
                if detail_str == "human":
                    return "reached", True, ""
                else:
                    return "delivered", False, "voicemail_left"
            return "failed", False, detail_str or "no_answer"

        elif ch == "email":
            if status_str == "delivered":
                return "delivered", False, ""
            return "failed", False, detail_str or "email_bounce"

        return "failed", False, "unknown_channel"

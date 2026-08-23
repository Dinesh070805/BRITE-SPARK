import json
import csv
from typing import List, Dict, Any
from reminder.models import AuditRecord, ReminderAttempt, ChannelType, CommunicationStatus

class MetricsCollector:
    def __init__(self):
        self.audit_records: List[AuditRecord] = []

    def add_audit_records(self, records: List[AuditRecord]):
        self.audit_records.extend(records)

    def write_audit_log_csv(self, filepath: str = "audit_log.csv"):
        if not self.audit_records:
            return
        fieldnames = list(self.audit_records[0].to_dict().keys())
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self.audit_records:
                writer.writerow(rec.to_dict())

    def write_audit_log_json(self, filepath: str = "audit_log.json"):
        records_dict = [rec.to_dict() for rec in self.audit_records]
        with open(filepath, mode='w', encoding='utf-8') as f:
            json.dump(records_dict, f, indent=2)

    def compute_metrics(
        self,
        total_appointments: int,
        total_residents: int,
        language_fallback_count: int = 0
    ) -> Dict[str, Any]:
        # Aggregate counts
        appointments_processed = total_appointments
        residents_processed = total_residents

        reminder_attempts = sum(1 for r in self.audit_records if r.status in ("delivered", "reached", "failed"))

        reached_residents = set(r.resident_id for r in self.audit_records if r.reached)
        residents_reached_count = len(reached_residents)

        # Residents needing reminders (all residents in processed appointments)
        all_app_residents = set(r.resident_id for r in self.audit_records)
        residents_not_reached_count = len(all_app_residents - reached_residents)

        no_eligible_contact_count = sum(1 for r in self.audit_records if r.outcome in ("no_contact_info", "no_eligible_channels"))
        optout_blocked_count = sum(1 for r in self.audit_records if r.outcome == "all_opted_out" or "opt-out" in r.reason.lower())
        quiet_hour_deferred_count = sum(1 for r in self.audit_records if r.deferred)
        duplicate_prevented_count = sum(1 for r in self.audit_records if r.duplicate_prevented)

        # Per channel breakdown
        sms_attempts = sum(1 for r in self.audit_records if r.channel == ChannelType.SMS.value)
        sms_delivered = sum(1 for r in self.audit_records if r.channel == ChannelType.SMS.value and r.status == "delivered")
        sms_failures = sms_attempts - sms_delivered

        voice_attempts = sum(1 for r in self.audit_records if r.channel == ChannelType.VOICE.value)
        voice_human_answered = sum(1 for r in self.audit_records if r.channel == ChannelType.VOICE.value and r.outcome == "human")
        voice_voicemail = sum(1 for r in self.audit_records if r.channel == ChannelType.VOICE.value and r.outcome == "voicemail_left")
        voice_no_answer = voice_attempts - voice_human_answered - voice_voicemail

        email_attempts = sum(1 for r in self.audit_records if r.channel == ChannelType.EMAIL.value)
        email_delivered = sum(1 for r in self.audit_records if r.channel == ChannelType.EMAIL.value and r.status == "delivered")
        email_failures = email_attempts - email_delivered

        # Language breakdown
        language_counts: Dict[str, int] = {}
        for r in self.audit_records:
            if r.language:
                language_counts[r.language] = language_counts.get(r.language, 0) + 1

        # Ratios
        total_delivered = sms_delivered + voice_human_answered + voice_voicemail + email_delivered
        delivery_rate = (total_delivered / reminder_attempts * 100.0) if reminder_attempts > 0 else 0.0

        residents_requiring_reminders = len(all_app_residents)
        reach_rate = (residents_reached_count / residents_requiring_reminders * 100.0) if residents_requiring_reminders > 0 else 0.0

        return {
            "summary": {
                "appointments_processed": appointments_processed,
                "residents_processed": residents_processed,
                "residents_requiring_reminders": residents_requiring_reminders,
                "reminder_attempts": reminder_attempts,
                "residents_reached": residents_reached_count,
                "residents_not_reached": residents_not_reached_count,
                "no_eligible_contact": no_eligible_contact_count,
                "optout_blocked": optout_blocked_count,
                "quiet_hour_deferred": quiet_hour_deferred_count,
                "duplicate_attempts_prevented": duplicate_prevented_count,
            },
            "rates": {
                "delivery_rate_percent": round(delivery_rate, 2),
                "reach_rate_percent": round(reach_rate, 2),
            },
            "channels": {
                "sms": {
                    "attempts": sms_attempts,
                    "delivered": sms_delivered,
                    "failures": sms_failures,
                },
                "voice": {
                    "attempts": voice_attempts,
                    "human_answered": voice_human_answered,
                    "voicemail": voice_voicemail,
                    "no_answer_or_failed": voice_no_answer,
                },
                "email": {
                    "attempts": email_attempts,
                    "delivered": email_delivered,
                    "failures": email_failures,
                }
            },
            "languages": {
                "counts_per_language": language_counts,
                "english_fallbacks": language_fallback_count,
            }
        }

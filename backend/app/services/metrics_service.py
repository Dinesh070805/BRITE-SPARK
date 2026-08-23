from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.app.models import (
    AppointmentDB, ResidentDB, ReminderDB, ReminderAttemptDB, AuditLogDB
)

class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        total_appointments = self.db.query(AppointmentDB).count()
        total_residents = self.db.query(ResidentDB).count()

        reminders_attempted = self.db.query(ReminderAttemptDB).count()
        
        # Residents reached
        reached_residents_count = self.db.query(func.count(func.distinct(ReminderDB.resident_id))).filter(ReminderDB.reached == True).scalar() or 0

        # Unique residents needing reminders
        app_residents_count = self.db.query(func.count(func.distinct(AppointmentDB.resident_id))).scalar() or 0

        # Calculations
        reach_rate = round((reached_residents_count / app_residents_count * 100.0), 2) if app_residents_count > 0 else 0.0

        delivered_attempts = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.status.in_(["delivered", "reached"])).count()
        delivery_rate = round((delivered_attempts / reminders_attempted * 100.0), 2) if reminders_attempted > 0 else 0.0

        failed_count = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.status == "failed").count()
        deferred_count = self.db.query(AuditLogDB).filter(AuditLogDB.action == "DEFERRED").count()
        blocked_count = self.db.query(AuditLogDB).filter(AuditLogDB.action == "BLOCKED").count()
        duplicates_prevented = self.db.query(AuditLogDB).filter(AuditLogDB.action == "DUPLICATE_PREVENTED").count()

        # Channel stats
        sms_attempts = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "sms").count()
        sms_delivered = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "sms", ReminderAttemptDB.status == "delivered").count()

        voice_attempts = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "voice").count()
        voice_human = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "voice", ReminderAttemptDB.status == "reached").count()
        voice_voicemail = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "voice", ReminderAttemptDB.provider_detail == "voicemail_left").count()

        email_attempts = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "email").count()
        email_delivered = self.db.query(ReminderAttemptDB).filter(ReminderAttemptDB.channel == "email", ReminderAttemptDB.status == "delivered").count()

        # Language stats
        lang_rows = self.db.query(ReminderDB.language, func.count(ReminderDB.id)).group_by(ReminderDB.language).all()
        language_stats = {lang: count for lang, count in lang_rows if lang}

        return {
            "appointments": total_appointments,
            "residents": total_residents,
            "reminders_attempted": reminders_attempted,
            "residents_reached": reached_residents_count,
            "reach_rate": reach_rate,
            "delivery_rate": delivery_rate,
            "failed": failed_count,
            "deferred": deferred_count,
            "blocked": blocked_count,
            "duplicates_prevented": duplicates_prevented,
            "channel_stats": {
                "sms": {"attempts": sms_attempts, "delivered": sms_delivered, "failed": sms_attempts - sms_delivered},
                "voice": {"attempts": voice_attempts, "human": voice_human, "voicemail": voice_voicemail, "failed": voice_attempts - voice_human - voice_voicemail},
                "email": {"attempts": email_attempts, "delivered": email_delivered, "failed": email_attempts - email_delivered}
            },
            "language_stats": language_stats
        }

from typing import Tuple, Dict
from backend.app.models import ResidentDB, AppointmentDB

TEMPLATES: Dict[str, str] = {
    "en": "Hello {name}, this is a reminder for your {service_type} appointment on {date_str} at {location}.",
    "es": "Hola {name}, este es un recordatorio para su cita de {service_type} el {date_str} en {location}.",
    "vi": "Xin chào {name}, đây là lời nhắc cho cuộc hẹn {service_type} của bạn vào {date_str} tại {location}.",
    "so": "Salamaan {name}, kani waa xusuusin ku saabsan ballantaada {service_type} ee {date_str} ee {location}.",
    "ru": "Здравствуйте, {name}, это напоминание о вашей встрече ({service_type}) {date_str} в {location}.",
    "zh": "您好 {name}，这是关于您于 {date_str} 在 {location} 的 {service_type} 预约的提醒。",
}

class LanguageService:
    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.fallback_count = 0

    def select_template(self, requested_lang: str) -> Tuple[str, bool]:
        lang = (requested_lang or "").strip().lower()
        if lang in TEMPLATES:
            return lang, False
        self.fallback_count += 1
        return self.default_language, True

    def render_reminder(self, resident: ResidentDB, appointment: AppointmentDB) -> Tuple[str, str, bool]:
        lang, is_fallback = self.select_template(resident.language)
        template = TEMPLATES[lang]
        date_str = appointment.scheduled_at.strftime("%Y-%m-%d at %H:%M")
        body = template.format(
            name=resident.name,
            service_type=appointment.service_type,
            date_str=date_str,
            location=appointment.location
        )
        return body, lang, is_fallback

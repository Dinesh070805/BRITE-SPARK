import csv
from datetime import datetime
from typing import List, Dict, Tuple
from reminder.models import Resident, Appointment

def parse_date(date_str: str) -> datetime:
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse date: '{date_str}'")

def load_contacts(filepath: str) -> Dict[str, Resident]:
    contacts = {}
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            res_id = row['resident_id'].strip()
            verified = parse_date(row.get('number_last_verified', ''))
            resident = Resident(
                resident_id=res_id,
                name=row['name'].strip(),
                mobile=row['mobile'].strip(),
                landline=row['landline'].strip(),
                email=row['email'].strip(),
                language=row['language'].strip(),
                sms_optout=row['sms_optout'].strip().upper() == 'Y',
                voice_optout=row['voice_optout'].strip().upper() == 'Y',
                email_optout=row['email_optout'].strip().upper() == 'Y',
                number_last_verified=verified
            )
            contacts[res_id] = resident
    return contacts

def load_appointments(filepath: str) -> List[Appointment]:
    appointments = []
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            app_id = row['appointment_id'].strip()
            res_id = row['resident_id'].strip()
            sched_at = parse_date(row['scheduled_at'])
            app = Appointment(
                appointment_id=app_id,
                resident_id=res_id,
                scheduled_at=sched_at,
                location=row['location'].strip(),
                service_type=row['service_type'].strip(),
                status=row['status'].strip()
            )
            appointments.append(app)
    return appointments

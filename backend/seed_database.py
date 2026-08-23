#!/usr/bin/env python3
"""
Seed script to import CSV data into SQLite database.
Run: python backend/seed_database.py
"""
import sys
import os
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, Base, SessionLocal
from backend.app.models import ResidentDB, AppointmentDB, PolicyDB

def parse_datetime(val: str):
    if not val or not val.strip():
        return None
    val = val.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            pass
    return None

def seed_database(contacts_path="data/contacts.csv", appointments_path="data/appointments.csv"):
    print("==================================================")
    print("      SEEDING DATABASE — CALDER COUNTY            ")
    print("==================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Clear existing records
    db.query(AppointmentDB).delete()
    db.query(ResidentDB).delete()
    db.query(PolicyDB).delete()
    db.commit()

    # Seed Default Policy
    default_policy = PolicyDB(id=1, quiet_hours_start=20, quiet_hours_end=8, max_attempts=3, channel_priority="SMS,Voice,Email")
    db.add(default_policy)
    db.commit()

    # 2. Seed Contacts
    residents_count = 0
    with open(contacts_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            res_id = row['resident_id'].strip()
            verified = parse_datetime(row.get('number_last_verified', ''))
            resident = ResidentDB(
                id=res_id,
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
            db.add(resident)
            residents_count += 1

    db.commit()

    # 3. Seed Appointments
    appointments_count = 0
    with open(appointments_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            app_id = row['appointment_id'].strip()
            res_id = row['resident_id'].strip()
            sched_at = parse_datetime(row['scheduled_at'])
            app = AppointmentDB(
                id=app_id,
                resident_id=res_id,
                scheduled_at=sched_at,
                location=row['location'].strip(),
                service_type=row['service_type'].strip(),
                status=row['status'].strip()
            )
            db.add(app)
            appointments_count += 1

    db.commit()
    db.close()

    print(f"Successfully imported {residents_count} residents and {appointments_count} appointments into SQLite.")
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_database()

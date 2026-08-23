"""
Challenge Dataset Analysis Script
Analyzes appointments.csv and contacts.csv to identify edge cases, data quality issues,
preferred languages, channel availability, and opt-out rates.
"""

import csv
import os

def analyze_dataset():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    appointments_path = os.path.join(base_dir, 'appointments.csv')
    contacts_path = os.path.join(base_dir, 'contacts.csv')

    print("=== Analyzing Challenge Dataset ===")
    
    # 1. Analyze Appointments
    appointments = []
    if os.path.exists(appointments_path):
        with open(appointments_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                appointments.append(row)
    print(f"Total Appointments: {len(appointments)}")

    # 2. Analyze Contacts
    contacts = []
    if os.path.exists(contacts_path):
        with open(contacts_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append(row)
    print(f"Total Resident Contacts: {len(contacts)}")

    # 3. Edge Cases Breakdown
    languages = {}
    mobile_count = 0
    landline_count = 0
    email_count = 0
    sms_optouts = 0
    voice_optouts = 0
    email_optouts = 0
    shared_mobiles = {}

    for c in contacts:
        lang = c.get('language', 'en')
        languages[lang] = languages.get(lang, 0) + 1
        
        mob = c.get('mobile', '').strip()
        if mob:
            mobile_count += 1
            shared_mobiles[mob] = shared_mobiles.get(mob, 0) + 1
        if c.get('landline', '').strip():
            landline_count += 1
        if c.get('email', '').strip():
            email_count += 1

        if c.get('sms_optout') == 'Y':
            sms_optouts += 1
        if c.get('voice_optout') == 'Y':
            voice_optouts += 1
        if c.get('email_optout') == 'Y':
            email_optouts += 1

    shared_phone_count = sum(1 for m, count in shared_mobiles.items() if count > 1)

    print("\n--- Key Insights ---")
    print(f"Language Distribution: {languages}")
    print(f"Contacts with Mobile: {mobile_count}/{len(contacts)}")
    print(f"Contacts with Landline: {landline_count}/{len(contacts)}")
    print(f"Contacts with Email: {email_count}/{len(contacts)}")
    print(f"Shared Mobile Numbers: {shared_phone_count}")
    print(f"Opt-Outs -> SMS: {sms_optouts}, Voice: {voice_optouts}, Email: {email_optouts}")

if __name__ == '__main__':
    analyze_dataset()

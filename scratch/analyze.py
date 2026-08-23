import csv
from collections import Counter, defaultdict
from datetime import datetime

contacts_path = "data/contacts.csv"
appointments_path = "data/appointments.csv"

contacts = {}
with open(contacts_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        contacts[row['resident_id']] = row

appointments = []
with open(appointments_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        appointments.append(row)

print("=== DATASET ANALYSIS ===")
print(f"Total Appointments: {len(appointments)}")
print(f"Total Contacts/Residents: {len(contacts)}")

# Check appointment status values
app_statuses = Counter(a['status'] for a in appointments)
print(f"Appointment Statuses: {dict(app_statuses)}")

# Residents in appointments
app_residents = set(a['resident_id'] for a in appointments)
print(f"Unique Residents with appointments: {len(app_residents)}")
missing_residents_in_contacts = app_residents - set(contacts.keys())
print(f"Appointment residents missing from contacts.csv: {len(missing_residents_in_contacts)}")

# Missing contact channels per resident
no_mobile = sum(1 for c in contacts.values() if not c['mobile'].strip())
no_landline = sum(1 for c in contacts.values() if not c['landline'].strip())
no_email = sum(1 for c in contacts.values() if not c['email'].strip())
no_any_contact = sum(1 for c in contacts.values() if not c['mobile'].strip() and not c['landline'].strip() and not c['email'].strip())

print(f"Residents with no mobile: {no_mobile}")
print(f"Residents with no landline: {no_landline}")
print(f"Residents with no email: {no_email}")
print(f"Residents with NO contact details at all: {no_any_contact}")

# Opt-outs
all_opted_out = sum(1 for c in contacts.values() if c['sms_optout'] == 'Y' and c['voice_optout'] == 'Y' and c['email_optout'] == 'Y')
sms_optout = sum(1 for c in contacts.values() if c['sms_optout'] == 'Y')
voice_optout = sum(1 for c in contacts.values() if c['voice_optout'] == 'Y')
email_optout = sum(1 for c in contacts.values() if c['email_optout'] == 'Y')

print(f"SMS Opt-outs: {sms_optout}")
print(f"Voice Opt-outs: {voice_optout}")
print(f"Email Opt-outs: {email_optout}")
print(f"All 3 Opted out: {all_opted_out}")

# Languages
languages = Counter(c['language'].strip() for c in contacts.values())
print(f"Languages: {dict(languages)}")

# Shared contact info (deduplication check)
mobiles = defaultdict(list)
landlines = defaultdict(list)
emails = defaultdict(list)

for c in contacts.values():
    m = c['mobile'].strip()
    l = c['landline'].strip()
    e = c['email'].strip().lower()
    if m: mobiles[m].append(c['resident_id'])
    if l: landlines[l].append(c['resident_id'])
    if e: emails[e].append(c['resident_id'])

shared_mobiles = {m: r for m, r in mobiles.items() if len(r) > 1}
shared_landlines = {l: r for l, r in landlines.items() if len(r) > 1}
shared_emails = {e: r for e, r in emails.items() if len(r) > 1}

print(f"Shared mobiles count: {len(shared_mobiles)}")
print(f"Shared landlines count: {len(shared_landlines)}")
print(f"Shared emails count: {len(shared_emails)}")
if shared_mobiles:
    print(f"Sample shared mobile: {list(shared_mobiles.items())[:3]}")
if shared_landlines:
    print(f"Sample shared landline: {list(shared_landlines.items())[:3]}")
if shared_emails:
    print(f"Sample shared email: {list(shared_emails.items())[:3]}")

# Landline numbers placed in 'mobile' field? Or landline block 555-2xx?
# Let's check how many numbers in mobile field are 555-2xx
mobile_in_landline_block = sum(1 for c in contacts.values() if c['mobile'].strip() and 200 <= int(c['mobile'].strip().split('-')[1]) <= 249)
landline_in_mobile_block = sum(1 for c in contacts.values() if c['landline'].strip() and not (200 <= int(c['landline'].strip().split('-')[1]) <= 249))

print(f"Mobile field containing landline block (555-2xx): {mobile_in_landline_block}")
print(f"Landline field NOT in landline block: {landline_in_mobile_block}")

# Stale contacts analysis (number_last_verified)
verified_dates = [c['number_last_verified'].strip() for c in contacts.values() if c['number_last_verified'].strip()]
min_verified = min(verified_dates)
max_verified = max(verified_dates)
print(f"Verification date range: {min_verified} to {max_verified}")

# Appointment timing
app_times = [datetime.strptime(a['scheduled_at'], "%Y-%m-%d %H:%M") for a in appointments]
min_app_time = min(app_times)
max_app_time = max(app_times)
print(f"Appointment datetime range: {min_app_time} to {max_app_time}")

# Hours of appointments
app_hours = Counter(t.hour for t in app_times)
print(f"Appointment hours distribution: {sorted(app_hours.items())}")

# Multiple appointments per resident
resident_app_count = Counter(a['resident_id'] for a in appointments)
multi_app_residents = {r: cnt for r, cnt in resident_app_count.items() if cnt > 1}
print(f"Residents with multiple appointments: {len(multi_app_residents)}")
print(f"Max appointments for a single resident: {max(resident_app_count.values())}")

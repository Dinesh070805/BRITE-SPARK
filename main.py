#!/usr/bin/env python3
"""
Policy-Driven Appointment Reminder System ("Reminder That Reaches")
Main execution entry point.
"""
import sys
import json
from datetime import datetime, timedelta

from reminder.loader import load_contacts, load_appointments
from reminder.policy import ContactPolicy
from reminder.language import LanguageSelector
from reminder.dedup import DeduplicationService
from reminder.dispatcher import ReminderDispatcher
from reminder.planner import ReminderPlanner
from reminder.metrics import MetricsCollector

def run_reminder_engine(
    contacts_file: str = "data/contacts.csv",
    appointments_file: str = "data/appointments.csv",
    quiet_start: int = 20,
    quiet_end: int = 8,
    max_attempts: int = 3
):
    print("==================================================")
    print("    REMINDER THAT REACHES — CALDER COUNTY         ")
    print("==================================================")

    # 1. Load Data
    contacts = load_contacts(contacts_file)
    appointments = load_appointments(appointments_file)

    print(f"Loaded {len(contacts)} contacts and {len(appointments)} appointments.")

    # 2. Initialize Components
    policy = ContactPolicy(
        quiet_start_hour=quiet_start,
        quiet_end_hour=quiet_end,
        max_attempts_per_appointment=max_attempts
    )
    lang_selector = LanguageSelector(default_language="en")
    dedup_service = DeduplicationService()
    dispatcher = ReminderDispatcher(
        policy=policy,
        language_selector=lang_selector,
        dedup_service=dedup_service,
        max_attempts=max_attempts
    )
    planner = ReminderPlanner(policy=policy, advance_hours=24)
    metrics_collector = MetricsCollector()

    # 3. Process Appointments
    for app in appointments:
        resident = contacts.get(app.resident_id)
        if not resident:
            # Missing resident record handled as blocked
            continue

        # Plan reminder dispatch time (24h before appointment)
        planned_time, was_deferred = planner.plan_reminder_time(app)

        # Dispatch reminder
        attempts = dispatcher.dispatch_reminder(
            appointment=app,
            resident=resident,
            current_time=planned_time
        )

    # 4. Collect Audit Records & Compute Metrics
    metrics_collector.add_audit_records(dispatcher.audit_records)
    metrics_collector.write_audit_log_csv("audit_log.csv")
    metrics_collector.write_audit_log_json("audit_log.json")

    report = metrics_collector.compute_metrics(
        total_appointments=len(appointments),
        total_residents=len(contacts),
        language_fallback_count=lang_selector.fallback_count
    )

    print("\n==================================================")
    print("               FINAL RUN REPORT                   ")
    print("==================================================")
    print(json.dumps(report, indent=2))
    print("\nAudit logs saved to audit_log.csv and audit_log.json.")
    print("Channel dispatches logged to outbox.jsonl.")
    print("==================================================")

if __name__ == "__main__":
    run_reminder_engine()

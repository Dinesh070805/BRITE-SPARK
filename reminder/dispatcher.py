from datetime import datetime
from typing import List, Tuple, Optional
from reminder.models import (
    Resident, Appointment, ReminderAttempt, AuditRecord,
    ChannelType, CommunicationStatus
)
from reminder.policy import ContactPolicy
from reminder.language import LanguageSelector
from reminder.dedup import DeduplicationService
from reminder.adapters import get_channel_adapter

class ReminderDispatcher:
    def __init__(
        self,
        policy: ContactPolicy,
        language_selector: LanguageSelector,
        dedup_service: DeduplicationService,
        max_attempts: int = 3
    ):
        self.policy = policy
        self.language_selector = language_selector
        self.dedup_service = dedup_service
        self.max_attempts = max_attempts
        self.audit_records: List[AuditRecord] = []

    def dispatch_reminder(
        self,
        appointment: Appointment,
        resident: Resident,
        current_time: datetime
    ) -> List[ReminderAttempt]:
        attempts: List[ReminderAttempt] = []
        
        # 1. Check if resident is missing from system or has NO contact info at all
        if not resident.mobile.strip() and not resident.landline.strip() and not resident.email.strip():
            rec = AuditRecord(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel="none",
                contact="none",
                language=resident.language or "unknown",
                timestamp=current_time.isoformat(),
                status="blocked",
                outcome="no_contact_info",
                reason="Resident has no phone or email contact details",
                attempt_number=0,
                fallback_used=False,
                reached=False,
                deferred=False,
                duplicate_prevented=False
            )
            self.audit_records.append(rec)
            return attempts

        # 2. Check all opt-outs
        if resident.sms_optout and resident.voice_optout and resident.email_optout:
            rec = AuditRecord(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel="all",
                contact="none",
                language=resident.language or "en",
                timestamp=current_time.isoformat(),
                status="blocked",
                outcome="all_opted_out",
                reason="Resident has opted out of all communication channels (SMS, Voice, Email)",
                attempt_number=0,
                fallback_used=False,
                reached=False,
                deferred=False,
                duplicate_prevented=False
            )
            self.audit_records.append(rec)
            return attempts

        # 3. Check if too close to appointment
        if self.policy.is_too_close_to_appointment(current_time, appointment.scheduled_at):
            rec = AuditRecord(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel="none",
                contact="none",
                language=resident.language or "en",
                timestamp=current_time.isoformat(),
                status="stopped",
                outcome="too_close_to_appointment",
                reason=f"Current time is within {self.policy.min_lead_minutes} minutes of appointment",
                attempt_number=0,
                fallback_used=False,
                reached=False,
                deferred=False,
                duplicate_prevented=False
            )
            self.audit_records.append(rec)
            return attempts

        # 4. Get eligible channels via ContactPolicy
        eligible_channels = self.policy.get_eligible_channels(resident, current_time)
        if not eligible_channels:
            rec = AuditRecord(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel="none",
                contact="none",
                language=resident.language or "en",
                timestamp=current_time.isoformat(),
                status="blocked",
                outcome="no_eligible_channels",
                reason="No channels passed ContactPolicy eligibility rules",
                attempt_number=0,
                fallback_used=False,
                reached=False,
                deferred=False,
                duplicate_prevented=False
            )
            self.audit_records.append(rec)
            return attempts

        # Render message text in resident's language
        body, used_lang, is_fallback_lang = self.language_selector.render_reminder(resident, appointment)

        attempt_count = 0
        resident_reached = False
        fallback_used = False

        for ch_idx, (channel_type, contact_val, deferred_time, eligibility_reason) in enumerate(eligible_channels):
            if resident_reached or attempt_count >= self.max_attempts:
                break

            if ch_idx > 0:
                fallback_used = True

            # Check quiet hours deferral
            if deferred_time is not None:
                rec = AuditRecord(
                    appointment_id=appointment.appointment_id,
                    resident_id=resident.resident_id,
                    channel=channel_type.value,
                    contact=contact_val,
                    language=used_lang,
                    timestamp=current_time.isoformat(),
                    status="deferred",
                    outcome="quiet_hours_deferred",
                    reason=f"Scheduled during quiet hours. Deferred to {deferred_time.isoformat()}",
                    attempt_number=attempt_count + 1,
                    fallback_used=fallback_used,
                    reached=False,
                    deferred=True,
                    duplicate_prevented=False
                )
                self.audit_records.append(rec)
                # We do not dispatch during quiet hours; deferral handled
                continue

            # Check deduplication
            if self.dedup_service.is_duplicate(contact_val, channel_type, appointment.appointment_id):
                self.dedup_service.duplicate_prevented_count += 1
                rec = AuditRecord(
                    appointment_id=appointment.appointment_id,
                    resident_id=resident.resident_id,
                    channel=channel_type.value,
                    contact=contact_val,
                    language=used_lang,
                    timestamp=current_time.isoformat(),
                    status="blocked",
                    outcome="duplicate_prevented",
                    reason="Duplicate message prevented for this contact point and appointment",
                    attempt_number=attempt_count + 1,
                    fallback_used=fallback_used,
                    reached=False,
                    deferred=False,
                    duplicate_prevented=True
                )
                self.audit_records.append(rec)
                continue

            # Execute channel dispatch
            attempt_count += 1
            adapter = get_channel_adapter(channel_type)
            result = adapter.send(contact_val, body, current_time, attempt=1)
            
            # Record dispatch for deduplication
            self.dedup_service.record_dispatch(contact_val, channel_type, appointment.appointment_id)

            status_str = result.get('status', 'failed')
            detail_str = result.get('detail', '')

            # Interpret outcome: reach vs delivery
            is_reached = False
            comm_status = CommunicationStatus.FAILED

            if channel_type == ChannelType.SMS:
                if status_str == 'delivered':
                    if detail_str == 'accepted_by_carrier' and self.policy.is_landline_number(contact_val):
                        # Landline accepted by carrier but cannot receive SMS
                        comm_status = CommunicationStatus.FAILED
                        detail_str = 'accepted_by_carrier_landline_unreachable'
                        is_reached = False
                    else:
                        comm_status = CommunicationStatus.DELIVERED
                        is_reached = False # SMS delivery != confirmed human reach
                else:
                    comm_status = CommunicationStatus.FAILED

            elif channel_type == ChannelType.VOICE:
                if status_str == 'answered':
                    if detail_str == 'human':
                        comm_status = CommunicationStatus.REACHED
                        is_reached = True # Human answer = Confirmed Human Reach!
                    else:
                        # Voicemail left
                        comm_status = CommunicationStatus.DELIVERED
                        is_reached = False
                else:
                    comm_status = CommunicationStatus.FAILED

            elif channel_type == ChannelType.EMAIL:
                if status_str == 'delivered':
                    comm_status = CommunicationStatus.DELIVERED
                    is_reached = False
                else:
                    comm_status = CommunicationStatus.FAILED

            attempt_record = ReminderAttempt(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel=channel_type,
                to_contact=contact_val,
                language=used_lang,
                timestamp=current_time,
                attempt_number=attempt_count,
                status=comm_status,
                detail=detail_str,
                reached=is_reached,
                deferred=False,
                reason=eligibility_reason,
                fallback_used=fallback_used
            )
            attempts.append(attempt_record)

            rec = AuditRecord(
                appointment_id=appointment.appointment_id,
                resident_id=resident.resident_id,
                channel=channel_type.value,
                contact=contact_val,
                language=used_lang,
                timestamp=current_time.isoformat(),
                status=comm_status.value,
                outcome=detail_str if detail_str else status_str,
                reason=eligibility_reason,
                attempt_number=attempt_count,
                fallback_used=fallback_used,
                reached=is_reached,
                deferred=False,
                duplicate_prevented=False
            )
            self.audit_records.append(rec)

            if is_reached:
                resident_reached = True
                break

        return attempts

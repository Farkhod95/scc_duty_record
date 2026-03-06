from django.utils import timezone

from monitoring.models import Event, EventAssignment, DutyDayStatus, RejectedAtStage


def validate_event_transport_capacity(event, transport, exclude_pk=None):
    """
    Tadbir ichida transport sig'imini tekshiradi.
    Raises ValueError agar limit oshsa.
    """
    if transport is None:
        return

    qs = EventAssignment.objects.filter(event=event, transport=transport)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    current_count = qs.count()
    if current_count >= transport.capacity:
        raise ValueError(
            f"Transport to'ldi. Sig'im: {transport.capacity}, "
            f"hozir biriktirilgan: {current_count}."
        )


def submit_event(event, submitted_by):
    """OFFICER tadbirni tasdiqlashga yuboradi."""
    if event.status != DutyDayStatus.DRAFT:
        raise ValueError("Faqat DRAFT holatidagi tadbirni yuborish mumkin.")
    if not event.assignments.exists():
        raise ValueError("Tadbirga kamida 1 ta xodim biriktirilishi kerak.")

    event.status = DutyDayStatus.SUBMITTED
    event.submitted_by = submitted_by
    event.submitted_at = timezone.now()
    event.updated_by = submitted_by
    event.save(update_fields=['status', 'submitted_by', 'submitted_at', 'updated_by'])


def collect_event(event, collected_by):
    """COLLECTOR birinchi tasdiqlash."""
    if event.status != DutyDayStatus.SUBMITTED:
        raise ValueError("Faqat SUBMITTED holatidagi tadbirni tasdiqlash mumkin.")

    event.status = DutyDayStatus.COLLECTED
    event.collected_by = collected_by
    event.collected_at = timezone.now()
    event.updated_by = collected_by
    event.save(update_fields=['status', 'collected_by', 'collected_at', 'updated_by'])


def approve_event(event, approved_by):
    """DISTRICT_ADMIN yakuniy tasdiqlash."""
    if event.status != DutyDayStatus.COLLECTED:
        raise ValueError("Faqat COLLECTED holatidagi tadbirni tasdiqlash mumkin.")

    event.status = DutyDayStatus.APPROVED
    event.approved_by = approved_by
    event.approved_at = timezone.now()
    event.updated_by = approved_by
    event.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_by'])


def reject_event(event, rejected_by, reason, stage):
    """COLLECTOR yoki DISTRICT_ADMIN rad etadi."""
    allowed = [DutyDayStatus.SUBMITTED, DutyDayStatus.COLLECTED]
    if event.status not in allowed:
        raise ValueError("Faqat SUBMITTED yoki COLLECTED holatidagi tadbirni rad etish mumkin.")

    event.status = DutyDayStatus.REJECTED
    event.rejected_by = rejected_by
    event.rejected_at = timezone.now()
    event.rejection_reason = reason
    event.rejected_at_stage = stage
    event.updated_by = rejected_by
    event.save(update_fields=[
        'status', 'rejected_by', 'rejected_at',
        'rejection_reason', 'rejected_at_stage', 'updated_by',
    ])

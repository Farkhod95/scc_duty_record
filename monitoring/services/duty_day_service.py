import datetime

from django.utils import timezone

from directory.models import OrgStageDefinition
from monitoring.models import (
    DutyDay, DutySection, DutySectionAssignment,
    DutyDayStatus, RejectedAtStage,
)


def create_duty_day_with_sections(organization, duty_date, created_by):
    """
    DutyDay yaratadi va org.stages_count ga qarab DutySection-larni
    avtomatik ochadi. OrgStageDefinition mavjud bo'lsa — vaqt va nom undan olinadi.
    """
    duty_day = DutyDay.objects.create(
        organization=organization,
        duty_date=duty_date,
        created_by=created_by,
    )

    stage_definitions = {
        sd.stage_number: sd
        for sd in OrgStageDefinition.objects.filter(organization=organization)
    }

    for stage_num in range(1, organization.stages_count + 1):
        sd = stage_definitions.get(stage_num)
        if sd:
            name = sd.name
            start_dt = timezone.make_aware(
                datetime.datetime.combine(duty_date, sd.default_start_time)
            )
            end_dt = timezone.make_aware(
                datetime.datetime.combine(duty_date, sd.default_end_time)
            )
            # Tungi navbat: tugash vaqti boshlanishdan kichik bo'lsa — keyingi kun
            if end_dt <= start_dt:
                end_dt += datetime.timedelta(days=1)
        else:
            name = f"{stage_num}-bosqich"
            start_dt = None
            end_dt = None

        DutySection.objects.create(
            duty_day=duty_day,
            stage_number=stage_num,
            name=name,
            start_time=start_dt,
            end_time=end_dt,
            created_by=created_by,
        )

    return duty_day



def submit_duty_day(duty_day, submitted_by):
    """OFFICER navbatchilikni tasdiqlashga yuboradi."""
    if duty_day.status != DutyDayStatus.DRAFT:
        raise ValueError("Faqat DRAFT holatidagi navbatchilikni yuborish mumkin.")

    from django.db.models import Count
    for section in duty_day.sections.all():
        has_employees = section.assignments.annotate(
            emp_count=Count('employees')
        ).filter(emp_count__gt=0).exists()
        if not has_employees:
            raise ValueError(
                f"'{section.name}' seksiyasida kamida 1 ta navbatchi bo'lishi kerak."
            )

    duty_day.status = DutyDayStatus.SUBMITTED
    duty_day.submitted_by = submitted_by
    duty_day.submitted_at = timezone.now()
    duty_day.updated_by = submitted_by
    duty_day.save(update_fields=['status', 'submitted_by', 'submitted_at', 'updated_by'])


def collect_duty_day(duty_day, collected_by):
    """COLLECTOR birinchi tasdiqlash."""
    if duty_day.status != DutyDayStatus.SUBMITTED:
        raise ValueError("Faqat SUBMITTED holatidagi navbatchilikni tasdiqlash mumkin.")

    duty_day.status = DutyDayStatus.COLLECTED
    duty_day.collected_by = collected_by
    duty_day.collected_at = timezone.now()
    duty_day.updated_by = collected_by
    duty_day.save(update_fields=['status', 'collected_by', 'collected_at', 'updated_by'])


def approve_duty_day(duty_day, approved_by):
    """DISTRICT_ADMIN yakuniy tasdiqlash."""
    if duty_day.status != DutyDayStatus.COLLECTED:
        raise ValueError("Faqat COLLECTED holatidagi navbatchilikni tasdiqlash mumkin.")

    duty_day.status = DutyDayStatus.APPROVED
    duty_day.approved_by = approved_by
    duty_day.approved_at = timezone.now()
    duty_day.updated_by = approved_by
    duty_day.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_by'])

    # Har bir section uchun gRPC AlarmStream tinglash taskini ishga tushirish
    from monitoring.tasks import listen_alarm_stream
    for section in duty_day.sections.all():
        listen_alarm_stream.delay(section.id)


def reject_duty_day(duty_day, rejected_by, reason, stage):
    """
    COLLECTOR yoki DISTRICT_ADMIN rad etadi.
    stage: RejectedAtStage.COLLECTOR yoki RejectedAtStage.DISTRICT_ADMIN
    """
    allowed = [DutyDayStatus.SUBMITTED, DutyDayStatus.COLLECTED]
    if duty_day.status not in allowed:
        raise ValueError("Faqat SUBMITTED yoki COLLECTED holatidagi navbatchilikni rad etish mumkin.")

    duty_day.status = DutyDayStatus.REJECTED
    duty_day.rejected_by = rejected_by
    duty_day.rejected_at = timezone.now()
    duty_day.rejection_reason = reason
    duty_day.rejected_at_stage = stage
    duty_day.updated_by = rejected_by
    duty_day.save(update_fields=[
        'status', 'rejected_by', 'rejected_at',
        'rejection_reason', 'rejected_at_stage', 'updated_by',
    ])

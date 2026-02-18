from django.utils import timezone
from rest_framework.exceptions import ValidationError

from monitoring.models import MainDutyStatus, RoleInTransport


def send_for_approval(main_duty, user):
    """DRAFT -> SENT_FOR_APPROVAL with validation."""
    if main_duty.status != MainDutyStatus.DRAFT:
        raise ValidationError({'status': "Faqat DRAFT holatdagi navbatchilikni tasdiqlashga yuborish mumkin."})

    tasks = main_duty.tasks.all()
    if not tasks.exists():
        raise ValidationError("Kamida bitta vazifa bo'lishi kerak.")

    for task in tasks:
        assignments = task.assignments.all()
        if not assignments.exists():
            raise ValidationError(f"'{task.title}' vazifasida kamida bitta tayinlash bo'lishi kerak.")

        # Check: if transport is CAR, at least one DRIVER must exist
        car_transports = set()
        driver_transports = set()
        for assignment in assignments:
            if assignment.transport and assignment.transport.transport_type == 'CAR':
                car_transports.add(assignment.transport_id)
                if assignment.role_in_transport == RoleInTransport.DRIVER:
                    driver_transports.add(assignment.transport_id)

        missing_drivers = car_transports - driver_transports
        if missing_drivers:
            raise ValidationError(f"'{task.title}' vazifasida avtomobil transportiga haydovchi tayinlanmagan.")

    main_duty.status = MainDutyStatus.SENT_FOR_APPROVAL
    main_duty.save(update_fields=['status', 'updated_time'])


def approve_main_duty(main_duty, approved_by):
    """SENT_FOR_APPROVAL -> APPROVED."""
    if main_duty.status != MainDutyStatus.SENT_FOR_APPROVAL:
        raise ValidationError("Faqat tasdiqlashga yuborilgan navbatchilikni tasdiqlash mumkin.")

    main_duty.status = MainDutyStatus.APPROVED
    main_duty.approved_by = approved_by
    main_duty.approved_at = timezone.now()
    main_duty.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_time'])

    # Generate PDF report
    from monitoring.services.pdf_service import generate_main_duty_pdf
    generate_main_duty_pdf(main_duty)


def reject_main_duty(main_duty, rejected_by, reason):
    """SENT_FOR_APPROVAL -> REJECTED."""
    if main_duty.status != MainDutyStatus.SENT_FOR_APPROVAL:
        raise ValidationError("Faqat tasdiqlashga yuborilgan navbatchilikni rad etish mumkin.")

    if not reason:
        raise ValidationError({'rejection_reason': "Rad etish sababi kiritilishi shart."})

    main_duty.status = MainDutyStatus.REJECTED
    main_duty.rejection_reason = reason
    main_duty.save(update_fields=['status', 'rejection_reason', 'updated_time'])

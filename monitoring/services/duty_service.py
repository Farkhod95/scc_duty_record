from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied

from monitoring.models import Duty, DutyUser, DutyStatus, DutyUserStatus


@transaction.atomic
def create_duty(data, created_by):
    duty = Duty.objects.create(
        organization=data.get('organization'),
        location=data.get('location'),
        category=data.get('category'),
        name=data.get('name'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        file=data.get('file'),
        status=DutyStatus.PENDING,
        created_by=created_by,
        updated_by=created_by
    )
    return duty


@transaction.atomic
def approve_duty(duty, approved_by):
    if not approved_by.is_superuser:
        raise PermissionDenied({
            'detail': _("Faqat superadmin duty ni tasdiqlashi mumkin")
        })

    if duty.status != DutyStatus.PENDING:
        raise ValidationError({
            'detail': _("Faqat pending statusdagi duty ni tasdiqlash mumkin")
        })

    if not duty.duty_users.exists():
        raise ValidationError({
            'detail': _("Duty ga kamida bitta user biriktirilgan bo'lishi kerak")
        })

    if duty.duty_users.filter(transport__isnull=False).exists():
        if not duty.duty_users.filter(is_driver=True).exists():
            raise ValidationError({
                'detail': _("Transport bo'lsa, kamida bitta haydovchi bo'lishi kerak")
            })

    duty.status = DutyStatus.APPROVED
    duty.approved_by = approved_by
    duty.approved_at = timezone.now()
    duty.updated_by = approved_by
    duty.save()

    return duty


@transaction.atomic
def reject_duty(duty, rejected_by, reason):
    if not rejected_by.is_superuser:
        raise PermissionDenied({
            'detail': _("Faqat superadmin duty ni rad etishi mumkin")
        })

    if duty.status != DutyStatus.PENDING:
        raise ValidationError({
            'detail': _("Faqat pending statusdagi duty ni rad etish mumkin")
        })

    duty.status = DutyStatus.REJECTED
    duty.rejection_reason = reason
    duty.updated_by = rejected_by
    duty.save()

    return duty


@transaction.atomic
def activate_duty(duty, activated_by):

    if duty.status != DutyStatus.APPROVED:
        raise ValidationError({
            'detail': _("Faqat approved statusdagi duty ni faollashtirish mumkin")
        })

    now = timezone.now()
    if now < duty.start_time:
        raise ValidationError({
            'detail': _("Duty hali boshlanmagan")
        })

    if now > duty.end_time:
        raise ValidationError({
            'detail': _("Duty muddati tugagan")
        })

    duty.status = DutyStatus.ACTIVE
    duty.updated_by = activated_by
    duty.save()

    return duty


@transaction.atomic
def complete_duty(duty, completed_by):
    if not (completed_by.is_superuser or duty.approved_by == completed_by):
        raise PermissionDenied({
            'detail': _("Faqat superadmin yoki duty ni tasdiqlagan user yakunlashi mumkin")
        })

    if duty.status != DutyStatus.ACTIVE:
        raise ValidationError({
            'detail': _("Faqat active statusdagi duty ni yakunlash mumkin")
        })

    duty.status = DutyStatus.COMPLETED
    duty.updated_by = completed_by
    duty.save()

    duty.duty_users.update(
        current_status=DutyUserStatus.OFFLINE,
        updated_by=completed_by
    )
    return duty


@transaction.atomic
def cancel_duty(duty, cancelled_by, reason):
    if not cancelled_by.is_superuser:
        raise PermissionDenied({
            'detail': _("Faqat superadmin duty ni bekor qilishi mumkin")
        })

    if duty.status in [DutyStatus.COMPLETED, DutyStatus.CANCELLED]:
        raise ValidationError({
            'detail': _("Yakunlangan yoki bekor qilingan duty ni qayta bekor qilib bo'lmaydi")
        })

    duty.status = DutyStatus.CANCELLED
    duty.rejection_reason = reason
    duty.updated_by = cancelled_by
    duty.save()

    duty.duty_users.update(
        current_status=DutyUserStatus.OFFLINE,
        updated_by=cancelled_by
    )
    return duty


def can_edit_duty(duty, user):
    if duty.status not in [DutyStatus.PENDING, DutyStatus.APPROVED]:
        return False

    if user.is_superuser:
        return True

    if duty.created_by == user and duty.status == DutyStatus.PENDING:
        return True

    return False


def get_duty_statistics(duty):
    total_users = duty.duty_users.count()
    checked_in_users = duty.duty_users.filter(check_in_time__isnull=False).count()
    checked_out_users = duty.duty_users.filter(check_out_time__isnull=False).count()
    on_duty_users = duty.duty_users.filter(current_status=DutyUserStatus.ON_DUTY).count()

    return {
        'total_users': total_users,
        'checked_in_users': checked_in_users,
        'checked_out_users': checked_out_users,
        'on_duty_users': on_duty_users,
        'completion_rate': (checked_in_users / total_users * 100) if total_users > 0 else 0
    }
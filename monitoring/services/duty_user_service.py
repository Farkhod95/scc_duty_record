from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from monitoring.models import Duty, DutyUser, DutyStatus, DutyUserStatus
from fleet.models import Transport

User = get_user_model()


@transaction.atomic
def add_user_to_duty(duty, user_id, transport_id=None, is_driver=False, created_by=None):
    if duty.status not in [DutyStatus.PENDING, DutyStatus.APPROVED]:
        raise ValidationError({
            'detail': _("Faqat pending yoki approved statusdagi duty ga user qo'shish mumkin")
        })

    if duty.duty_users.filter(user_id=user_id).exists():
        raise ValidationError({
            'detail': _("Bu user allaqachon duty ga qo'shilgan")
        })

    # User organizatsiyasi tekshiruvi
    try:
        user = User.objects.get(id=user_id)
        if user.organization and user.organization != duty.organization:
            raise ValidationError({
                'detail': _("User boshqa organizatsiyaga tegishli")
            })
    except User.DoesNotExist:
        raise ValidationError({
            'detail': _("User topilmadi")
        })

    # Transport organizatsiyasi tekshiruvi
    if transport_id:
        try:
            transport = Transport.objects.get(id=transport_id)
            if transport.organization != duty.organization:
                raise ValidationError({
                    'detail': _("Transport boshqa organizatsiyaga tegishli")
                })
        except Transport.DoesNotExist:
            raise ValidationError({
                'detail': _("Transport topilmadi")
            })

    duty_user = DutyUser.objects.create(
        duty=duty,
        user_id=user_id,
        transport_id=transport_id,
        is_driver=is_driver,
        current_status=DutyUserStatus.OFFLINE,
        created_by=created_by,
        updated_by=created_by
    )

    duty.updated_by = created_by
    duty.save()

    return duty_user


@transaction.atomic
def update_duty_user(duty_user, transport_id=None, is_driver=None, updated_by=None):
    if duty_user.duty.status not in [DutyStatus.PENDING, DutyStatus.APPROVED]:
        raise ValidationError({
            'detail': _("Faqat pending yoki approved statusdagi duty userni yangilash mumkin")
        })

    # Transport organizatsiyasi tekshiruvi
    if transport_id is not None:
        if transport_id:
            try:
                transport = Transport.objects.get(id=transport_id)
                if transport.organization != duty_user.duty.organization:
                    raise ValidationError({
                        'detail': _("Transport boshqa organizatsiyaga tegishli")
                    })
            except Transport.DoesNotExist:
                raise ValidationError({
                    'detail': _("Transport topilmadi")
                })
        duty_user.transport_id = transport_id

    if is_driver is not None:
        duty_user.is_driver = is_driver

    duty_user.updated_by = updated_by
    duty_user.save()

    return duty_user


@transaction.atomic
def remove_user_from_duty(duty, user_id, removed_by=None):
    if duty.status not in [DutyStatus.PENDING, DutyStatus.APPROVED]:
        raise ValidationError({
            'detail': _("Faqat pending yoki approved statusdagi duty dan user o'chirish mumkin")
        })

    duty_user = duty.duty_users.filter(user_id=user_id).first()

    if not duty_user:
        raise ValidationError({
            'detail': _("Bu user duty da mavjud emas")
        })

    duty_user.delete()

    duty.updated_by = removed_by
    duty.save()

    return True
import logging

from django.db import IntegrityError, OperationalError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotAuthenticated, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _extract_error_message(detail):
    """Flatten DRF ValidationError detail to a single string."""
    if isinstance(detail, dict):
        first_value = next(iter(detail.values()))
        return _extract_error_message(first_value)
    if isinstance(detail, list):
        return _extract_error_message(detail[0])
    return str(detail)


def _integrity_error_message(exc):
    """IntegrityError dan foydalanuvchiga tushunarli xabar yasaydi."""
    msg = str(exc).lower()
    if 'unique' in msg or 'duplicate' in msg:
        return "Bu ma'lumot allaqachon mavjud (takroriy qiymat)."
    if 'not null' in msg or 'null value' in msg:
        return "Majburiy maydon bo'sh qoldirilgan."
    if 'foreign key' in msg or 'violates foreign key' in msg:
        return "Bog'liq yozuv topilmadi yoki o'chirib bo'lmaydi."
    return "Ma'lumotlar bazasi cheklovi buzildi."


def custom_exception_handler(exc, context):
    # DB xatolari DRF handler ga tushmasdan keladi — avval tekshiramiz
    if isinstance(exc, IntegrityError):
        logger.warning("IntegrityError: %s", exc)
        return Response(
            {'detail': _integrity_error_message(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, OperationalError):
        logger.error("OperationalError: %s", exc)
        return Response(
            {'detail': "Ma'lumotlar bazasida xatolik yuz berdi."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = exception_handler(exc, context)

    if response is None:
        # DRF ham, yuqoridagi ham tutmagan xatolik
        logger.exception("Unhandled exception in API: %s", exc)
        return Response(
            {'detail': "Kutilmagan xatolik yuz berdi."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, Http404):
        response.data = {'detail': 'Topilmadi.'}

    elif isinstance(exc, ValidationError):
        response.data = {'detail': _extract_error_message(exc.detail)}

    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        response.data = {'detail': 'Autentifikatsiya talab etiladi.'}

    return response

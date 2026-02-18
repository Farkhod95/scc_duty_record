from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotAuthenticated, AuthenticationFailed
from rest_framework.views import exception_handler


def _extract_error_message(detail):
    """Flatten DRF ValidationError detail to a single string."""
    if isinstance(detail, dict):
        first_value = next(iter(detail.values()))
        return _extract_error_message(first_value)
    if isinstance(detail, list):
        return _extract_error_message(detail[0])
    return str(detail)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Http404):
        response.data = {'error': 'Not Found'}

    elif isinstance(exc, ValidationError):
        response.data = {'error': _extract_error_message(exc.detail)}

    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        response.data = {'error': 'Wrong Email or Password'}

    return response

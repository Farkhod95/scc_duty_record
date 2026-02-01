# restapp/current_user.py

import threading
from typing import Optional
from django.contrib.auth import get_user_model

_user_storage = threading.local()
User = get_user_model()


def set_current_user(user: Optional[User]):
    """
    Middleware ichidan chaqiriladi.
    """
    _user_storage.user = user


def get_current_user() -> Optional[User]:
    """
    Signals ichida joriy foydalanuvchini olish uchun.
    """
    return getattr(_user_storage, "user", None)

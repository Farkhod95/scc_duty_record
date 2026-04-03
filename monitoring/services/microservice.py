"""
Monitoring mikroservisga event yuborish — gRPC orqali.

Barcha funksiyalar:
  - gRPC sozlanmagan bo'lsa — log qilib o'tkazadi
  - Xatolik bo'lsa — log qilib, asosiy jarayonni to'xtatmaydi
"""
import logging

logger = logging.getLogger(__name__)


def send_location_sync(location) -> None:
    """
    Location yaratilganda yoki yangilanganda chaqiriladi.
    PaligonCreate gRPC RPC si orqali mikroservicga yuboriladi.
    """
    from monitoring.services.grpc_client import grpc_location
    try:
        grpc_location.paligon_create(location)
    except Exception as exc:
        logger.warning("send_location_sync xato: %s", exc)


def send_point_sync(point) -> None:
    """
    LocationPoint yaratilganda yoki yangilanganda chaqiriladi.
    PointCreate gRPC RPC si orqali mikroservicga yuboriladi.
    """
    from monitoring.services.grpc_client import grpc_location
    try:
        grpc_location.point_create(point)
    except Exception as exc:
        logger.warning("send_point_sync xato: %s", exc)


def send_section_started(section) -> None:
    """
    DutySection boshlanganda chaqiriladi.
    DutyCreate gRPC RPC si orqali mikroservicga yuboriladi.
    """
    from monitoring.services.grpc_client import grpc_location
    try:
        grpc_location.duty_create(section)
    except Exception as exc:
        logger.warning("send_section_started xato: %s", exc)


def send_section_ended(section) -> None:
    """
    DutySection tugaganda chaqiriladi.
    DutyStop gRPC RPC si orqali mikroservicga yuboriladi.
    """
    from monitoring.services.grpc_client import grpc_location
    try:
        grpc_location.duty_stop(section)
    except Exception as exc:
        logger.warning("send_section_ended xato: %s", exc)

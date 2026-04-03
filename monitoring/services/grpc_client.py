"""
LocationService gRPC client.

Barcha gRPC chaqiruvlari shu moduldan o'tadi.
Ulanish singleton — dastur ishga tushganda bir marta yaratiladi.

Ishlatish:
    from monitoring.services.grpc_client import grpc_location
    grpc_location.send_location(pinfl_hash, lat, lng, accuracy, timestamp)
"""
import logging
import sys
import os

from django.conf import settings

logger = logging.getLogger(__name__)

# Proto stublari /app/proto/ ichida (Dockerfile da generate qilinadi)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'proto'))

try:
    import grpc
    import location_service_pb2 as pb2
    import location_service_pb2_grpc as pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("grpc yoki proto stublari topilmadi. Proto kompilatsiya qilindimi?")


TIMEOUT = 5  # sekund


class LocationServiceClient:
    """
    LocationService gRPC client singleton.
    Ulanish lazy — birinchi chaqiruvda ochiladi.
    """

    def __init__(self):
        self._channel = None
        self._stub = None

    def _get_stub(self):
        if not GRPC_AVAILABLE:
            return None
        if self._stub is None:
            addr = getattr(settings, 'GRPC_LOCATION_SERVICE_ADDR', '')
            if not addr:
                logger.debug("GRPC_LOCATION_SERVICE_ADDR sozlanmagan.")
                return None
            self._channel = grpc.insecure_channel(addr)
            self._stub = pb2_grpc.LocationServiceStub(self._channel)
        return self._stub

    def _call(self, method_name, request):
        """Stub metodini chaqiradi, xatolikni log qilib o'tkazadi."""
        stub = self._get_stub()
        if stub is None:
            return None
        try:
            method = getattr(stub, method_name)
            return method(request, timeout=TIMEOUT)
        except Exception as exc:
            logger.warning("gRPC %s xato: %s", method_name, exc)
            return None

    # ── Paligon (bizda: Location) ────────────────────────────────

    def paligon_create(self, location):
        """
        Location modelini mikroservicga yuboradi (yaratish yoki yangilash).
        boundary_data: [{"lat": ..., "lon": ...}, ...] yoki GeoJSON coordinates
        """
        boundary = _parse_boundary(location.boundary_data)
        return self._call('PaligonCreate', pb2.PaligonRequest(
            id=location.id,
            region_id=location.region_id or 0,
            district_id=location.district_id or 0,
            org_id=location.organization_id or 0,
            boundary_data=boundary,
        ))

    def paligon_delete(self, location_id: int):
        return self._call('PaligonDelete', pb2.PaligonDeleteRequest(id=location_id))

    # ── Point (bizda: LocationPoint) ─────────────────────────────

    def point_create(self, point):
        """
        LocationPoint modelini mikroservicga yuboradi.
        radius default 500 metr (LocationPoint modelida radius maydoni yo'q).
        """
        return self._call('PointCreate', pb2.PointRequest(
            id=point.id,
            paligon_id=point.location_id,
            order=point.order,
            radius=getattr(point, 'radius', 500),
            latitude=float(point.latitude) if point.latitude else 0.0,
            longitude=float(point.longitude) if point.longitude else 0.0,
            start_time=str(point.start_time),
            end_time=str(point.end_time),
        ))

    def point_delete(self, point_id: int):
        return self._call('PointDelete', pb2.PointDeleteRequest(id=point_id))

    # ── Duty (bizda: DutySection) ────────────────────────────────

    def duty_create(self, section):
        """
        DutySection boshlanganida DutyCreate chaqiriladi.
        Assignment larda: paligon_id = location_id, employees = pinfl_hash lar, vehicles = plate_number lar.
        """
        from django.utils import timezone
        local_tz = timezone.get_current_timezone()
        org = section.duty_day.organization

        started_at = (
            section.start_time.astimezone(local_tz).isoformat()
            if section.start_time
            else timezone.now().astimezone(local_tz).isoformat()
        )

        assignments_qs = section.assignments.select_related('location').prefetch_related(
            'employees', 'transports'
        )
        assignments = []
        for asgn in assignments_qs:
            employees = [
                emp.pinfl_hash
                for emp in asgn.employees.all()
                if emp.pinfl_hash
            ]
            vehicles = [
                tr.plate_number
                for tr in asgn.transports.all()
                if tr.plate_number
            ]
            if not employees and not vehicles:
                continue
            assignments.append(pb2.Assignment(
                paligon_id=asgn.location_id or 0,
                employees=employees,
                vehicles=vehicles,
            ))

        return self._call('DutyCreate', pb2.DutyRequest(
            section_id=section.id,
            started_at=started_at,
            org_id=org.id,
            region_id=org.region_id or 0,
            district_id=org.district_id or 0,
            assignments=assignments,
        ))

    def duty_stop(self, section):
        """DutySection tugaganida DutyStop chaqiriladi."""
        from django.utils import timezone
        local_tz = timezone.get_current_timezone()
        ended_at = (
            section.end_time.astimezone(local_tz).isoformat()
            if section.end_time
            else timezone.now().astimezone(local_tz).isoformat()
        )
        return self._call('DutyStop', pb2.StopDutyRequest(
            section_id=section.id,
            ended_at=ended_at,
        ))

    def duty_info(self, section_id: int):
        """
        DutyInfo — section dagi barcha xodim va mashinalarning joriy GPS holati.
        Qaytaradi: DutyInfoResponse yoki None
        """
        return self._call('DutyInfo', pb2.DutyInfoRequest(section_id=section_id))

    # ── Lokatsiya (planshetdan GPS) ──────────────────────────────

    def send_location(self, pinfl_hash: str, latitude: float, longitude: float,
                      accuracy: float = None, timestamp: int = None):
        """Planshetdan kelgan GPS ni mikroservicga uzatadi."""
        return self._call('Location', pb2.LocationRequest(
            pinfl_hash=pinfl_hash,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy or 0.0,
            timestamp=timestamp or 0,
        ))


# ── Yordamchi ────────────────────────────────────────────────────

def _parse_boundary(boundary_data):
    """
    boundary_data dan pb2.Coordinate ro'yxatini tuzadi.
    Qo'llab-quvvatlanadigan formatlar:
      - [{"lat": 41.3, "lon": 69.2}, ...]
      - [[69.2, 41.3], ...]   (GeoJSON: [lon, lat])
      - {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}
    """
    if not boundary_data:
        return []

    coords = boundary_data
    # GeoJSON Polygon
    if isinstance(boundary_data, dict):
        coords = boundary_data.get('coordinates', [[]])[0]

    result = []
    for item in coords:
        if isinstance(item, dict):
            lat = item.get('lat') or item.get('latitude')
            lon = item.get('lon') or item.get('longitude')
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            lon, lat = item[0], item[1]
        else:
            continue
        if lat is not None and lon is not None:
            result.append(pb2.Coordinate(latitude=float(lat), longitude=float(lon)))
    return result


# Singleton
grpc_location = LocationServiceClient()

"""
Xarita (Map) uchun API endpointlari.

GET /api/v1/map/filters/   — Rol asosida mavjud filter opsiyalari
GET /api/v1/map/live/      — Jonli xarita: xodimlar va transportlar holati (DutyInfo gRPC)
GET /api/v1/map/history/   — Xodim harakati tarixi (DutyList gRPC)

Rol-asosida ko'rinish:
  SUPER_ADMIN    → hamma viloyat, tuman, tashkilotlar
  DISTRICT_ADMIN → faqat o'z tumani
  COLLECTOR      → faqat o'z tumani
  OFFICER        → faqat o'z tashkiloti
"""
import logging

import urllib.request
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from directory.models import Organization, District, Region
from monitoring.models import DutySection
from users.models import User

logger = logging.getLogger(__name__)


# ── Ichki yordamchilar ───────────────────────────────────────────

def _visible_section_qs(user):
    qs = DutySection.objects.select_related(
        'duty_day__organization__district__region',
    ).prefetch_related(
        'assignments__employees',
        'assignments__transports__type',
        'assignments__location',
    ).filter(
        duty_day__status__in=['SUBMITTED', 'COLLECTED', 'APPROVED'],
    )
    if user.is_super_admin():
        return qs
    if user.is_district_admin() or user.is_collector():
        return qs.filter(duty_day__organization__district_id=user.district_id)
    return qs.filter(duty_day__organization=user.organization)


def _apply_filters(qs, params, user):
    date = params.get('date')
    qs = qs.filter(duty_day__duty_date=date) if date else qs.filter(duty_day__duty_date=timezone.localdate())

    org_id = params.get('organization_id')
    if org_id and not user.is_super_admin() is False:
        # OFFICER uchun ishlamaydi
        if user.is_super_admin() or user.is_district_admin() or user.is_collector():
            qs = qs.filter(duty_day__organization_id=org_id)

    if params.get('district_id') and user.is_super_admin():
        qs = qs.filter(duty_day__organization__district_id=params['district_id'])

    if params.get('region_id') and user.is_super_admin():
        qs = qs.filter(duty_day__organization__district__region_id=params['region_id'])

    if params.get('section_id'):
        qs = qs.filter(pk=params['section_id'])

    return qs


def _build_user_lookup(sections):
    pinfl_hashes = set()
    for section in sections:
        for asgn in section.assignments.all():
            for emp in asgn.employees.all():
                if emp.pinfl_hash:
                    pinfl_hashes.add(emp.pinfl_hash)
    if not pinfl_hashes:
        return {}
    users = User.objects.filter(
        pinfl_hash__in=pinfl_hashes,
    ).select_related('organization__district__region', 'position', 'special_rank')
    return {u.pinfl_hash: u for u in users}


def _employee_info(u):
    org = u.organization
    return {
        'id': u.pk,
        'full_name': ' '.join(p for p in [u.last_name, u.first_name, u.second_name] if p),
        'position': u.position.name if u.position else None,
        'special_rank': u.special_rank.name if u.special_rank else None,
        'organization': {
            'id': org.pk,
            'name': org.name,
            'district': org.district.name if org.district else None,
            'region': org.district.region.name if org.district and org.district.region else None,
        } if org else None,
    }


def _section_info(s):
    return {
        'id': s.pk,
        'stage_number': s.stage_number,
        'name': s.name,
        'start_time': s.start_time,
        'end_time': s.end_time,
        'duty_date': str(s.duty_day.duty_date),
    }


def _transport_info(t):
    return {
        'id': t.pk,
        'model': t.model,
        'plate_number': t.plate_number,
        'number': t.number,
        'type': t.type.name if t.type else None,
    }


# ── 1. MapFiltersView ────────────────────────────────────────────

class MapFiltersView(APIView):
    """GET /api/v1/map/filters/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_super_admin():
            orgs_qs = Organization.objects.select_related('district__region').order_by('name')
            districts_qs = District.objects.select_related('region').order_by('name')
            regions_qs = Region.objects.order_by('name')
        elif user.is_district_admin() or user.is_collector():
            orgs_qs = Organization.objects.filter(
                district_id=user.district_id
            ).select_related('district__region').order_by('name')
            districts_qs = District.objects.filter(pk=user.district_id).select_related('region')
            regions_qs = Region.objects.filter(districts__pk=user.district_id).distinct()
        else:
            orgs_qs = Organization.objects.filter(pk=user.organization_id).select_related('district__region')
            districts_qs = District.objects.none()
            regions_qs = Region.objects.none()

        dates_qs = _visible_section_qs(user).values_list(
            'duty_day__duty_date', flat=True
        ).distinct().order_by('-duty_day__duty_date')[:30]

        return Response({
            'regions': [{'id': r.pk, 'name': r.name} for r in regions_qs],
            'districts': [{'id': d.pk, 'name': d.name, 'region_id': d.region_id} for d in districts_qs],
            'organizations': [
                {'id': o.pk, 'name': o.name, 'district_id': o.district_id,
                 'district': o.district.name if o.district else None}
                for o in orgs_qs
            ],
            'dates': [str(d) for d in dates_qs],
        })


# ── 2. MapLiveView ───────────────────────────────────────────────

class MapLiveView(APIView):
    """
    GET /api/v1/map/live/
    Query params: date, organization_id, district_id, region_id, section_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from monitoring.services.grpc_client import grpc_location

        params = request.query_params
        date = params.get('date', str(timezone.localdate()))

        sections = list(_apply_filters(_visible_section_qs(request.user), params, request.user))
        user_lookup = _build_user_lookup(sections)

        results = []
        seen = set()

        for section in sections:
            # gRPC DutyInfo — shu section dagi joriy GPS holatlar
            duty_info = grpc_location.duty_info(section.pk)
            if duty_info is None:
                # Mikroservicda duty yo'q — ro'yxatdan o'tkazamiz
                grpc_location.duty_create(section)
                duty_info = grpc_location.duty_info(section.pk)

            # pinfl_hash → gRPC EmployeeInfo lug'ati
            emp_gps = {}
            # plate_number → gRPC VehicleInfo lug'ati
            veh_gps = {}
            if duty_info:
                for asgn_info in duty_info.assignments:
                    for ei in asgn_info.employees:
                        emp_gps[ei.pinfl_hash] = ei
                    for vi in asgn_info.vehicles:
                        veh_gps[vi.plate_number] = vi

            for asgn in section.assignments.all():
                transports = [_transport_info(t) for t in asgn.transports.all()]

                for emp in asgn.employees.all():
                    key = (emp.pinfl_hash, section.pk)
                    if key in seen:
                        continue
                    seen.add(key)

                    gps = emp_gps.get(emp.pinfl_hash) if emp.pinfl_hash else None
                    db_user = user_lookup.get(emp.pinfl_hash) if emp.pinfl_hash else None

                    # is_online: oxirgi update 5 daqiqadan kam
                    is_online = False
                    lat = lng = accuracy = updated_at = None
                    if gps and gps.updated_at:
                        import time
                        is_online = (time.time() * 1000 - gps.updated_at) < 5 * 60 * 1000
                        lat = gps.latitude or None
                        lng = gps.longitude or None
                        updated_at = gps.updated_at

                    results.append({
                        'pinfl_hash': emp.pinfl_hash,
                        'is_online': is_online,
                        'latitude': lat,
                        'longitude': lng,
                        'updated_at': updated_at,
                        'in_polygon': gps.in_polygon if gps else None,
                        'at_point': gps.at_point if gps else None,
                        'point_id': gps.point_id if gps and gps.point_id != -1 else None,
                        'employee': _employee_info(db_user) if db_user else {
                            'id': emp.pk,
                            'full_name': str(emp),
                            'position': emp.position.name if emp.position else None,
                            'special_rank': None,
                            'organization': None,
                        },
                        'section': _section_info(section),
                        'transports': transports,
                    })

            # Mashinalar (transport)
            for asgn in section.assignments.all():
                for transport in asgn.transports.all():
                    if not transport.plate_number:
                        continue
                    key = ('veh', transport.plate_number, section.pk)
                    if key in seen:
                        continue
                    seen.add(key)

                    vgps = veh_gps.get(transport.plate_number)
                    is_online = False
                    lat = lng = updated_at = None
                    if vgps and vgps.updated_at:
                        import time
                        is_online = (time.time() * 1000 - vgps.updated_at) < 5 * 60 * 1000
                        lat = vgps.latitude or None
                        lng = vgps.longitude or None
                        updated_at = vgps.updated_at

                    results.append({
                        'type': 'vehicle',
                        'plate_number': transport.plate_number,
                        'is_online': is_online,
                        'latitude': lat,
                        'longitude': lng,
                        'updated_at': updated_at,
                        'in_polygon': vgps.in_polygon if vgps else None,
                        'transport': _transport_info(transport),
                        'section': _section_info(section),
                    })

        online_count = sum(1 for r in results if r.get('is_online'))

        return Response({
            'date': date,
            'total': len(results),
            'online': online_count,
            'results': results,
        })


# ── 3. MapTileProxyView ──────────────────────────────────────────

class MapTileProxyView(APIView):
    """
    GET /api/v1/map/tiles/<z>/<x>/<y>.png
    safecity.uz tile serverini proxy qiladi. Tillar Redis'da 24 soat cache qilinadi.
    """
    permission_classes = []
    authentication_classes = []

    TILE_URL = 'https://tosh.safecity.uz/map/main/{z}/{x}/{y}.png'
    CACHE_TTL = 60 * 60 * 24  # 24 soat

    def get(self, request, z, x, y):
        from django.core.cache import cache

        cache_key = f'tile:{z}:{x}:{y}'
        cached = cache.get(cache_key)
        if cached:
            return HttpResponse(cached, content_type='image/png')

        url = self.TILE_URL.format(z=z, x=x, y=y)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; TileProxy/1.0)',
                'Referer': 'https://tosh.safecity.uz/',
                'Accept': 'image/png,image/*,*/*',
                'Accept-Language': 'uz,ru;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
        except Exception:
            return HttpResponse(status=502)

        cache.set(cache_key, data, self.CACHE_TTL)
        return HttpResponse(data, content_type='image/png')


# ── 4. MapZonesView ─────────────────────────────────────────────

class MapZonesView(APIView):
    """
    GET /api/v1/map/zones/
    Hozir active bo'lgan sectionlarning location chegaralarini (GeoJSON) qaytaradi.
    Query params: date, organization_id, district_id, region_id, section_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        now = timezone.now()

        qs = DutySection.objects.select_related(
            'duty_day__organization__district__region',
        ).prefetch_related(
            'assignments__location__mahallas',
        ).filter(
            duty_day__status__in=['SUBMITTED', 'COLLECTED', 'APPROVED'],
        )

        if not request.user.is_super_admin():
            if request.user.is_district_admin() or request.user.is_collector():
                qs = qs.filter(duty_day__organization__district_id=request.user.district_id)
            else:
                qs = qs.filter(duty_day__organization=request.user.organization)

        date = params.get('date')
        qs = qs.filter(duty_day__duty_date=date) if date else qs.filter(duty_day__duty_date=timezone.localdate())

        if params.get('organization_id'):
            if not request.user.is_super_admin() is False:
                if request.user.is_super_admin() or request.user.is_district_admin() or request.user.is_collector():
                    qs = qs.filter(duty_day__organization_id=params['organization_id'])
        if params.get('district_id') and request.user.is_super_admin():
            qs = qs.filter(duty_day__organization__district_id=params['district_id'])
        if params.get('region_id') and request.user.is_super_admin():
            qs = qs.filter(duty_day__organization__district__region_id=params['region_id'])
        if params.get('section_id'):
            qs = qs.filter(pk=params['section_id'])

        # Faqat hozir active (start_time <= now <= end_time) bo'lgan sectionlar
        active_only = params.get('active_only', 'true').lower() != 'false'
        if active_only:
            qs = qs.filter(start_time__lte=now, end_time__gte=now)

        results = []
        for section in qs:
            org = section.duty_day.organization
            zones = []
            for asgn in section.assignments.all():
                loc = asgn.location
                if loc is None:
                    continue
                zones.append({
                    'assignment_id': asgn.pk,
                    'location': {
                        'id': loc.pk,
                        'title': loc.title,
                        'boundary_data': loc.boundary_data,
                        'mahallas': [
                            {'id': m.pk, 'name': m.name, 'boundary_data': m.boundary_data}
                            for m in loc.mahallas.all()
                        ],
                    },
                })

            results.append({
                'section_id': section.pk,
                'stage_number': section.stage_number,
                'name': section.name,
                'start_time': section.start_time,
                'end_time': section.end_time,
                'organization': {
                    'id': org.pk,
                    'name': org.name,
                    'district': org.district.name if org.district else None,
                },
                'zones': zones,
            })

        return Response({'results': results})


# ── 4. MapHistoryView ────────────────────────────────────────────

class MapHistoryView(APIView):
    """
    GET /api/v1/map/history/
    Query params: date, organization_id, district_id, region_id, section_id, pinfl_hash
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from monitoring.services.grpc_client import grpc_location

        params = request.query_params
        pinfl_hash = params.get('pinfl_hash')
        section_id = params.get('section_id')

        sections = list(_apply_filters(_visible_section_qs(request.user), params, request.user))
        if not sections:
            return Response({'total_points': 0, 'results': []})

        user_lookup = _build_user_lookup(sections)

        # section_id → section
        section_map = {s.pk: s for s in sections}

        # Mikroservicdan DutyList orqali tarix olish
        # Filtrlash uchun birinchi org/district/region dan foydalanamiz
        first_section = sections[0]
        org = first_section.duty_day.organization

        duty_list_req_kwargs = {
            'org_id': org.id,
        }
        if section_id:
            duty_list_req_kwargs['section_id'] = int(section_id)

        # Hozircha DutyList faqat metadata qaytaradi — trek uchun
        # mikroservis history endpointini kutmoqdamiz (proto da yo'q)
        # Shuning uchun DutyInfo orqali joriy holatni qaytaramiz

        results = []
        total_points = 0

        for section in sections:
            duty_info = grpc_location.duty_info(section.pk)
            if not duty_info:
                continue

            for asgn_info in duty_info.assignments:
                for ei in asgn_info.employees:
                    if pinfl_hash and ei.pinfl_hash != pinfl_hash:
                        continue
                    db_user = user_lookup.get(ei.pinfl_hash)
                    if not db_user:
                        continue

                    # Joriy nuqta (tarix proto da yo'q — faqat joriy holat)
                    track = []
                    if ei.latitude and ei.longitude:
                        track = [{
                            'latitude': ei.latitude,
                            'longitude': ei.longitude,
                            'accuracy': None,
                            'timestamp': ei.updated_at,
                        }]
                        total_points += 1

                    results.append({
                        'employee': {
                            'id': db_user.pk,
                            'full_name': ' '.join(
                                p for p in [db_user.last_name, db_user.first_name, db_user.second_name] if p
                            ),
                            'pinfl_hash': ei.pinfl_hash,
                            'position': db_user.position.name if db_user.position else None,
                            'organization': {
                                'id': db_user.organization.pk,
                                'name': db_user.organization.name,
                            } if db_user.organization else None,
                        },
                        'section': _section_info(section),
                        'track': track,
                    })

        return Response({
            'total_points': total_points,
            'results': results,
        })

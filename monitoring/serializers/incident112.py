from rest_framework import serializers

from monitoring.models import Incident112, Incident112Notification


def _parse_112_date(val):
    """'22.04.2026 17:00:38' → string saqlanadi (CharField uchun)."""
    if not val:
        return None
    return str(val)


def _geo_from_payload(geo):
    """geoInfo: [lat, lon] | {lat, lon} | "lat,lon" | "[lat,lon]" | null."""
    if not geo:
        return None, None
    if isinstance(geo, (list, tuple)) and len(geo) >= 2:
        try:
            return float(geo[0]), float(geo[1])
        except (TypeError, ValueError):
            return None, None
    if isinstance(geo, dict):
        try:
            lat = float(geo.get('lat') or geo.get('latitude') or 0) or None
            lon = float(geo.get('lon') or geo.get('longitude') or 0) or None
            return lat, lon
        except (TypeError, ValueError):
            return None, None
    if isinstance(geo, str):
        import json as _json
        try:
            parsed = _json.loads(geo)
            return _geo_from_payload(parsed)
        except (_json.JSONDecodeError, TypeError):
            pass
        parts = geo.strip('[] ').split(',')
        if len(parts) >= 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except (ValueError, TypeError):
                pass
    return None, None


class Incident112CreateSerializer(serializers.Serializer):
    """
    112 tizimdan kelgan payload ni qabul qiladi.
    Faqat card112Number majburiy — qolgan hamma field ixtiyoriy.
    """
    card112Number = serializers.CharField()

    def to_internal_value(self, data):
        if 'card112Number' not in data or not data['card112Number']:
            raise serializers.ValidationError({'card112Number': 'Bu maydon majburiy.'})
        return data

    def save(self, raw_payload):
        d = self.validated_data

        lat, lon = _geo_from_payload(d.get('geoInfo'))

        # Declarant info — barcha declarant* fieldlar
        declarant_info = {
            k: v for k, v in d.items()
            if k.startswith('declarant')
        } or None

        # Victim info — barcha victim* fieldlar
        victim_info = {
            k: v for k, v in d.items()
            if k.startswith('victim')
        } or None

        # Hospital application — flat fieldlar
        hospital_info = {
            k: v for k, v in d.items()
            if k.startswith('hospitalApplication')
        } or None

        # Traffic collision — flat fieldlar
        traffic_info = {
            k: v for k, v in d.items()
            if k.startswith('trafficCollision')
        } or None

        # called_phone: strCdPn yoki strCdPN
        called_phone = d.get('strCdPn') or d.get('strCdPN') or ''

        # priority_id: priorityTypeId yoki nPriorityId
        priority_id = d.get('priorityTypeId') or d.get('nPriorityId')

        # call_type_id: faqat nCallTypeId (callId112 bu call ID, type emas)
        call_type_id = d.get('nCallTypeId') or 0

        incident, created = Incident112.objects.update_or_create(
            card_number=d['card112Number'],
            defaults=dict(
                dt_create=_parse_112_date(d.get('dtCreate112') or d.get('the_date')),
                operator=d.get('strCreator112'),
                called_phone=called_phone,
                fabula=d.get('fabula'),
                call_type_id=call_type_id,
                incident_type_id=d.get('nIncidentTypeId') or 0,
                incident_description=d.get('strIncidentDescription') or '',
                country_area_id=d.get('nCountryAreaId'),
                district_id_112=str(d.get('nDistrictID') or d.get('cityDistrictId') or ''),
                city_id=d.get('nCityID'),
                local_district_id=d.get('nLocalDistrictId') or d.get('cityDistrictId'),
                mahallya_id=d.get('nMahallyaId'),
                street_id=str(d.get('nStreetID') or ''),
                building=d.get('strBuilding'),
                entrance=d.get('strEntrance'),
                floor=d.get('nFloor'),
                flat=d.get('strFlat'),
                block=d.get('strBlock'),
                note=d.get('strNote'),
                latitude=lat,
                longitude=lon,
                l_control=d.get('lControl'),
                dt_time_from=_parse_112_date(d.get('dtTimeFrom')),
                dt_time_to=_parse_112_date(d.get('dtTimeTo')),
                addendum_id=d.get('nAddendumId'),
                dept_id=d.get('nDeptId'),
                priority_id=priority_id,
                l_hospital_application=d.get('lHospitalApplication'),
                first_card_id=d.get('firstCardId'),
                new_card=d.get('newCard'),
                appeal_type_id=d.get('nAppealTypeId'),
                card_creation_area_id=d.get('cardCreationAreaId'),
                call_id_112=str(d.get('callID112') or d.get('callId112') or ''),
                declarant_info=declarant_info,
                victim_info=victim_info,
                traffic_collision=traffic_info,
                hospital_application_data=hospital_info,
                # Yangi fieldlar
                incident_id_112=d.get('id'),
                incident_type_str=d.get('incidentType'),
                priority_type_str=d.get('priorityType'),
                appeal_type=d.get('appealType'),
                city_name=d.get('nCity'),
                database_name=d.get('database_name'),
                raw_payload=raw_payload,
            ),
        )
        return incident, created


class Incident112ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident112
        fields = [
            'id', 'card_number', 'dt_create', 'operator', 'called_phone',
            'fabula', 'call_type_id', 'incident_type_id', 'incident_description',
            'latitude', 'longitude', 'priority_id',
            'district_id_112', 'mahallya_id',
            'new_card', 'created_time',
        ]


class Incident112DetailSerializer(serializers.ModelSerializer):
    notifications_count = serializers.IntegerField(
        source='notifications.count', read_only=True
    )

    class Meta:
        model = Incident112
        exclude = ['raw_payload']


class Incident112NotificationSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(source='incident.card_number')
    incident_id_112 = serializers.IntegerField(source='incident.incident_id_112', allow_null=True)
    incident_type_id = serializers.IntegerField(source='incident.incident_type_id')
    incident_type_str = serializers.CharField(source='incident.incident_type_str', allow_null=True)
    incident_description = serializers.CharField(source='incident.incident_description')
    latitude = serializers.FloatField(source='incident.latitude', allow_null=True)
    longitude = serializers.FloatField(source='incident.longitude', allow_null=True)
    priority_id = serializers.IntegerField(source='incident.priority_id', allow_null=True)
    priority_type_str = serializers.CharField(source='incident.priority_type_str', allow_null=True)
    fabula = serializers.CharField(source='incident.fabula', allow_null=True)
    called_phone = serializers.CharField(source='incident.called_phone')
    city_name = serializers.CharField(source='incident.city_name', allow_null=True)
    building = serializers.CharField(source='incident.building', allow_null=True)
    note = serializers.CharField(source='incident.note', allow_null=True)
    operator = serializers.CharField(source='incident.operator', allow_null=True)
    dt_create = serializers.CharField(source='incident.dt_create', allow_null=True)
    incident_created_at = serializers.DateTimeField(source='incident.created_time')
    declarant_info = serializers.JSONField(source='incident.declarant_info', allow_null=True)
    victim_info = serializers.JSONField(source='incident.victim_info', allow_null=True)

    class Meta:
        model = Incident112Notification
        fields = [
            'id', 'incident_id',
            'incident_id_112', 'card_number',
            'incident_type_id', 'incident_type_str',
            'incident_description',
            'latitude', 'longitude',
            'priority_id', 'priority_type_str',
            'fabula', 'called_phone',
            'city_name', 'building', 'note',
            'operator', 'dt_create', 'incident_created_at',
            'declarant_info', 'victim_info',
            'distance_km', 'sent_at', 'is_read', 'read_at',
        ]

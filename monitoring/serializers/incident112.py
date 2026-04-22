from rest_framework import serializers

from monitoring.models import Incident112, Incident112Notification


class FlexibleIntegerField(serializers.IntegerField):
    """112 tizim ba'zan float yoki string yuboradi — int ga aylantiradi."""

    def to_internal_value(self, data):
        if data is None:
            if self.allow_null:
                return None
            self.fail('null')
        try:
            return int(float(str(data)))
        except (ValueError, TypeError):
            self.fail('invalid')


class GeoInfoSerializer(serializers.Serializer):
    lat = serializers.FloatField(allow_null=True, required=False)
    lon = serializers.FloatField(allow_null=True, required=False)


class Incident112CreateSerializer(serializers.Serializer):
    card112Number = serializers.CharField()
    dtCreate112 = FlexibleIntegerField()
    strCreator112 = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    strCdPN = serializers.CharField()
    fabula = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    nCallTypeId = FlexibleIntegerField()
    nIncidentTypeId = FlexibleIntegerField()
    strIncidentDescription = serializers.CharField()
    nCountryAreaId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nDistrictID = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    nCityID = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nLocalDistrictId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nMahallyaId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nStreetID = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    strBuilding = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    strEntrance = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    nFloor = FlexibleIntegerField(allow_null=True, required=False, default=None)
    geoInfo = GeoInfoSerializer(allow_null=True, required=False, default=None)
    declarantInfo = serializers.DictField(allow_null=True, required=False, default=None)
    victimInfo = serializers.DictField(allow_null=True, required=False, default=None)
    lControl = FlexibleIntegerField(allow_null=True, required=False, default=None)
    strFlat = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    strBlock = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    strNote = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)
    dtTimeFrom = FlexibleIntegerField(allow_null=True, required=False, default=None)
    dtTimeTo = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nAddendumId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nDeptId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    nPriorityId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    lHospitalApplication = serializers.BooleanField(allow_null=True, required=False, default=None)
    firstCardId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    trafficCollision = serializers.DictField(allow_null=True, required=False, default=None)
    hospitalApplication = serializers.DictField(allow_null=True, required=False, default=None)
    newCard = serializers.BooleanField(allow_null=True, required=False, default=None)
    nAppealTypeId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    cardCreationAreaId = FlexibleIntegerField(allow_null=True, required=False, default=None)
    callID112 = serializers.CharField(allow_null=True, allow_blank=True, required=False, default=None)

    def save(self, raw_payload):
        d = self.validated_data
        geo = d.get('geoInfo') or {}
        incident, created = Incident112.objects.update_or_create(
            card_number=d['card112Number'],
            defaults=dict(
                dt_create=d['dtCreate112'],
                operator=d.get('strCreator112'),
                called_phone=d['strCdPN'],
                fabula=d.get('fabula'),
                call_type_id=d['nCallTypeId'],
                incident_type_id=d['nIncidentTypeId'],
                incident_description=d['strIncidentDescription'],
                country_area_id=d.get('nCountryAreaId'),
                district_id_112=d.get('nDistrictID'),
                city_id=d.get('nCityID'),
                local_district_id=d.get('nLocalDistrictId'),
                mahallya_id=d.get('nMahallyaId'),
                street_id=d.get('nStreetID'),
                building=d.get('strBuilding'),
                entrance=d.get('strEntrance'),
                floor=d.get('nFloor'),
                flat=d.get('strFlat'),
                block=d.get('strBlock'),
                note=d.get('strNote'),
                latitude=geo.get('lat') if isinstance(geo, dict) else None,
                longitude=geo.get('lon') if isinstance(geo, dict) else None,
                l_control=d.get('lControl'),
                dt_time_from=d.get('dtTimeFrom'),
                dt_time_to=d.get('dtTimeTo'),
                addendum_id=d.get('nAddendumId'),
                dept_id=d.get('nDeptId'),
                priority_id=d.get('nPriorityId'),
                l_hospital_application=d.get('lHospitalApplication'),
                first_card_id=d.get('firstCardId'),
                new_card=d.get('newCard'),
                appeal_type_id=d.get('nAppealTypeId'),
                card_creation_area_id=d.get('cardCreationAreaId'),
                call_id_112=d.get('callID112'),
                declarant_info=d.get('declarantInfo'),
                victim_info=d.get('victimInfo'),
                traffic_collision=d.get('trafficCollision'),
                hospital_application_data=d.get('hospitalApplication'),
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
    incident_type_id = serializers.IntegerField(source='incident.incident_type_id')
    incident_description = serializers.CharField(source='incident.incident_description')
    latitude = serializers.FloatField(source='incident.latitude', allow_null=True)
    longitude = serializers.FloatField(source='incident.longitude', allow_null=True)
    priority_id = serializers.IntegerField(source='incident.priority_id', allow_null=True)
    fabula = serializers.CharField(source='incident.fabula', allow_null=True)
    called_phone = serializers.CharField(source='incident.called_phone')
    incident_created_at = serializers.DateTimeField(source='incident.created_time')

    class Meta:
        model = Incident112Notification
        fields = [
            'id', 'incident_id',
            'card_number', 'incident_type_id', 'incident_description',
            'latitude', 'longitude', 'priority_id', 'fabula', 'called_phone',
            'incident_created_at',
            'distance_km', 'sent_at', 'is_read', 'read_at',
        ]

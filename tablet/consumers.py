import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class LocationConsumer(AsyncWebsocketConsumer):
    """
    Navbatchi planshetidan real-time joylashuv qabul qiladi.
    Ulanish: ws://.../ws/location/{section_id}/?token=<jwt>

    Client yuboradi:
        {"lat": 41.299, "lon": 69.240, "accuracy": 5.0}

    Server saqlab, monitoring guruhi ga broadcast qiladi:
        {"type": "location_update", "employee_id": 3, "employee_name": "...",
         "lat": 41.299, "lon": 69.240, "accuracy": 5.0, "timestamp": "..."}
    """

    async def connect(self):
        self.section_id = self.scope['url_route']['kwargs']['section_id']
        self.ws_group = f"location_{self.section_id}"

        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        verified = await self._verify_assignment(user)
        if not verified:
            await self.close(code=4003)
            return

        self.user = user
        await self.channel_layer.group_add(self.ws_group, self.channel_name)
        await self.accept()
        logger.info(f"LocationConsumer: {user} connected section={self.section_id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'ws_group'):
            await self.channel_layer.group_discard(self.ws_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        lat = data.get('lat')
        lon = data.get('lon')
        if lat is None or lon is None:
            return

        accuracy = data.get('accuracy')
        timestamp = await self._save_location(lat, lon, accuracy)

        await self.channel_layer.group_send(
            self.ws_group,
            {
                'type': 'location_update',
                'employee_id': self.user.pk,
                'employee_name': str(self.user),
                'lat': float(lat),
                'lon': float(lon),
                'accuracy': accuracy,
                'timestamp': str(timestamp),
            }
        )

    async def location_update(self, event):
        """Guruh xabarini clientga yuboradi (monitoring tomoniga)."""
        await self.send(text_data=json.dumps(event))

    # ── Helpers ────────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _authenticate(self):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError

        User = get_user_model()
        query_string = self.scope.get('query_string', b'').decode()
        params = {}
        for part in query_string.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
                params[k] = v

        token_str = params.get('token')
        if not token_str:
            return None
        try:
            token = AccessToken(token_str)
            return User.objects.select_related('organization').get(pk=token['user_id'])
        except (TokenError, Exception):
            return None

    @database_sync_to_async
    def _verify_assignment(self, user):
        from monitoring.models import DutySection
        try:
            section = DutySection.objects.get(pk=self.section_id)
            return section.assignments.filter(employees=user).exists()
        except DutySection.DoesNotExist:
            return False

    @database_sync_to_async
    def _save_location(self, lat, lon, accuracy):
        from tablet.models import EmployeeLocationLog
        log = EmployeeLocationLog.objects.create(
            employee=self.user,
            duty_section_id=self.section_id,
            latitude=lat,
            longitude=lon,
            accuracy=accuracy,
        )
        return log.timestamp

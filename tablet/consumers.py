import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


@database_sync_to_async
def _jwt_user(scope):
    """Query string dagi ?token=<jwt> dan foydalanuvchini qaytaradi."""
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError

    User = get_user_model()
    qs = scope.get('query_string', b'').decode()
    params = {}
    for part in qs.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[k] = v

    token_str = params.get('token', '').strip()
    if not token_str:
        return None
    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token['user_id'], is_active=True)
    except (TokenError, User.DoesNotExist, KeyError):
        return None


class IncidentConsumer(AsyncWebsocketConsumer):
    """
    ws://.../ws/incidents/?token=<jwt_access_token>

    Tablet ulanadi va o'ziga yuborilgan 112 hodisa xabarlarini oladi.
    Har bir foydalanuvchi o'z guruhi: `incident_user_{user_id}`
    """

    async def connect(self):
        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f'incident_user_{user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("IncidentConsumer: user=%s connected", user.id)

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Tabletdan kelgan xabarlar — hozircha faqat ping/read."""
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return

        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

        elif data.get('type') == 'read' and data.get('notification_id'):
            await self._mark_read(data['notification_id'])

    # ── Channel layer handler ────────────────────────────────────

    async def incident_notification(self, event):
        """Celery task group_send → tabletga yuborish."""
        await self.send(text_data=json.dumps({
            'type': 'incident',
            'data': event['data'],
        }))

    # ── Helpers ─────────────────────────────────────────────────

    async def _authenticate(self):
        return await _jwt_user(self.scope)

    @database_sync_to_async
    def _mark_read(self, notification_id):
        from django.utils import timezone
        from monitoring.models import Incident112Notification

        Incident112Notification.objects.filter(
            id=notification_id,
            employee=self.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())


class AdminAlarmConsumer(AsyncWebsocketConsumer):
    """
    ws://.../ws/admin/alarms/?token=<jwt>

    Admin (DISTRICT_ADMIN, COLLECTOR, SUPER_ADMIN) alarm voqealarini
    real vaqtda oladi.

    Guruhlar:
      SUPER_ADMIN    → 'alarms_all'
      Boshqalar      → 'alarms_district_{district_id}'
    """

    async def connect(self):
        user = await _jwt_user(self.scope)
        if user is None:
            await self.close(code=4001)
            return

        self.user = user
        self.groups = await self._resolve_groups(user)

        for group in self.groups:
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()
        logger.info("AdminAlarmConsumer: user=%s connected, groups=%s", user.id, self.groups)

    async def disconnect(self, code):
        for group in getattr(self, 'groups', []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def alarm_event(self, event):
        """channel_layer group_send → adminga yuborish."""
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def _resolve_groups(self, user):
        groups = ['alarms_all']
        if not user.is_super_admin():
            district_id = user.district_id or (
                user.organization.district_id if user.organization else None
            )
            if district_id:
                groups.append(f'alarms_district_{district_id}')
        return groups

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


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

    @database_sync_to_async
    def _authenticate(self):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError

        User = get_user_model()
        qs = self.scope.get('query_string', b'').decode()
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

    @database_sync_to_async
    def _mark_read(self, notification_id):
        from django.utils import timezone
        from monitoring.models import Incident112Notification

        Incident112Notification.objects.filter(
            id=notification_id,
            employee=self.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())

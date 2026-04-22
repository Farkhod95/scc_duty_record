import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Django HTTP application ni oldin ishga tushiramiz
django_asgi_app = get_asgi_application()

from tablet.routing import websocket_urlpatterns  # noqa: E402 (import after setup)

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(websocket_urlpatterns),
})

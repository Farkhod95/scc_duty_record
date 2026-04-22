from django.urls import path
from tablet.consumers import IncidentConsumer

websocket_urlpatterns = [
    path('ws/incidents/', IncidentConsumer.as_asgi()),
]

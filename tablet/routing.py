from django.urls import path
from tablet.consumers import IncidentConsumer, AdminAlarmConsumer

websocket_urlpatterns = [
    path('ws/incidents/', IncidentConsumer.as_asgi()),   # Tablet
    path('ws/admin/alarms/', AdminAlarmConsumer.as_asgi()),  # Admin
]

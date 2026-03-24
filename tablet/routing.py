from django.urls import re_path
from tablet.consumers import LocationConsumer

websocket_urlpatterns = [
    re_path(r'^ws/location/(?P<section_id>\d+)/$', LocationConsumer.as_asgi()),
]

from django.urls import path, re_path
from fleet.views import (
    TransportTypeView,
    TransportTypeDetailView,
    TransportTypeFieldInfoView,

    TransportView,
    TransportDetailView,
    TransportFieldInfoView
)

urlpatterns = [
    # TransportType endpoints
    re_path(r'^transport-type/$', TransportTypeView.as_view(), name='transport_type_view'),
    path('transport-type/<int:pk>', TransportTypeDetailView.as_view(), name='transport_type_detail_view'),
    path('transport-type/fields/', TransportTypeFieldInfoView.as_view(), name='transport_type_fields_info'),

    # Transport endpoints
    re_path(r'^transport/$', TransportView.as_view(), name='transport_view'),
    path('transport/<int:pk>', TransportDetailView.as_view(), name='transport_detail_view'),
    path('transport/fields/', TransportFieldInfoView.as_view(), name='transport_fields_info'),
]
from django.urls import path
from tablet.views import TabletMyDutyView, TabletDutyStartView, TabletDutyEndView, TabletTodayDutyView, TabletMeView
from tablet.auth import TabletAuthView

urlpatterns = [
    path('tablet/auth/', TabletAuthView.as_view(), name='tablet_auth'),
    path('me/', TabletMeView.as_view(), name='tablet_me'),
    path('duty/', TabletMyDutyView.as_view(), name='tablet_my_duty'),
    path('duty/today/', TabletTodayDutyView.as_view(), name='tablet_today_duty'),
    path('duty/<int:section_id>/start/', TabletDutyStartView.as_view(), name='tablet_duty_start'),
    path('duty/<int:section_id>/end/', TabletDutyEndView.as_view(), name='tablet_duty_end'),
]

from django.urls import re_path, path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from restapp.views.language import LanguagesView
from restapp.views.logout import LogoutView
from restapp.views.model_change_log import ModelChangeLogView, ModelChangeLogDetailView
from restapp.views.notification import NotificationView, NotificationDetailView
from restapp.views.notification_count import NotificationCountView
from restapp.views.term import TermView, TermDetailView
from restapp.views.translations import TranslationsView
from restapp.views.user_log import UserLogsView
from users.view.user import TokenAuthView

urlpatterns = [
    # re_path(r'^auth/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^auth/token/$', TokenAuthView.as_view(), name='token_obtain_pair'),
    # # re_path(r'^auth/token/$', TokenAuthView.as_view(), name='token_obtain_pair'),
    re_path(r'^auth/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^auth/logout/$', LogoutView.as_view(), name='auth_logout'),
    path('', include('users.urls')),
    path('', include('monitoring.urls')),
    path('', include('directory.urls')),
    re_path(r'^notification/$', NotificationView.as_view(), name='notification_view'),
    path('notification/<int:pk>', NotificationDetailView.as_view(), name='notification_detail_view'),
    path('notification/count/', NotificationCountView.as_view(), name='notification_detail_view'),

    re_path(r'^model-change-log/$', ModelChangeLogView.as_view(), name='model-change-log-view'),
    path('model-change-log/<int:pk>', ModelChangeLogDetailView.as_view(), name='model-change-log-detail-view'),
    re_path(r'^settings/languages/$', LanguagesView.as_view(), name='languages_list'),
    re_path(r'^settings/translations/$', TermView.as_view(), name='translations_list'),
    path('settings/translations/<int:pk>', TermDetailView.as_view(), name='translations_list'),
    re_path(r'^settings/userlogs/$', UserLogsView.as_view(), name='user_logs'),
    path('translations', TranslationsView.as_view(), name='translations_list'),
]

router = DefaultRouter()
urlpatterns += router.urls
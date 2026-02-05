from django.urls import path, re_path
from monitoring.views import (
    DutyCategoryView,
    DutyCategoryDetailView,
    DutyCategoryFieldInfoView,

    DutyView,
    DutyDetailView,
    DutyFieldInfoView,
    DutyApproveView,
    DutyRejectView,
    DutyActivateView,
    DutyCompleteView,
    DutyCancelView,
    DutyFileView,
    DutyFileDetailView,

    DutyUserAddView,
    DutyUserUpdateView,
)

urlpatterns = [
    # DutyCategory endpoints
    re_path(r'^duty-category/$', DutyCategoryView.as_view(), name='duty_category_view'),
    path('duty-category/<int:pk>', DutyCategoryDetailView.as_view(), name='duty_category_detail_view'),
    path('duty-category/fields/', DutyCategoryFieldInfoView.as_view(), name='duty_category_fields_info'),

    # Duty endpoints
    re_path(r'^duty/$', DutyView.as_view(), name='duty_view'),
    path('duty/<int:pk>', DutyDetailView.as_view(), name='duty_detail_view'),
    path('duty/fields/', DutyFieldInfoView.as_view(), name='duty_fields_info'),

    # Duty actions
    path('duty/<int:pk>/approve/', DutyApproveView.as_view(), name='duty_approve'),
    path('duty/<int:pk>/reject/', DutyRejectView.as_view(), name='duty_reject'),
    path('duty/<int:pk>/activate/', DutyActivateView.as_view(), name='duty_activate'),
    path('duty/<int:pk>/complete/', DutyCompleteView.as_view(), name='duty_complete'),
    path('duty/<int:pk>/cancel/', DutyCancelView.as_view(), name='duty_cancel'),

    # Duty File endpoints
    path('duty/<int:duty_id>/files/', DutyFileView.as_view(), name='duty_file_view'),
    path('duty/files/<int:pk>', DutyFileDetailView.as_view(), name='duty_file_detail_view'),

    # Duty User endpoints
    path('duty/<int:pk>/users/', DutyUserAddView.as_view(), name='duty_user_add'),
    path('duty/<int:pk>/users/<int:user_pk>', DutyUserUpdateView.as_view(), name='duty_user_update'),
]
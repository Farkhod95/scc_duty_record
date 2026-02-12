from django.urls import path, re_path

from monitoring.views import (
    MainDutyView, MainDutyDetailView,
    MainDutySendForApprovalView, MainDutyApproveView, MainDutyRejectView,
    DutySectionView, DutySectionDetailView,
    TaskView, TaskDetailView,
    TaskAssignmentView, TaskAssignmentDetailView,
    DutyFileView, DutyFileDetailView,
    DailyDutyOfficerView, DailyDutyOfficerDetailView,
)

urlpatterns = [
    # MainDuty
    re_path(r'^main-duty/$', MainDutyView.as_view(), name='main_duty_view'),
    path('main-duty/<int:pk>', MainDutyDetailView.as_view(), name='main_duty_detail_view'),
    path('main-duty/<int:pk>/send-for-approval/', MainDutySendForApprovalView.as_view(), name='main_duty_send_for_approval'),
    path('main-duty/<int:pk>/approve/', MainDutyApproveView.as_view(), name='main_duty_approve'),
    path('main-duty/<int:pk>/reject/', MainDutyRejectView.as_view(), name='main_duty_reject'),

    # DutySection (nested under main-duty)
    path('main-duty/<int:main_duty_id>/sections/', DutySectionView.as_view(), name='duty_section_view'),
    path('main-duty/<int:main_duty_id>/sections/<int:pk>', DutySectionDetailView.as_view(), name='duty_section_detail_view'),

    # Task (nested under section)
    path('sections/<int:section_id>/tasks/', TaskView.as_view(), name='task_view'),
    path('sections/<int:section_id>/tasks/<int:pk>', TaskDetailView.as_view(), name='task_detail_view'),

    # TaskAssignment (nested under task)
    path('tasks/<int:task_id>/assignments/', TaskAssignmentView.as_view(), name='task_assignment_view'),
    path('tasks/<int:task_id>/assignments/<int:pk>', TaskAssignmentDetailView.as_view(), name='task_assignment_detail_view'),

    # DutyFile (nested under main-duty)
    path('main-duty/<int:main_duty_id>/files/', DutyFileView.as_view(), name='duty_file_view'),
    path('main-duty/files/<int:pk>', DutyFileDetailView.as_view(), name='duty_file_detail_view'),

    # DailyDutyOfficer
    re_path(r'^daily-duty-officer/$', DailyDutyOfficerView.as_view(), name='daily_duty_officer_view'),
    path('daily-duty-officer/<int:pk>', DailyDutyOfficerDetailView.as_view(), name='daily_duty_officer_detail_view'),
]

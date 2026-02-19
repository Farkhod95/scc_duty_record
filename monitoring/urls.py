from django.urls import path, re_path

from monitoring.views import (
    MainDutyView, MainDutyDetailView,
    MainDutySendForApprovalView, MainDutyApproveView, MainDutyRejectView,
    TaskView, TaskDetailView,
    TaskAssignmentView, TaskAssignmentDetailView,
    AbsenceRequestCreateView, AbsenceRequestReviewView, AbsenceRequestListView,
    DutyFileView, DutyFileDetailView,
    DailyDutyOfficerView, DailyDutyOfficerDetailView,
    DashboardView,
    LocationTasksView,
)

urlpatterns = [
    # Dashboard
    re_path(r'^dashboard/$', DashboardView.as_view(), name='dashboard_view'),

    # MainDuty
    re_path(r'^main-duty/$', MainDutyView.as_view(), name='main_duty_view'),
    path('main-duty/<int:pk>', MainDutyDetailView.as_view(), name='main_duty_detail_view'),
    path('main-duty/<int:pk>/send-for-approval/', MainDutySendForApprovalView.as_view(), name='main_duty_send_for_approval'),
    path('main-duty/<int:pk>/approve/', MainDutyApproveView.as_view(), name='main_duty_approve'),
    path('main-duty/<int:pk>/reject/', MainDutyRejectView.as_view(), name='main_duty_reject'),

    # Task (nested under main-duty)
    path('main-duty/<int:main_duty_id>/tasks/', TaskView.as_view(), name='task_view'),
    path('main-duty/<int:main_duty_id>/tasks/<int:pk>', TaskDetailView.as_view(), name='task_detail_view'),

    # TaskAssignment (nested under task)
    path('tasks/<int:task_id>/assignments/', TaskAssignmentView.as_view(), name='task_assignment_view'),
    path('tasks/<int:task_id>/assignments/<int:pk>', TaskAssignmentDetailView.as_view(), name='task_assignment_detail_view'),

    # AbsenceRequest
    path('tasks/<int:task_id>/assignments/<int:pk>/absence-request/', AbsenceRequestCreateView.as_view(), name='absence_request_create'),
    re_path(r'^absence-requests/$', AbsenceRequestListView.as_view(), name='absence_request_list'),
    path('absence-requests/<int:pk>/', AbsenceRequestReviewView.as_view(), name='absence_request_review'),

    # DutyFile (nested under main-duty)
    path('main-duty/<int:main_duty_id>/files/', DutyFileView.as_view(), name='duty_file_view'),
    path('main-duty/files/<int:pk>', DutyFileDetailView.as_view(), name='duty_file_detail_view'),

    # Location Tasks
    re_path(r'^location-tasks/$', LocationTasksView.as_view(), name='location_tasks_view'),

    # DailyDutyOfficer
    re_path(r'^daily-duty-officer/$', DailyDutyOfficerView.as_view(), name='daily_duty_officer_view'),
    path('daily-duty-officer/<int:pk>', DailyDutyOfficerDetailView.as_view(), name='daily_duty_officer_detail_view'),
]

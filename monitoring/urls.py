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
    EmployeeAttendanceView,
    DutyDayListCreateView, DutyDayDetailView,
    DutySectionDetailView,
    DutySectionAssignmentListCreateView, DutySectionAssignmentDetailView,
    DutyDaySubmitView, DutyDayCollectView, DutyDayApproveView, DutyDayRejectView,
    DistrictDutyView, DutyDayPdfView,
    EventListCreateView, EventDetailView,
    EventAssignmentListCreateView, EventAssignmentDetailView,
    EventSubmitView, EventCollectView, EventApproveView, EventRejectView,
    EventPdfView,
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
    path('absence-requests/<int:pk>', AbsenceRequestReviewView.as_view(), name='absence_request_review'),

    # DutyFile (nested under main-duty)
    path('main-duty/<int:main_duty_id>/files/', DutyFileView.as_view(), name='duty_file_view'),
    path('main-duty/files/<int:pk>', DutyFileDetailView.as_view(), name='duty_file_detail_view'),

    # Location Tasks
    re_path(r'^location-tasks/$', LocationTasksView.as_view(), name='location_tasks_view'),

    # DailyDutyOfficer
    re_path(r'^daily-duty-officer/$', DailyDutyOfficerView.as_view(), name='daily_duty_officer_view'),
    path('daily-duty-officer/<int:pk>', DailyDutyOfficerDetailView.as_view(), name='daily_duty_officer_detail_view'),

    # Integration: Employee Attendance
    re_path(r'^attendance/$', EmployeeAttendanceView.as_view(), name='employee_attendance'),

    # ── Etap 2: Yangi navbatchilik ──────────────────────────────────────────
    # DutyDay
    path('duty-days/', DutyDayListCreateView.as_view(), name='duty_day_list'),
    path('duty-days/<int:pk>', DutyDayDetailView.as_view(), name='duty_day_detail'),

    # DutySection
    path('duty-sections/<int:pk>', DutySectionDetailView.as_view(), name='duty_section_detail'),

    # DutySectionAssignment
    path('duty-sections/<int:section_id>/assignments/', DutySectionAssignmentListCreateView.as_view(), name='duty_section_assignment_list'),
    path('duty-section-assignments/<int:pk>', DutySectionAssignmentDetailView.as_view(), name='duty_section_assignment_detail'),

    # ── Etap 4: Tasdiqlash zanjiri ──────────────────────────────────────────
    path('duty-days/<int:pk>/submit/', DutyDaySubmitView.as_view(), name='duty_day_submit'),
    path('duty-days/<int:pk>/collect/', DutyDayCollectView.as_view(), name='duty_day_collect'),
    path('duty-days/<int:pk>/approve/', DutyDayApproveView.as_view(), name='duty_day_approve'),
    path('duty-days/<int:pk>/reject/', DutyDayRejectView.as_view(), name='duty_day_reject'),

    # Tuman ko'rinishi (navbatchilik + tadbir)
    path('district-duty/', DistrictDutyView.as_view(), name='district_duty'),

    # ── Etap 5: Tadbir (Event) ──────────────────────────────────────────────
    path('events/', EventListCreateView.as_view(), name='event_list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event_detail'),
    path('events/<int:event_id>/assignments/', EventAssignmentListCreateView.as_view(), name='event_assignment_list'),
    path('event-assignments/<int:pk>', EventAssignmentDetailView.as_view(), name='event_assignment_detail'),
    path('events/<int:pk>/submit/', EventSubmitView.as_view(), name='event_submit'),
    path('events/<int:pk>/collect/', EventCollectView.as_view(), name='event_collect'),
    path('events/<int:pk>/approve/', EventApproveView.as_view(), name='event_approve'),
    path('events/<int:pk>/reject/', EventRejectView.as_view(), name='event_reject'),

    # ── Etap 6: PDF ─────────────────────────────────────────────────────────
    path('duty-days/<int:pk>/pdf/', DutyDayPdfView.as_view(), name='duty_day_pdf'),
    path('events/<int:pk>/pdf/', EventPdfView.as_view(), name='event_pdf'),
]

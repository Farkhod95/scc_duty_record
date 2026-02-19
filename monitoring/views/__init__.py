from monitoring.views.main_duty import (
    MainDutyView, MainDutyDetailView,
    MainDutySendForApprovalView, MainDutyApproveView, MainDutyRejectView,
)
from monitoring.views.task import TaskView, TaskDetailView
from monitoring.views.task_assignment import (
    TaskAssignmentView, TaskAssignmentDetailView,
    AbsenceRequestCreateView, AbsenceRequestReviewView,
    AbsenceRequestListView,
)
from monitoring.views.duty_file import DutyFileView, DutyFileDetailView
from monitoring.views.daily_duty_officer import DailyDutyOfficerView, DailyDutyOfficerDetailView
from monitoring.views.dashboard import DashboardView
from monitoring.views.location_tasks import LocationTasksView

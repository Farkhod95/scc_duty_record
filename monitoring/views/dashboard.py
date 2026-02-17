from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import MainDuty, MainDutyStatus
from monitoring.serializers.main_duty import MainDutyListSerializer
from users.utils.permissions import IsOrgAdmin


class DashboardView(APIView):
    permission_classes = [IsOrgAdmin]

    def get(self, request):
        queryset = MainDuty.objects.select_related('organization', 'created_by')

        if not request.user.is_superuser:
            queryset = queryset.filter(organization=request.user.organization)

        # Statistika
        stats = queryset.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=MainDutyStatus.SENT_FOR_APPROVAL)),
            approved=Count('id', filter=Q(status=MainDutyStatus.APPROVED)),
            rejected=Count('id', filter=Q(status=MainDutyStatus.REJECTED)),
            draft=Count('id', filter=Q(status=MainDutyStatus.DRAFT)),
        )

        # Bugungi navbatchiliklar
        today = timezone.localdate()
        today_duties = queryset.filter(
            duty_date=today
        ).annotate(tasks_count=Count('tasks'))

        serializer = MainDutyListSerializer(today_duties, many=True)

        return Response({
            'statistics': {
                'total': stats['total'],
                'draft': stats['draft'],
                'pending': stats['pending'],
                'approved': stats['approved'],
                'rejected': stats['rejected'],
            },
            'today_duties': serializer.data,
        }, status=status.HTTP_200_OK)

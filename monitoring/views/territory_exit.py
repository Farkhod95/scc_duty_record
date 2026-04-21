from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import TerritoryExitLog
from monitoring.serializers.territory_exit import (
    TerritoryExitLogCreateSerializer,
    TerritoryExitLogReturnSerializer,
    TerritoryExitLogSerializer,
)


class TerritoryExitLogCreateView(APIView):
    """
    POST /api/v1/territory-exit/

    Tablet: xodim hududni tark etish sababini yozadi.
    Authenticated user avtomatik employee sifatida olinadi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TerritoryExitLogCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        log = serializer.save()
        return Response(
            {
                'success': True,
                'message': 'Hudud tark etish qayd etildi.',
                'data': TerritoryExitLogSerializer(log).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TerritoryExitLogListView(APIView):
    """
    GET /api/v1/territory-exit/list/

    Admin: barcha chiqish yozuvlari ro'yxati.
    Filter parametrlari:
      - employee_id
      - date (YYYY-MM-DD) — exit_time bo'yicha
      - task_assignment_id
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = TerritoryExitLog.objects.select_related(
            'employee', 'employee__position', 'task_assignment'
        )

        employee_id = request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        date_str = request.query_params.get('date')
        if date_str:
            qs = qs.filter(exit_time__date=date_str)

        task_assignment_id = request.query_params.get('task_assignment_id')
        if task_assignment_id:
            qs = qs.filter(task_assignment_id=task_assignment_id)

        serializer = TerritoryExitLogSerializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})


class TerritoryExitLogDetailView(APIView):
    """
    GET  /api/v1/territory-exit/<pk>/  — yozuvni ko'rish
    POST /api/v1/territory-exit/<pk>/return/ — qaytish vaqtini belgilash
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return TerritoryExitLog.objects.select_related(
                'employee', 'employee__position', 'task_assignment'
            ).get(pk=pk)
        except TerritoryExitLog.DoesNotExist:
            return None

    def get(self, request, pk):
        log = self.get_object(pk)
        if not log:
            return Response({'detail': 'Topilmadi.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'success': True, 'data': TerritoryExitLogSerializer(log).data})

    def patch(self, request, pk):
        """Xodim qaytganida return_time ni belgilash."""
        log = self.get_object(pk)
        if not log:
            return Response({'detail': 'Topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TerritoryExitLogReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        log.return_time = serializer.validated_data.get('return_time') or timezone.now()
        log.save(update_fields=['return_time', 'updated_time'])

        return Response({
            'success': True,
            'message': 'Qaytish vaqti qayd etildi.',
            'data': TerritoryExitLogSerializer(log).data,
        })

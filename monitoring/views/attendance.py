from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.serializers.attendance import (
    EmployeeAttendanceSerializer,
    EmployeeAttendanceResponseSerializer,
)


class EmployeeAttendanceView(APIView):
    """
    POST /api/v1/attendance/

    Tashqi tizimdan xodim keldi/ketdi ma'lumotini qabul qiladi.
    PINFL SHA256 xeshi orqali xodimni aniqlaydi va hodisani yozib qo'yadi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmployeeAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = serializer.save()

        response_serializer = EmployeeAttendanceResponseSerializer(
            attendance, context={'request': request}
        )
        return Response(
            {
                'success': True,
                'message': 'Xodim aniqlandi va qayd etildi.',
                'data': response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

# monitoring/views/duty.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, CreateAPIView, \
    UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import Duty, DutyFile
from monitoring.serializers.duty import (
    DutySerializer,
    DutyListSerializer,
    DutyDetailSerializer,
    DutyApproveSerializer,
    DutyRejectSerializer,
    DutyCancelSerializer,
    DutyFileSerializer,
)
from monitoring.filterset import DutyFilter
from monitoring.services import duty_service
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class DutyFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in Duty._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class DutyView(ListCreateAPIView):
    serializer_class = DutyListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DutyFilter
    search_fields = ('name', 'organization__name', 'location__title')
    ordering = ['-start_time']

    def get_queryset(self):
        return Duty.objects.select_related(
            'organization', 'location', 'category', 'approved_by'
        ).prefetch_related('duty_users').all()

    def post(self, request):
        serializer = DutySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        duty = duty_service.create_duty(
            data=serializer.validated_data,
            created_by=request.user
        )

        response_serializer = DutyDetailSerializer(duty)
        return Response(response_serializer.data, status.HTTP_201_CREATED)


class DutyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DutySerializer

    def get_queryset(self):
        return Duty.objects.select_related(
            'organization', 'location', 'category', 'approved_by'
        ).prefetch_related('duty_users__user', 'duty_users__transport', 'files').all()

    def get(self, request, pk):
        instance = get_object_or_404(Duty, id=pk)
        serializer = DutyDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Duty, id=pk)

        if not duty_service.can_edit_duty(instance, request.user):
            return Response(
                {'detail': 'Sizda bu duty ni tahrirlash huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)

        response_serializer = DutyDetailSerializer(instance)
        return Response(response_serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Duty, id=pk)

        if instance.status != 'pending':
            return Response(
                {'detail': 'Faqat pending statusdagi duty ni o\'chirish mumkin'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (request.user.is_superuser or instance.created_by == request.user):
            return Response(
                {'detail': 'Sizda bu duty ni o\'chirish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class DutyApproveView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DutyApproveSerializer

    def post(self, request, pk):
        duty = get_object_or_404(Duty, id=pk)

        serializer = DutyApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duty_service.approve_duty(duty=duty, approved_by=request.user)
            response_serializer = DutyDetailSerializer(duty)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyRejectView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DutyRejectSerializer

    def post(self, request, pk):
        duty = get_object_or_404(Duty, id=pk)

        serializer = DutyRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duty_service.reject_duty(
                duty=duty,
                rejected_by=request.user,
                reason=serializer.validated_data['reason']
            )
            response_serializer = DutyDetailSerializer(duty)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyActivateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DutyApproveSerializer

    def post(self, request, pk):
        duty = get_object_or_404(Duty, id=pk)

        try:
            duty_service.activate_duty(duty=duty, activated_by=request.user)
            response_serializer = DutyDetailSerializer(duty)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyCompleteView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DutyApproveSerializer

    def post(self, request, pk):
        duty = get_object_or_404(Duty, id=pk)

        try:
            duty_service.complete_duty(duty=duty, completed_by=request.user)
            response_serializer = DutyDetailSerializer(duty)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyCancelView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DutyCancelSerializer

    def post(self, request, pk):
        duty = get_object_or_404(Duty, id=pk)

        serializer = DutyCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duty_service.cancel_duty(
                duty=duty,
                cancelled_by=request.user,
                reason=serializer.validated_data['reason']
            )
            response_serializer = DutyDetailSerializer(duty)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyFileView(ListCreateAPIView):
    """Duty ga tegishli fayllarni ko'rish va qo'shish"""
    permission_classes = [IsAuthenticated]
    serializer_class = DutyFileSerializer

    def get_queryset(self):
        duty_id = self.kwargs.get('duty_id')
        return DutyFile.objects.filter(duty_id=duty_id)

    def post(self, request, duty_id):
        duty = get_object_or_404(Duty, id=duty_id)

        if not duty_service.can_edit_duty(duty, request.user):
            return Response(
                {'detail': 'Sizda bu duty ga fayl qo\'shish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        data['duty'] = duty_id

        serializer = DutyFileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user, updated_by=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DutyFileDetailView(RetrieveUpdateDestroyAPIView):
    """Duty faylini ko'rish, yangilash va o'chirish"""
    permission_classes = [IsAuthenticated]
    serializer_class = DutyFileSerializer

    def get_queryset(self):
        return DutyFile.objects.all()

    def delete(self, request, pk):
        duty_file = get_object_or_404(DutyFile, id=pk)

        if not duty_service.can_edit_duty(duty_file.duty, request.user):
            return Response(
                {'detail': 'Sizda bu faylni o\'chirish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        duty_file.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
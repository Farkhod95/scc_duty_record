from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.models import MainDuty, MainDutyStatus
from monitoring.serializers.main_duty import (
    MainDutySerializer, MainDutyListSerializer, MainDutyDetailSerializer,
)
from monitoring.filterset import MainDutyFilter
from monitoring.services.main_duty_service import send_for_approval, approve_main_duty, reject_main_duty
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin, IsSuperAdmin


class MainDutyView(ListCreateAPIView):
    serializer_class = MainDutyListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = MainDutyFilter
    search_fields = ('title', 'organization__name')
    ordering = ['-created_time']

    def get_queryset(self):
        queryset = MainDuty.objects.select_related(
            'organization', 'created_by'
        ).annotate(tasks_count=Count('tasks'))

        if self.request.user.is_superuser:
            return queryset.filter(status__in=[MainDutyStatus.SENT_FOR_APPROVAL, MainDutyStatus.APPROVED, MainDutyStatus.REJECTED])

        return queryset.filter(organization=self.request.user.organization)

    def post(self, request):
        serializer = MainDutySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data.get('organization')

        # SuperAdmin — har qanday org uchun yarata oladi
        if request.user.is_superuser:
            serializer.save(created_by=request.user)
            return Response(serializer.data, status.HTTP_201_CREATED)

        # O'z tashkiloti tekshiruvi
        if org != request.user.organization:
            return Response(
                {'error': "Siz faqat o'z organizatsiyangiz uchun navbatchilik yarata olasiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Manager — o'z tashkiloti uchun yarata oladi
        if request.user.is_manager():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status.HTTP_201_CREATED)

        # OrgAdmin — faqat bugungi dijur bo'lsa yarata oladi
        from monitoring.models import DailyDutyOfficer
        from django.utils import timezone
        today = timezone.localdate()
        is_duty_officer = DailyDutyOfficer.objects.filter(
            organization=org, officer=request.user, duty_date=today
        ).exists()

        if not is_duty_officer:
            return Response(
                {'error': "Siz bugun dijur tayinlanmagansiz. Navbatchilik yarata olmaysiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class MainDutyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MainDutySerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = MainDuty.objects.select_related(
            'organization', 'approved_by', 'created_by',
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(organization=self.request.user.organization)

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = MainDutyDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        if instance.status != MainDutyStatus.DRAFT:
            return Response(
                {'error': "Faqat DRAFT holatdagi navbatchilikni tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class MainDutySendForApprovalView(APIView):
    permission_classes = [IsOrgAdmin]

    def post(self, request, pk):
        queryset = MainDuty.objects.all()
        if not request.user.is_superuser:
            queryset = queryset.filter(organization=request.user.organization)

        main_duty = get_object_or_404(queryset, id=pk)
        send_for_approval(main_duty, request.user)
        return Response({'detail': "Tasdiqlashga yuborildi."}, status=status.HTTP_200_OK)


class MainDutyApproveView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        main_duty = get_object_or_404(MainDuty, id=pk)
        approve_main_duty(main_duty, request.user)
        return Response({'detail': "Tasdiqlandi."}, status=status.HTTP_200_OK)


class MainDutyRejectView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        main_duty = get_object_or_404(MainDuty, id=pk)
        reason = request.data.get('rejection_reason', '')
        reject_main_duty(main_duty, request.user, reason)
        return Response({'detail': "Rad etildi."}, status=status.HTTP_200_OK)

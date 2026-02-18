from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response

from monitoring.models import DailyDutyOfficer
from monitoring.serializers.daily_duty_officer import (
    DailyDutyOfficerSerializer, DailyDutyOfficerListSerializer,
)
from monitoring.filterset import DailyDutyOfficerFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsManager


class DailyDutyOfficerView(ListCreateAPIView):
    serializer_class = DailyDutyOfficerListSerializer
    permission_classes = [IsManager]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DailyDutyOfficerFilter
    search_fields = ('officer__first_name', 'officer__last_name')
    ordering = ['-duty_date']

    def get_queryset(self):
        queryset = DailyDutyOfficer.objects.select_related(
            'organization', 'officer', 'assigned_by'
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(organization=self.request.user.organization)

    def post(self, request):
        serializer = DailyDutyOfficerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data.get('organization')
        if not request.user.is_superuser and org != request.user.organization:
            return Response(
                {'error': "Siz faqat o'z organizatsiyangiz uchun dijur tayinlashingiz mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(assigned_by=request.user, created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DailyDutyOfficerDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DailyDutyOfficerSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        queryset = DailyDutyOfficer.objects.select_related(
            'organization', 'officer', 'assigned_by'
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(organization=self.request.user.organization)

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = DailyDutyOfficerListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data.get('organization')
        if not request.user.is_superuser and org != request.user.organization:
            return Response(
                {'error': "Siz faqat o'z organizatsiyangiz uchun dijur tayinlashingiz mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response

from monitoring.models import DutySection, MainDuty, MainDutyStatus
from monitoring.serializers.duty_section import (
    DutySectionSerializer, DutySectionListSerializer, DutySectionDetailSerializer,
)
from monitoring.filterset import DutySectionFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin


class DutySectionView(ListCreateAPIView):
    serializer_class = DutySectionListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DutySectionFilter
    search_fields = ('name', 'section_type__name')

    def get_main_duty(self):
        queryset = MainDuty.objects.all()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(organization=self.request.user.organization)
        return get_object_or_404(queryset, id=self.kwargs['main_duty_id'])

    def get_queryset(self):
        main_duty = self.get_main_duty()
        return DutySection.objects.filter(
            main_duty=main_duty
        ).select_related('section_type').annotate(tasks_count=Count('tasks'))

    def post(self, request, main_duty_id):
        main_duty = self.get_main_duty()

        if main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilikka bo'lim qo'shish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['main_duty'] = main_duty.id
        serializer = DutySectionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DutySectionDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DutySectionSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = DutySection.objects.select_related('main_duty__organization', 'section_type')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                main_duty__organization=self.request.user.organization
            )
        return queryset.filter(main_duty_id=self.kwargs['main_duty_id'])

    def get(self, request, main_duty_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = DutySectionDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, main_duty_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        if instance.main_duty.status != MainDutyStatus.DRAFT:
            return Response(
                {'detail': "Faqat DRAFT holatdagi navbatchilik bo'limini tahrirlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data['main_duty'] = main_duty_id
        serializer = self.serializer_class(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, main_duty_id, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)

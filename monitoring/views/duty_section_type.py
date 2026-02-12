from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.response import Response

from monitoring.models import DutySectionType
from monitoring.serializers.duty_section import (
    DutySectionTypeSerializer, DutySectionTypeListSerializer,
)
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin


class DutySectionTypeView(ListCreateAPIView):
    serializer_class = DutySectionTypeListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    search_fields = ('name',)
    ordering = ['sort_order']

    def get_queryset(self):
        queryset = DutySectionType.objects.select_related('organization')

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(organization=self.request.user.organization)

    def post(self, request):
        serializer = DutySectionTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = serializer.validated_data.get('organization')
        if not request.user.is_superuser and org != request.user.organization:
            return Response(
                {'detail': "Siz faqat o'z organizatsiyangiz uchun bo'lim turi yarata olasiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DutySectionTypeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DutySectionTypeSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = DutySectionType.objects.select_related('organization')

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(organization=self.request.user.organization)

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = DutySectionTypeListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)

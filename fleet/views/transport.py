# fleet/views/transport.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from fleet.models import Transport
from fleet.serializers.transport import TransportSerializer, TransportListSerializer
from fleet.filterset import TransportFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class TransportFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in Transport._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class TransportView(ListCreateAPIView):
    serializer_class = TransportListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = TransportFilter
    search_fields = ('number', 'model', 'organization__name')
    ordering = ['-created_time']

    def get_queryset(self):
        return Transport.objects.select_related('organization', 'type').all()

    def post(self, request):
        serializer = TransportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TransportDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TransportSerializer

    def get_queryset(self):
        return Transport.objects.select_related('organization', 'type').all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Transport, id=pk)
        serializer = TransportListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Transport, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Transport, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
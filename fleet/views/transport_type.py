from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from fleet.models import TransportType
from fleet.filterset import TransportTypeFilter
from fleet.serializers.transport_type import TransportTypeListSerializer, TransportTypeSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class TransportTypeFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in TransportType._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class TransportTypeView(ListCreateAPIView):
    serializer_class = TransportTypeListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = TransportTypeFilter
    search_fields = ('name',)
    ordering = ['name']

    def get_queryset(self):
        return TransportType.objects.all()

    def post(self, request, **kwargs):
        serializer = TransportTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class TransportTypeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TransportTypeSerializer

    def get_queryset(self):
        return TransportType.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk, **kwargs):
        instance = get_object_or_404(TransportType, id=pk)
        serializer = TransportTypeListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(TransportType, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(TransportType, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
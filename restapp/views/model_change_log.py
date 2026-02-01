from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restapp.filterset import ModelChangeLogFilter
from restapp.models import ModelChangeLog
from restapp.serializers import ModelChangeLogListSerializer, ModelChangeLogSerializer

from restapp.pagination import ResultsSetPagination


class ModelChangeLogFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in ModelChangeLog._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class ModelChangeLogView(ListCreateAPIView):
    serializer_class = ModelChangeLogListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ModelChangeLogFilter
    search_fields = ('app_label', 'model_name', 'action', 'action', 'data_before', 'data_after')
    ordering = ['-pk']

    def get_queryset(self):
        queryset = ModelChangeLog.objects.all()
        return queryset

    def post(self, request):
        serializer = ModelChangeLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ModelChangeLogDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ModelChangeLogSerializer

    def get_queryset(self):
        return ModelChangeLog.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ModelChangeLog, id=pk)
        serializer = ModelChangeLogListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ModelChangeLog, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)


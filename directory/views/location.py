from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from directory.models import Location, LocationPoint
from directory.serializers import LocationSerializer, LocationListSerializer, LocationDetailSerializer, LocationPointSerializer
from directory.filterset import LocationFilter
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class LocationFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in Location._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class LocationView(ListCreateAPIView):
    serializer_class = LocationListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = LocationFilter
    search_fields = ('title', 'region__name', 'district__name')
    ordering = ['title']

    def get_queryset(self):
        return Location.objects.select_related('region', 'district').prefetch_related('mahallas').all()

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class LocationDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = LocationSerializer

    def get_queryset(self):
        return Location.objects.select_related('region', 'district').prefetch_related('mahallas', 'points').all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Location, id=pk)
        serializer = LocationDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Location, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Location, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class LocationPointView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, location_pk):
        location = get_object_or_404(Location, id=location_pk)
        points = location.points.order_by('order')
        serializer = LocationPointSerializer(points, many=True)
        return Response(serializer.data)

    def post(self, request, location_pk):
        location = get_object_or_404(Location, id=location_pk)
        serializer = LocationPointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(location=location)
        return Response(serializer.data, status.HTTP_201_CREATED)


class LocationPointDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, location_pk, pk):
        point = get_object_or_404(LocationPoint, id=pk, location_id=location_pk)
        return Response(LocationPointSerializer(point).data)

    def put(self, request, location_pk, pk):
        point = get_object_or_404(LocationPoint, id=pk, location_id=location_pk)
        serializer = LocationPointSerializer(point, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, location_pk, pk):
        point = get_object_or_404(LocationPoint, id=pk, location_id=location_pk)
        point.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
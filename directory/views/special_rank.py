from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from directory.filterset import SpecialRankFilter
from directory.models import SpecialRank
from directory.serializers import SpecialRankSerializer

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class SpecialRankFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in SpecialRank._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class SpecialRankView(ListCreateAPIView):
    serializer_class = SpecialRankSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SpecialRankFilter
    search_fields = ('name_uz', 'name_uz_cyrl', 'name_ru', 'name_kaa')
    ordering = ['pk']

    def get_queryset(self):
        return SpecialRank.objects.all()

    def post(self, request):
        serializer = SpecialRankSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class SpecialRankDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SpecialRankSerializer

    def get_queryset(self):
        return SpecialRank.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(SpecialRank, id=pk)
        serializer = SpecialRankSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(SpecialRank, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(SpecialRank, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)




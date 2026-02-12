from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from monitoring.models import DutyFile, MainDuty
from monitoring.serializers.duty_file import DutyFileSerializer, DutyFileListSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.utils.permissions import IsOrgAdmin


class DutyFileView(ListCreateAPIView):
    serializer_class = DutyFileListSerializer
    permission_classes = [IsOrgAdmin]
    pagination_class = ResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_main_duty(self):
        queryset = MainDuty.objects.all()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(organization=self.request.user.organization)
        return get_object_or_404(queryset, id=self.kwargs['main_duty_id'])

    def get_queryset(self):
        main_duty = self.get_main_duty()
        return DutyFile.objects.filter(main_duty=main_duty)

    def post(self, request, main_duty_id):
        main_duty = self.get_main_duty()

        data = request.data.copy()
        data['main_duty'] = main_duty.id
        serializer = DutyFileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class DutyFileDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DutyFileSerializer
    permission_classes = [IsOrgAdmin]

    def get_queryset(self):
        queryset = DutyFile.objects.select_related('main_duty__organization')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                main_duty__organization=self.request.user.organization
            )
        return queryset

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = DutyFileListSerializer(instance)
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

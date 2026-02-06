from rest_framework import status
from rest_framework.generics import get_object_or_404, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.response import Response

from monitoring.models import Duty, DutyUser
from monitoring.serializers.duty_user import DutyUserSerializer
from monitoring.services import duty_user_service
from users.utils.permissions import IsOrgAdmin


class DutyUserAddView(CreateAPIView):
    permission_classes = [IsOrgAdmin]
    serializer_class = DutyUserSerializer

    def get_duty(self, pk, user):
        """Duty ni olish va organizatsiya tekshiruvi"""
        if user.is_superuser:
            return get_object_or_404(Duty, id=pk)
        return get_object_or_404(Duty, id=pk, organization=user.organization)

    def post(self, request, pk):
        duty = self.get_duty(pk, request.user)

        serializer = DutyUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            duty_user = duty_user_service.add_user_to_duty(
                duty=duty,
                user_id=serializer.validated_data['user'].id,
                transport_id=serializer.validated_data.get('transport').id if serializer.validated_data.get(
                    'transport') else None,
                is_driver=serializer.validated_data.get('is_driver', False),
                created_by=request.user
            )

            response_serializer = DutyUserSerializer(duty_user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DutyUserUpdateView(UpdateAPIView, DestroyAPIView):
    permission_classes = [IsOrgAdmin]
    serializer_class = DutyUserSerializer

    def get_duty(self, pk, user):
        """Duty ni olish va organizatsiya tekshiruvi"""
        if user.is_superuser:
            return get_object_or_404(Duty, id=pk)
        return get_object_or_404(Duty, id=pk, organization=user.organization)

    def put(self, request, pk, user_pk):
        duty = self.get_duty(pk, request.user)
        duty_user = get_object_or_404(DutyUser, duty=duty, id=user_pk)

        try:
            duty_user_service.update_duty_user(
                duty_user=duty_user,
                transport_id=request.data.get('transport'),
                is_driver=request.data.get('is_driver'),
                updated_by=request.user
            )

            serializer = DutyUserSerializer(duty_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, user_pk):
        duty = self.get_duty(pk, request.user)
        duty_user = get_object_or_404(DutyUser, duty=duty, id=user_pk)

        try:
            duty_user_service.remove_user_from_duty(
                duty=duty,
                user_id=duty_user.user_id,
                removed_by=request.user
            )

            return Response({'detail': 'User muvaffaqiyatli o\'chirildi'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

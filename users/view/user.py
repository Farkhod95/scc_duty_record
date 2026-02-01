from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from users.filterset import UserFilter
from users.models import User
from users.serializers import UserSerializer, ChangePasswordSerializer, UserListPublicIdSerializer, UserListSerializer

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from restapp.models import ModelChangeLog
from restapp.utils.utils import get_client_ip
from restapp.utils.utils import log_model_view


def _role_names(user) -> set[str]:
    """
    Return the current user's role names as a lowercase set.
    Handles the M2M relation efficiently.
    """
    if not getattr(user, "is_authenticated", False):
        return set()
    return {name.strip().lower() for name in user.roles.values_list("name", flat=True)}


def _has_any(roles: set[str], candidates: tuple[str, ...]) -> bool:
    cset = {c.lower() for c in candidates}
    return any(r in roles for r in cset)



class TokenAuthView(TokenObtainPairView):
    """
    Login (JWT token olish) uchun view.
    Muvaffaqiyatli login bo'lsa ModelChangeLog ga yozamiz.
    """
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Avval token olishni tekshiramiz
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user  # SimpleJWT shu yerda user ni beradi

        # Asl TokenObtainPairView javobini olamiz
        response = super().post(request, *args, **kwargs)

        # Login muvaffaqiyatli bo‘lgani uchun log yozamiz
        ip = get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")

        ModelChangeLog.objects.create(
            app_label="auth",                 # yoki "users" desang ham bo'ladi
            model_name="User.login",          # bu o'zing tanlagan nom
            object_id=str(user.pk),          # qaysi user login bo‘ldi
            action=ModelChangeLog.ActionChoices.LOGIN,   # login = create sifatida
            user=user,                       # amalni qilgan user = shu userning o'zi
            data_before=None,
            data_after={
                "event": "login",
                "username": user.username,
                "ip_address": ip,
                "user_agent": ua[:500],
            },
        )

        return response


class UserListView(APIView):

    def get(self, request):
        user = request.user
        serializer = UserListSerializer(user)
        return Response(serializer.data)



class UserView(ListCreateAPIView):
    serializer_class = UserSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = UserFilter
    search_fields = ('first_name', 'last_name', 'username', 'address', 'pinfl', 'passport_series', 'passport_number')
    ordering = ['-pk']

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)

class UserDetailView(RetrieveUpdateDestroyAPIView):

    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(User, id=pk)
        serializer = UserListPublicIdSerializer(instance)

        # USER BO‘YICHA LOG
        full_name = " ".join(
            x for x in [instance.last_name, instance.first_name, instance.second_name] if x
        )

        target_payload = {
            "id": instance.pk,
            # "pinfl": instance.pinfl,
            "full_name": full_name,
            "document_series": instance.passport_series,
            "document_number": instance.passport_number,
            # "region_id": instance.region_id,
            # "district_id": instance.district_id,
            # "mahalla_id": instance.mahalla_id,
            # "educational_institution_id": instance.educational_institution_id,
        }
        log_model_view(
            request,
            app_label="users",
            model_name="User",
            object_id=instance.pk,
            # target_obj=instance,
            extra=target_payload,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, *args, **kwargs):
        partial = kwargs.pop('partial', request.method == 'PATCH')

        instance = get_object_or_404(User, id=pk)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)

        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    # DRF 'update'ga yo'naltiramiz
    def put(self, request, pk, *args, **kwargs):
        kwargs['partial'] = False
        return self.update(request, pk, *args, **kwargs)

    def patch(self, request, pk, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, pk, *args, **kwargs)

    def delete(self, request, pk):
        instance = get_object_or_404(User, id=pk)
        instance.delete()

        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    http_method_names = ['put']

    def update(self, request):
        user = self.request.user
        serializer = self.serializer_class(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response({"message": "Your password has been changed successfully"}, status.HTTP_202_ACCEPTED)
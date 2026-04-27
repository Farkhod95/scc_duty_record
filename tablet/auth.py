import base64
import logging
import secrets

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

from django.conf import settings

logger = logging.getLogger(__name__)


def _load_private_key():
    pem = settings.TABLET_RSA_PRIVATE_KEY
    if not pem:
        return None
    return serialization.load_pem_private_key(pem.encode(), password=None)


class TabletAuthView(APIView):
    """
    POST /api/v1/tablet/auth/
    Body: {"encrypted_pinfl": "<base64 encoded RSA-OAEP ciphertext>"}
    Response: {"access": "...", "refresh": "..."}

    Yangi login bo'lganda eski sessiya o'chiriladi — eski tokenlar yaroqsiz bo'ladi.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        encrypted_b64 = request.data.get('encrypted_pinfl', '').strip()
        if not encrypted_b64:
            return Response(
                {'detail': 'encrypted_pinfl maydoni majburiy.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        private_key = _load_private_key()
        if private_key is None:
            return Response(
                {'detail': 'RSA kalit sozlanmagan.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            ciphertext = base64.b64decode(encrypted_b64)
            pinfl = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            ).decode('utf-8').strip()
        except Exception:
            logger.warning("TabletAuth: PINFL deshifrlash xatosi")
            return Response(
                {'detail': "Shifrlangan ma'lumot noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(pinfl=pinfl, is_active=True)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Foydalanuvchi topilmadi yoki faol emas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Yangi sessiya yaratish — eski avtomatik o'chadi (OneToOne)
        session_key = secrets.token_hex(32)
        from tablet.models import TabletSession
        TabletSession.objects.update_or_create(
            user=user,
            defaults={'session_key': session_key, 'created_at': timezone.now()},
        )

        refresh = RefreshToken.for_user(user)
        # Session key tokenga embed qilinadi — bu bilan eski tokenlar yaroqsiz bo'ladi
        refresh['tablet_session_key'] = session_key

        logger.info("TabletAuth: user=%s yangi sessiya yaratildi", user.id)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class IsTabletSessionValid(IsAuthenticated):
    """
    JWT dagi tablet_session_key DB dagi bilan mos kelishini tekshiradi.
    Sessiya yaroqsiz bo'lsa 401 qaytaradi — planshet avtomatik logout qiladi.
    """

    def has_permission(self, request, view):
        from rest_framework.exceptions import AuthenticationFailed

        if not super().has_permission(request, view):
            return False

        payload = getattr(request.auth, 'payload', None)
        if payload is None:
            raise AuthenticationFailed('Sessiya yaroqsiz. Qayta kiring.')

        token_session_key = payload.get('tablet_session_key')
        if not token_session_key:
            raise AuthenticationFailed('Sessiya yaroqsiz. Qayta kiring.')

        from tablet.models import TabletSession
        try:
            session = TabletSession.objects.get(user=request.user)
        except TabletSession.DoesNotExist:
            raise AuthenticationFailed('Sessiya yaroqsiz. Qayta kiring.')

        if session.session_key != token_session_key:
            raise AuthenticationFailed('Sessiya boshqa qurilmada ochilgan. Qayta kiring.')

        return True

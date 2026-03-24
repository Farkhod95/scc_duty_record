import base64
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

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

    Planshet tomonida shifrlash (Python misol):
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes, serialization
        import base64

        public_key = serialization.load_pem_public_key(public_pem.encode())
        ciphertext = public_key.encrypt(
            pinfl.encode(),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        encrypted_pinfl = base64.b64encode(ciphertext).decode()
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

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

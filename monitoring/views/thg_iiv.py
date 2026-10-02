"""
THG → IIV integratsiyasi: xarita qatlamlari uchun proxy endpointlar.

GET /api/v1/integrations/iiv/references/regions/
GET /api/v1/integrations/iiv/references/districts/   ?region_id=
GET /api/v1/integrations/iiv/references/tqm/         ?region_id= &district_id=
GET /api/v1/integrations/iiv/red-points/             ?region_id= &district_id= &tqm_id=
GET /api/v1/integrations/iiv/tqm-zones/              ?region_id= &district_id= &tqm_id=
GET /api/v1/integrations/iiv/patrol-routes/          ?region_id= &district_id= &tqm_id=
GET /api/v1/integrations/iiv/ppx/areas/              ?region_id= &district_id=
GET /api/v1/integrations/iiv/ppx/red-points/         ?region_id= &district_id=
GET /api/v1/integrations/iiv/active-staff/           ?region_id= &district_id= &tqm_id=

region_id / district_id / tqm_id — THG tizimidagi ID lar (references/* dan olinadi).
?refresh=true — keshni chetlab o'tadi.
API key frontendga chiqmaydi, THG javobi o'zgarishsiz qaytariladi.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.services.thg_iiv_client import fetch, ThgIivError, ThgIivNotConfigured


class ThgIivProxyView(APIView):
    """GET /api/v1/integrations/iiv/<resource>/"""
    permission_classes = [IsAuthenticated]
    resource = None

    def get(self, request):
        use_cache = request.query_params.get('refresh', '').lower() != 'true'
        try:
            data = fetch(self.resource, request.query_params, use_cache=use_cache)
        except ThgIivNotConfigured as e:
            return Response({'detail': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ThgIivError as e:
            return Response(
                {'detail': str(e), 'upstream_status': e.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(data)

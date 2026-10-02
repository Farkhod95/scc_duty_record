"""
THG → IIV xarita pull API klienti.

Manba: docs/IIV.postman_collection.json
Auth: x-api-key headeri (THG_IIV_API_KEY).

Resurslar:
  regions, districts, tqm          — ma'lumotnomalar
  red-points, tqm-zones,
  patrol-routes                    — xarita qatlamlari
  ppx-areas, ppx-red-points        — PPX
  active-staff                     — hozirgi smenadagi xodimlar + GPS
"""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

API_PREFIX = '/api/v1/integrations/iiv'

# resurs → (path, ruxsat etilgan query paramlar, kesh turi)
RESOURCES = {
    'regions':        ('/references/regions',   (),                                      'reference'),
    'districts':      ('/references/districts', ('region_id',),                          'reference'),
    'tqm':            ('/references/tqm',       ('region_id', 'district_id'),            'reference'),
    'red-points':     ('/red-points',           ('region_id', 'district_id', 'tqm_id'),  'layer'),
    'tqm-zones':      ('/tqm-zones',            ('region_id', 'district_id', 'tqm_id'),  'layer'),
    'patrol-routes':  ('/patrol-routes',        ('region_id', 'district_id', 'tqm_id'),  'layer'),
    'ppx-areas':      ('/ppx/areas',            ('region_id', 'district_id'),            'layer'),
    'ppx-red-points': ('/ppx/red-points',       ('region_id', 'district_id'),            'layer'),
    'active-staff':   ('/active-staff',         ('region_id', 'district_id', 'tqm_id'),  'live'),
}


class ThgIivError(Exception):
    """THG API ga so'rov muvaffaqiyatsiz tugadi."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ThgIivNotConfigured(ThgIivError):
    """THG_IIV_BASE_URL yoki THG_IIV_API_KEY sozlanmagan."""


def _cache_ttl(kind):
    return {
        'reference': settings.THG_IIV_REFERENCE_CACHE_TTL,
        'layer': settings.THG_IIV_LAYER_CACHE_TTL,
        'live': settings.THG_IIV_LIVE_CACHE_TTL,
    }[kind]


def fetch(resource, params=None, use_cache=True):
    """
    THG API dan resursni oladi va JSON (dict/list) qaytaradi.
    Noma'lum query paramlar tashlab yuboriladi.
    Xatolikda ThgIivError ko'taradi.
    """
    path, allowed, kind = RESOURCES[resource]

    base_url = (getattr(settings, 'THG_IIV_BASE_URL', '') or '').rstrip('/')
    # .env da base URL /api/v1 bilan berilgan bo'lishi mumkin — prefiks ikki marta qo'shilmasin
    if base_url.endswith('/api/v1'):
        base_url = base_url[:-len('/api/v1')]
    api_key = getattr(settings, 'THG_IIV_API_KEY', '')
    if not base_url or not api_key:
        raise ThgIivNotConfigured("THG_IIV_BASE_URL / THG_IIV_API_KEY sozlanmagan.")

    query = {
        k: str(params[k]) for k in allowed
        if params and params.get(k) not in (None, '')
    }
    url = f'{base_url}{API_PREFIX}{path}'
    if query:
        url = f'{url}?{urllib.parse.urlencode(query)}'

    ttl = _cache_ttl(kind)
    cache_key = 'thg_iiv:' + resource + ':' + urllib.parse.urlencode(sorted(query.items()))
    if use_cache and ttl > 0:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    req = urllib.request.Request(
        url,
        headers={'x-api-key': api_key, 'Accept': 'application/json'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.THG_IIV_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        logger.error("THG IIV %s HTTP xato: %s %s", resource, e.code, e.reason)
        raise ThgIivError(f'THG API xato qaytardi: {e.code} {e.reason}', status_code=e.code)
    except urllib.error.URLError as e:
        logger.error("THG IIV %s URL xato: %s", resource, e.reason)
        raise ThgIivError(f'THG API ga ulanib bo\'lmadi: {e.reason}')
    except (ValueError, TimeoutError, OSError) as e:
        logger.error("THG IIV %s kutilmagan xato: %s", resource, e)
        raise ThgIivError(f'THG API javobini o\'qib bo\'lmadi: {e}')

    if ttl > 0:
        cache.set(cache_key, data, ttl)
    return data

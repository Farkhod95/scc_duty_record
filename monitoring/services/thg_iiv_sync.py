"""
THG → IIV poligon qatlamlarini Location modeliga sinxronlash.

Location ga tushadigan qatlamlar (hammasi GeoJSON Polygon):
  tqm-zones      → source='thg_tqm_zone'
  patrol-routes  → source='thg_patrol_route'
  ppx-areas      → source='thg_ppx_area'

Qayta ishga tushirilsa (source, external_id) bo'yicha yangilanadi, dublikat yaratilmaydi.
THG da o'chirilgan yozuvlar bizda o'chirilmaydi (navbatchilikka biriktirilgan bo'lishi mumkin).
"""
import logging

from directory.models import Location
from monitoring.services.microservice import send_location_sync
from monitoring.services.thg_iiv_client import fetch

logger = logging.getLogger(__name__)


def _name(obj):
    """{'oz':..,'ru':..,'uz':..} dan lotincha nomni oladi."""
    if not obj:
        return ''
    return (obj.get('uz') or obj.get('oz') or obj.get('ru') or '').strip()


def _tqm_zone_title(item):
    return f"{_name(item.get('tqm'))} — {_name(item.get('main_or_additional'))} zona №{item['id']}"


def _patrol_route_title(item):
    return f"{_name(item.get('name')) or '№%s' % item['id']} — patrul marshruti ({_name(item.get('tqm'))})"


def _ppx_area_title(item):
    return f"{_name(item.get('service_type'))} — {_name(item.get('stage'))} №{item['id']}"


# qatlam → (Location.source, title yasovchi)
LAYERS = {
    'tqm-zones':     ('thg_tqm_zone',     _tqm_zone_title),
    'patrol-routes': ('thg_patrol_route', _patrol_route_title),
    'ppx-areas':     ('thg_ppx_area',     _ppx_area_title),
}


def sync_locations(organization, thg_district_id, layers=None, dry_run=False, push_grpc=True):
    """
    THG tumanidagi poligonlarni berilgan tashkilotning Location lariga yozadi.
    Location.region / district tashkilotnikidan olinadi.

    Qaytaradi: {qatlam: {'fetched', 'created', 'updated', 'unchanged', 'skipped'}}
    """
    stats = {}
    for layer in layers or LAYERS:
        source, make_title = LAYERS[layer]
        items = fetch(layer, {'district_id': thg_district_id}, use_cache=False).get('data') or []
        s = stats[layer] = {'fetched': len(items), 'created': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0}

        existing = {
            loc.external_id: loc
            for loc in Location.objects.filter(source=source, external_id__in=[i['id'] for i in items])
        }

        for item in items:
            geometry = item.get('geometry')
            if not geometry or geometry.get('type') != 'Polygon' or not geometry.get('coordinates'):
                s['skipped'] += 1
                continue

            fields = {
                'title': make_title(item)[:255],
                'boundary_data': geometry,
                'organization': organization,
                'region_id': organization.region_id,
                'district_id': organization.district_id,
            }

            loc = existing.get(item['id'])
            if loc is None:
                s['created'] += 1
                if dry_run:
                    continue
                loc = Location.objects.create(source=source, external_id=item['id'], **fields)
            else:
                changed = [k for k, v in fields.items() if getattr(loc, k) != v]
                if not changed:
                    s['unchanged'] += 1
                    continue
                s['updated'] += 1
                if dry_run:
                    continue
                for k in changed:
                    setattr(loc, k, fields[k])
                loc.save()

            if push_grpc:
                send_location_sync(loc)

        logger.info("THG sync %s (thg_district=%s, org=%s): %s", layer, thg_district_id, organization.pk, s)
    return stats

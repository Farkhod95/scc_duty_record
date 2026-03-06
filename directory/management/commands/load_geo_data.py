"""
python manage.py load_geo_data

data/ papkasidagi viloyat.geojson, Tuman.geojson, mahalla.geojson fayllarini
Region, District, Mahalla modellariga yuklaydi.
boundary_data ga har bir featurening geometry qismi saqlanadi.

Bog'lanish:
  Region   <- region_cad_id
  District <- region_cad_id (Region) + district_cad_id (o'z kaliti)
  Mahalla  <- region_cad_id (Region) + district_cad_id[:5] (District)
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from directory.models import Region, District, Mahalla

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Command(BaseCommand):
    help = 'GeoJSON fayllardan Region, District, Mahalla yuklaydi'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            choices=['region', 'district', 'mahalla'],
            help='Faqat bitta model yuklash',
        )

    def handle(self, *args, **options):
        only = options.get('only')

        if only in (None, 'region'):
            self._load_regions()
        if only in (None, 'district'):
            self._load_districts()
        if only in (None, 'mahalla'):
            self._load_mahallas()

        self.stdout.write(self.style.SUCCESS('Yuklash yakunlandi.'))

    # ──────────────────────────────────────────────────────────────────────────

    def _load_regions(self):
        self.stdout.write('Region (viloyat) yuklanmoqda...')
        data = _load_json('viloyat.geojson')
        created = updated = 0

        for feature in data['features']:
            props = feature['properties']
            cad_id = str(props['region_cad_id'])
            name = props['region_name']
            geometry = feature.get('geometry')

            _, is_created = Region.objects.update_or_create(
                code=cad_id,
                defaults={
                    'name': name,
                    'boundary_data': geometry,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(f'  Region: {created} yaratildi, {updated} yangilandi')

    def _load_districts(self):
        self.stdout.write('District (tuman) yuklanmoqda...')
        data = _load_json('Tuman.geojson')

        # region_cad_id → Region pk xaritasi
        region_map = {r.code: r for r in Region.objects.all()}

        created = updated = skipped = 0

        for feature in data['features']:
            props = feature['properties']
            cad_id = str(props['district_cad_id'])   # "11:15"
            name = props['district']
            soato = str(props['code'])
            region_cad_id = str(props['region_cad_id'])
            geometry = feature.get('geometry')

            region = region_map.get(region_cad_id)
            if region is None:
                self.stdout.write(
                    self.style.WARNING(f"  Region topilmadi: {region_cad_id} ({name})")
                )
                skipped += 1
                continue

            _, is_created = District.objects.update_or_create(
                code=soato,
                defaults={
                    'name': name,
                    'region': region,
                    'boundary_data': geometry,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            f'  District: {created} yaratildi, {updated} yangilandi, {skipped} o\'tkazib yuborildi'
        )

    def _load_mahallas(self):
        self.stdout.write('Mahalla yuklanmoqda...')
        data = _load_json('mahalla.geojson')

        region_map = {r.code: r for r in Region.objects.all()}

        # District: district_cad_id "11:15" formatida qidirish uchun
        # Mahalla da district_cad_id "11:15:00" — birinchi 2 segment ishlatiladi
        # District.code (soato) yoki district_cad_id bilan match qilish kerak
        # Tuman.geojson da district_cad_id "11:15" — shuning uchun map shu kalitda
        district_cad_map = {}
        for d in District.objects.select_related('region').all():
            # District.code = soato (masalan 1727259), lekin district_cad_id yo'q modelda
            # Shuning uchun Tuman.geojson dan ham o'qib map tuzamiz
            pass

        # district_cad_id ni Tuman.geojson dan o'qib District bilan solishtirish:
        # District.code (soato string) → District object
        soato_district_map = {d.code: d for d in District.objects.all()}

        # Tuman.geojson dan district_cad_id → soato xaritasi
        tuman_data = _load_json('Tuman.geojson')
        cad_to_soato = {}
        for feature in tuman_data['features']:
            p = feature['properties']
            cad_to_soato[str(p['district_cad_id'])] = str(p['code'])

        created = updated = skipped = 0
        total = len(data['features'])

        for i, feature in enumerate(data['features'], 1):
            if i % 1000 == 0:
                self.stdout.write(f'  {i}/{total}...')

            props = feature['properties']
            mahalla_id = str(props['mahalla_id'])
            name = props['mahalla_nomi']
            region_cad_id = str(props['region_cad_id'])
            district_cad_id_full = str(props['district_cad_id'])  # "23:17:00"
            geometry = feature.get('geometry')

            # "23:17:00" → "23:17"
            parts = district_cad_id_full.split(':')
            district_cad_id = ':'.join(parts[:2])

            region = region_map.get(region_cad_id)
            soato = cad_to_soato.get(district_cad_id)
            district = soato_district_map.get(soato) if soato else None

            if district is None:
                skipped += 1
                continue

            _, is_created = Mahalla.objects.update_or_create(
                code=mahalla_id,
                defaults={
                    'name': name,
                    'region': region,
                    'district': district,
                    'boundary_data': geometry,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            f'  Mahalla: {created} yaratildi, {updated} yangilandi, {skipped} o\'tkazib yuborildi'
        )

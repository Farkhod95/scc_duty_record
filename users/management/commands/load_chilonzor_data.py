"""
Chilonzor tumani PPX xodimlarini data/chilonzor_data.xlsx faylidan bazaga yuklaydi.

Ishlatish:
    python manage.py load_chilonzor_data --org-id 5
    python manage.py load_chilonzor_data --org-id 5 --dry-run
    python manage.py load_chilonzor_data --org-id 5 --update
"""
import re
from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


# ── Kirill → Lotin transliteratsiya ───────────────────────────────────────────
_CYRL_PAIRS = [
    ('Шч', 'Shch'), ('шч', 'shch'),
    ('Ш',  'Sh'),   ('ш',  'sh'),
    ('Ч',  'Ch'),   ('ч',  'ch'),
    ('Ю',  'Yu'),   ('ю',  'yu'),
    ('Я',  'Ya'),   ('я',  'ya'),
    ('Ё',  'Yo'),   ('ё',  'yo'),
    ('Ц',  'Ts'),   ('ц',  'ts'),
    ('Ъ',  "'"),    ('ъ',  "'"),
    ('Ь',  "'"),    ('ь',  "'"),
    ('Ў',  "O'"),   ('ў',  "o'"),
    ('Қ',  'Q'),    ('қ',  'q'),
    ('Ғ',  "G'"),   ('ғ',  "g'"),
    ('Ҳ',  'H'),    ('ҳ',  'h'),
    ('А',  'A'),    ('а',  'a'),
    ('Б',  'B'),    ('б',  'b'),
    ('В',  'V'),    ('в',  'v'),
    ('Г',  'G'),    ('г',  'g'),
    ('Д',  'D'),    ('д',  'd'),
    ('Е',  'E'),    ('е',  'e'),
    ('Ж',  'J'),    ('ж',  'j'),
    ('З',  'Z'),    ('з',  'z'),
    ('И',  'I'),    ('и',  'i'),
    ('Й',  'Y'),    ('й',  'y'),
    ('К',  'K'),    ('к',  'k'),
    ('Л',  'L'),    ('л',  'l'),
    ('М',  'M'),    ('м',  'm'),
    ('Н',  'N'),    ('н',  'n'),
    ('О',  'O'),    ('о',  'o'),
    ('П',  'P'),    ('п',  'p'),
    ('Р',  'R'),    ('р',  'r'),
    ('С',  'S'),    ('с',  's'),
    ('Т',  'T'),    ('т',  't'),
    ('У',  'U'),    ('у',  'u'),
    ('Ф',  'F'),    ('ф',  'f'),
    ('Х',  'X'),    ('х',  'x'),
    ('Ы',  'I'),    ('ы',  'i'),
    ('Э',  'E'),    ('э',  'e'),
]

def _to_latin(text):
    """Kirill Uzbek → Lotin Uzbek."""
    if not text:
        return text
    for cyrl, lat in _CYRL_PAIRS:
        text = text.replace(cyrl, lat)
    return text


# ── Yordamchi funksiyalar ──────────────────────────────────────────────────────

def _excel_date(serial):
    try:
        return (datetime(1899, 12, 30) + timedelta(days=int(float(serial)))).date()
    except (ValueError, TypeError):
        return None


def _parse_passport(raw):
    """'AD2336060' / 'AD-2231412' / 'AB 3565186' → (series, number)"""
    clean = re.sub(r'[\s\-]', '', raw.strip())
    m = re.match(r'^([A-Za-z]{2})(\d+)$', clean)
    if m:
        return m.group(1).upper(), m.group(2)
    return clean[:2].upper() if len(clean) >= 2 else clean, clean[2:]


def _parse_jeton(raw):
    """'А-014430' → (series='А', number='014430')"""
    raw = raw.strip()
    parts = re.split(r'[-\s]', raw, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return '', raw


def _parse_fio(raw):
    """'Усманов Иззаттилла Джамолидинович' → (last, first, second)"""
    parts = raw.strip().split()
    return (
        parts[0] if len(parts) > 0 else '',
        parts[1] if len(parts) > 1 else '',
        parts[2] if len(parts) > 2 else '',
    )


def _normalize_rank(raw):
    mapping = {
        'подполковник':    'Подполковник',
        'майор':           'Майор',
        'капитан':         'Капитан',
        'катта лейтенант': 'Катта лейтенант',
        'катта сержант':   'Катта сержант',
        'сержант':         'Сержант',
        'кичик сержант':   'Кичик сержант',
        'сафдор':          'Сафдор',
    }
    return mapping.get(raw.strip().lower(), raw.strip().title())


def _normalize_position(raw):
    mapping = {
        'жтсб бошлиги':    'ЖТСБ бошлиги',
        'отр командири':    'Отряд командири',
        'отряд командири':  'Отряд командири',
        'отр ком ў/ри':     'Отряд ком. ўринбосари',
        'гурух командири':  'Гурух командири',
        'гурух комондири':  'Гурух командири',
        'булинма командири':'Бўлинма командири',
        'бўлинма командири':'Бўлинма командири',
        'ппх инспектори':   'ППХ инспектори',
        'инспектор':        'Инспектор',
        'инспектори':       'Инспектор',
        'маб инспектор':    'МАБ инспектор',
    }
    return mapping.get(raw.strip().lower(), raw.strip())


def _normalize_dept(raw):
    raw = ' '.join(raw.strip().split())
    if 'ППХ' in raw:
        return 'ИИО ФМБ ЖТСБ ППХ'
    return 'ИИО ФМБ ЖТСБ'


def _read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    result = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        result.append({
            'dept':     str(row[1] or '').strip(),
            'fio':      str(row[2] or '').strip(),
            'pinfl':    str(row[3] or '').strip(),
            'passport': str(row[4] or '').strip(),
            'dob_raw':  row[5],
            'rank':     str(row[6] or '').strip(),
            'position': str(row[7] or '').strip(),
            'jeton':    str(row[8] or '').strip() if len(row) > 8 and row[8] else '',
            'phone':    str(row[9] or '').strip() if len(row) > 9 and row[9] else '',
        })
    wb.close()
    return result


def _set_locale_fields(obj, cyrl_name):
    """name_uz_cyrl = Kirill, name_uz = Lotin, name_ru = Kirill, name_kaa = Lotin."""
    latin = _to_latin(cyrl_name)
    obj.name         = cyrl_name
    obj.name_uz_cyrl = cyrl_name
    obj.name_uz      = latin
    obj.name_ru      = cyrl_name
    obj.name_kaa     = latin


# ── Command ────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Chilonzor PPX xodimlarini xlsx faylidan bazaga yuklaydi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-id', type=int, required=True,
            help="Xodimlar biriktirilishi kerak bo'lgan Organization ID",
        )
        parser.add_argument(
            '--file', default='data/chilonzor_data.xlsx',
            help="xlsx fayl yo'li (default: data/chilonzor_data.xlsx)",
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Bazaga yozmay tekshirish",
        )
        parser.add_argument(
            '--update', action='store_true',
            help="Mavjud foydalanuvchilarni yangilash (default: o'tkazib yuborish)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from directory.models import Organization, Department, Position, SpecialRank
        from users.models import User, Role, RoleName

        dry    = options['dry_run']
        update = options['update']
        org_id = options['org_id']

        if dry:
            self.stdout.write(self.style.WARNING("--- DRY RUN rejimi ---"))

        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f"Organization id={org_id} topilmadi.")
        self.stdout.write(f"Tashkilot: {org.name} (id={org.pk})")

        officer_role, _ = Role.objects.get_or_create(
            name=RoleName.OFFICER,
            defaults={'description': 'Officer', 'sorting': 4},
        )

        import os
        from django.conf import settings
        full_path = os.path.join(settings.BASE_DIR, options['file'])
        if not os.path.exists(full_path):
            raise CommandError(f"Fayl topilmadi: {full_path}")

        raw_rows = _read_xlsx(full_path)
        self.stdout.write(f"Faylda {len(raw_rows)} ta qator.\n")

        # ── Directory obyektlari cache ────────────────────────────────────────
        dept_cache = {}
        pos_cache  = {}
        rank_cache = {}

        def get_dept(raw_name):
            name = _normalize_dept(raw_name)
            if name not in dept_cache:
                dept, created = Department.objects.get_or_create(
                    name=name, organization=org,
                )
                if created:
                    _set_locale_fields(dept, name)
                    dept.save()
                    self.stdout.write(f"  [dept+] {name} / {_to_latin(name)}")
                dept_cache[name] = dept
            return dept_cache[name]

        def get_position(raw_name, dept):
            name = _normalize_position(raw_name)
            key  = (name, dept.pk)
            if key not in pos_cache:
                pos, created = Position.objects.get_or_create(
                    name=name, department=dept,
                )
                if created:
                    _set_locale_fields(pos, name)
                    pos.save()
                    self.stdout.write(f"  [pos+]  {name} / {_to_latin(name)}")
                pos_cache[key] = pos
            return pos_cache[key]

        def get_rank(raw_name):
            name = _normalize_rank(raw_name)
            if name not in rank_cache:
                rank, created = SpecialRank.objects.get_or_create(name=name)
                if created:
                    _set_locale_fields(rank, name)
                    rank.save()
                    self.stdout.write(f"  [rank+] {name} / {_to_latin(name)}")
                rank_cache[name] = rank
            return rank_cache[name]

        # ── Xodimlarni yaratish ───────────────────────────────────────────────
        created_count = updated_count = skipped_count = error_count = 0

        for i, row in enumerate(raw_rows, start=2):
            pinfl = re.sub(r'\D', '', row['pinfl'])
            if not pinfl:
                self.stdout.write(self.style.WARNING(f"  [{i}] PINFL yo'q, o'tkazildi"))
                skipped_count += 1
                continue

            last, first, second = _parse_fio(row['fio'])
            passport_series, passport_number = _parse_passport(row['passport'])
            jeton_series, jeton_number       = _parse_jeton(row['jeton'])
            dob   = _excel_date(row['dob_raw']) if row['dob_raw'] else None
            phone = re.sub(r'[\s\-]', '', row['phone'])
            if phone and not phone.startswith('+') and len(phone) == 9:
                phone = '+998' + phone

            exists = User.objects.filter(pinfl=pinfl).exists()

            if exists and not update:
                skipped_count += 1
                continue

            if dry:
                action = 'yangilanadi' if exists else 'yaratiladi'
                self.stdout.write(f"  [{i}] {row['fio']} ({pinfl}) — {action}")
                updated_count += 1 if exists else 0
                created_count += 0 if exists else 1
                continue

            dept     = get_dept(row['dept'])
            position = get_position(row['position'], dept)
            rank     = get_rank(row['rank'])

            try:
                if exists:
                    user = User.objects.get(pinfl=pinfl)
                    user.last_name        = last
                    user.first_name       = first
                    user.second_name      = second
                    user.organization     = org
                    user.department       = dept
                    user.position         = position
                    user.special_rank     = rank
                    user.passport_series  = passport_series
                    user.passport_number  = passport_number
                    user.date_of_birthday = dob
                    user.phone_number     = phone or ''
                    user.jeton_series     = jeton_series
                    user.jeton_number     = jeton_number
                    user.save()
                    updated_count += 1
                else:
                    user = User.objects.create(
                        username          = pinfl,
                        password          = make_password(pinfl),
                        last_name         = last,
                        first_name        = first,
                        second_name       = second,
                        pinfl             = pinfl,
                        organization      = org,
                        department        = dept,
                        position          = position,
                        special_rank      = rank,
                        passport_series   = passport_series,
                        passport_number   = passport_number,
                        date_of_birthday  = dob,
                        phone_number      = phone or '',
                        jeton_series      = jeton_series,
                        jeton_number      = jeton_number,
                        is_active         = True,
                    )
                    user.roles.add(officer_role)
                    created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [{i}] XATO — {row['fio']}: {e}"))
                error_count += 1

        # ── Natija ────────────────────────────────────────────────────────────
        if dry:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING(
                f"\nDRY RUN: yaratiladi={created_count}, yangilanadi={updated_count}, "
                f"o'tkaziladi={skipped_count}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nYakunlandi: yaratildi={created_count}, yangilandi={updated_count}, "
                f"o'tkazildi={skipped_count}, xato={error_count}"
            ))

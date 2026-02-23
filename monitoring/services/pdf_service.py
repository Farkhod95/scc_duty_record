import html
import io
import os
import qrcode

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font registration ---
_font_registered = False


def _register_fonts():
    global _font_registered
    if _font_registered:
        return
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    bold_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
        _font_registered = True


def _get_font_name(bold=False):
    _register_fonts()
    if _font_registered:
        return 'DejaVuSans-Bold' if bold else 'DejaVuSans'
    return 'Helvetica-Bold' if bold else 'Helvetica'


# --- Styles ---

def _get_styles():
    font = _get_font_name()
    font_bold = _get_font_name(bold=True)

    return {
        'title': ParagraphStyle(
            'PDFTitle', fontName=font_bold, fontSize=11,
            leading=14, alignment=1, spaceAfter=2 * mm,
        ),
        'center': ParagraphStyle(
            'PDFCenter', fontName=font, fontSize=10,
            leading=14, alignment=1,
        ),
        'right': ParagraphStyle(
            'PDFRight', fontName=font, fontSize=10,
            leading=16, alignment=2,
        ),
        'right_bold': ParagraphStyle(
            'PDFRightBold', fontName=font_bold, fontSize=10,
            leading=16, alignment=2,
        ),
        'header': ParagraphStyle(
            'PDFHeader', fontName=font_bold, fontSize=8,
            leading=10, alignment=1,
        ),
        'cell': ParagraphStyle(
            'PDFCell', fontName=font, fontSize=8, leading=10,
        ),
        'cell_center': ParagraphStyle(
            'PDFCellCenter', fontName=font, fontSize=8,
            leading=10, alignment=1,
        ),
        'cell_bold': ParagraphStyle(
            'PDFCellBold', fontName=font_bold, fontSize=8, leading=10,
        ),
        'qr_name': ParagraphStyle(
            'QRName', fontName=font_bold, fontSize=9,
            leading=12, alignment=1,
        ),
        'qr_position': ParagraphStyle(
            'QRPosition', fontName=font, fontSize=8,
            leading=10, alignment=1,
            textColor=colors.HexColor('#555555'),
        ),
        'qr_label': ParagraphStyle(
            'QRLabel', fontName=font, fontSize=8,
            leading=10, alignment=1,
            textColor=colors.HexColor('#444444'),
        ),
    }


# --- QR code generation ---

def _make_qr_image(data, size=3 * cm):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=size, height=size)


def _get_base_url():
    return getattr(settings, 'BASE_URL', 'http://localhost:8000').rstrip('/')


def _get_user_rank_name(user):
    """Unvon + F.I.O. ko'rinishida qaytaradi."""
    rank = ''
    if user.special_rank:
        rank = user.special_rank.name or ''
    full_name = user.get_full_name()
    return f"{rank} {full_name}".strip() if rank else full_name


def _get_user_position(user):
    if user.position:
        return user.position.name or ''
    return ''


def _build_qr_block(user, label, styles, qr_size=3 * cm):
    """QR code + label + ism, unvon bloki."""
    base_url = _get_base_url()
    qr_url = f"{base_url}/api/v1/qr/{user.id}/"
    qr_img = _make_qr_image(qr_url, size=qr_size)

    rank_name = html.escape(_get_user_rank_name(user))
    position_name = html.escape(_get_user_position(user))

    cell_data = [
        [Paragraph(html.escape(label), styles['qr_label'])],
        [qr_img],
        [Paragraph(rank_name, styles['qr_name'])],
    ]
    if position_name:
        cell_data.append([Paragraph(position_name, styles['qr_position'])])

    block = Table(cell_data, colWidths=[7 * cm])
    block.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return block


# --- Main PDF generator ---

def generate_main_duty_pdf(main_duty):
    """
    MainDuty uchun rasmiy PDF hisobot yaratish.

    Format:
      - O'ng tomonda «TASDIQLAYMAN» bloki (tasdiqlagan shaxs ma'lumotlari)
      - Markazda hujjat sarlavhasi va tavsif matni
      - Jadval: # | Vazifa | Turi | Hudud | Vaqt | Xodimlar | Transport | Telefon
      - Pastda: 2 ta QR code (yuboruvchi + tasdiqlagan)
    """
    from monitoring.models import DutyFile

    styles = _get_styles()
    local_tz = timezone.get_current_timezone()

    # Prefetch all data
    tasks = main_duty.tasks.select_related(
        'location__region', 'location__district',
    ).prefetch_related(
        'assignments__employee__special_rank',
        'assignments__employee__position',
        'assignments__transport__type',
    ).order_by('id')

    # --- Build PDF ---
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1 * cm,
    )

    story = []

    # ─── «TASDIQLAYMAN» bloki (o'ng tomonda) ───
    approved_by = main_duty.approved_by
    sent_by = main_duty.created_by

    tasdiq_lines = [Paragraph('«T A S D I Q L A Y M A N»', styles['right_bold'])]

    org_name = main_duty.organization.name if main_duty.organization else ''
    if org_name:
        tasdiq_lines.append(Paragraph(html.escape(org_name), styles['right']))

    if approved_by:
        position_name = _get_user_position(approved_by)
        rank_name = _get_user_rank_name(approved_by)
        if position_name:
            tasdiq_lines.append(Paragraph(html.escape(position_name), styles['right']))
        tasdiq_lines.append(Spacer(1, 0.4 * cm))
        tasdiq_lines.append(Paragraph(html.escape(rank_name), styles['right']))
    else:
        tasdiq_lines.append(Spacer(1, 0.4 * cm))
        tasdiq_lines.append(Paragraph('___________________', styles['right']))

    if main_duty.approved_at:
        approved_date = main_duty.approved_at.astimezone(local_tz)
        day = approved_date.strftime('%d')
        month = approved_date.strftime('%B')
        year = approved_date.strftime('%Y')
        tasdiq_lines.append(Spacer(1, 0.3 * cm))
        tasdiq_lines.append(Paragraph(f'{year} yil « {day} » {month}', styles['right']))
    elif main_duty.duty_date:
        day = main_duty.duty_date.strftime('%d')
        month = main_duty.duty_date.strftime('%B')
        year = main_duty.duty_date.strftime('%Y')
        tasdiq_lines.append(Spacer(1, 0.3 * cm))
        tasdiq_lines.append(Paragraph(f'{year} yil « {day} » {month}', styles['right']))

    for line in tasdiq_lines:
        story.append(line)

    story.append(Spacer(1, 0.8 * cm))

    # ─── Hujjat sarlavha matni ───
    duty_date_str = main_duty.duty_date.strftime('%d.%m.%Y') if main_duty.duty_date else ''
    start_str = main_duty.start_time.astimezone(local_tz).strftime('%H:%M') if main_duty.start_time else ''
    end_str = main_duty.end_time.astimezone(local_tz).strftime('%H:%M') if main_duty.end_time else ''

    intro_text = (
        f"{duty_date_str} kuni {html.escape(org_name)} hududida jamoat tartibini saqlash "
        f"maqsadida xizmatga jalb qilingan kuch va vositalar taqsimoti "
        f"({start_str} - {end_str}) yuzasidan."
    )
    story.append(Paragraph(intro_text, styles['center']))
    story.append(Spacer(1, 0.5 * cm))

    # ─── Asosiy jadval sarlavhasi ───
    story.append(Paragraph(html.escape(main_duty.title), styles['title']))
    story.append(Spacer(1, 0.4 * cm))

    # ===================== TABLE =====================
    headers = [
        Paragraph('<b>#</b>', styles['header']),
        Paragraph('<b>Vazifa</b>', styles['header']),
        Paragraph('<b>Turi</b>', styles['header']),
        Paragraph('<b>Hudud</b>', styles['header']),
        Paragraph('<b>Vaqt</b>', styles['header']),
        Paragraph('<b>Xodimlar</b>', styles['header']),
        Paragraph('<b>Transport</b>', styles['header']),
        Paragraph('<b>Telefon</b>', styles['header']),
    ]

    data = [headers]

    for row_num, task in enumerate(tasks, start=1):
        assignments = list(task.assignments.all())

        task_title = html.escape(task.title or '')
        task_type_display = html.escape(task.get_task_type_display())

        # Location
        location_parts = []
        if task.location:
            location_parts.append(task.location.title or '')
            if task.location.district:
                location_parts.append(task.location.district.name or '')
            if task.location.region:
                location_parts.append(task.location.region.name or '')
        location_str = html.escape(', '.join(filter(None, location_parts)))

        # Time
        task_start = task.start_time.astimezone(local_tz).strftime('%H:%M') if task.start_time else ''
        task_end = task.end_time.astimezone(local_tz).strftime('%H:%M') if task.end_time else ''
        time_str = f"{task_start} - {task_end}" if (task_start or task_end) else ''

        employee_lines, transport_lines, phone_lines = [], [], []

        for assignment in assignments:
            emp = assignment.employee
            rank_name = html.escape(_get_user_rank_name(emp))
            position_name = html.escape(_get_user_position(emp))

            emp_text = rank_name
            if position_name:
                emp_text = f"{emp_text} ({position_name})"
            if assignment.role_in_transport == 'DRIVER':
                emp_text = f"{emp_text} [Haydovchi]"
            employee_lines.append(emp_text)

            t = assignment.transport
            if t:
                t_info = html.escape(t.name_or_code or t.model or '')
                if t.plate_number:
                    t_info = f"{t_info} ({html.escape(t.plate_number)})"
                elif t.number:
                    t_info = f"{t_info} ({html.escape(t.number)})"
                t_type = html.escape(t.type.name if t.type else '')
                transport_lines.append(f"{t_type}: {t_info}" if t_type else t_info)
            else:
                transport_lines.append('—')

            phone_lines.append(html.escape(emp.phone_number or '—'))

        employees_text = '<br/>'.join(employee_lines) if employee_lines else '—'
        transport_text = '<br/>'.join(transport_lines) if transport_lines else '—'
        phone_text = '<br/>'.join(phone_lines) if phone_lines else '—'

        row = [
            Paragraph(str(row_num), styles['cell_center']),
            Paragraph(task_title, styles['cell_bold']),
            Paragraph(task_type_display, styles['cell_center']),
            Paragraph(location_str, styles['cell']),
            Paragraph(time_str, styles['cell_center']),
            Paragraph(employees_text, styles['cell']),
            Paragraph(transport_text, styles['cell']),
            Paragraph(phone_text, styles['cell']),
        ]
        data.append(row)

    # Column widths (landscape A4 ~ 25.7cm usable with 2cm margins each side)
    col_widths = [
        1 * cm,    # #
        4.5 * cm,  # Vazifa
        2 * cm,    # Turi
        3.5 * cm,  # Hudud
        2.5 * cm,  # Vaqt
        6 * cm,    # Xodimlar
        3.7 * cm,  # Transport
        2.5 * cm,  # Telefon
    ]

    table = Table(data, colWidths=col_widths, repeatRows=1)

    table_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d0d0d0')),
        ('FONTNAME', (0, 0), (-1, 0), _get_font_name(bold=True)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]

    # Alternate row colors (namunaga mos: f5f5f5 juft qatorlar)
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style_commands.append(
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5'))
            )

    table.setStyle(TableStyle(table_style_commands))
    story.append(table)

    # ===================== QR CODES (pastda) =====================
    story.append(Spacer(1, 1 * cm))

    qr_cells = []

    # Chap: Yuboruvchi (created_by / sent_by)
    if sent_by:
        qr_cells.append(_build_qr_block(sent_by, 'Navbatchilikni tuzgan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))

    # O'rta: bo'sh joy
    qr_cells.append(Spacer(1, 1))

    # O'ng: Tasdiqlagan (approved_by)
    if approved_by:
        qr_cells.append(_build_qr_block(approved_by, 'Tasdiqlagan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))

    # Landscape A4 usable width ~ 25.7cm, 2 qr block 7cm each, middle filler
    qr_table = Table(
        [qr_cells],
        colWidths=[7 * cm, 11.7 * cm, 7 * cm],
    )
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(qr_table)

    doc.build(story)

    # ===================== SAVE =====================
    pdf_content = buf.getvalue()
    buf.close()

    DutyFile.objects.filter(main_duty=main_duty, name='duty_report').delete()

    duty_file = DutyFile(
        main_duty=main_duty,
        name='duty_report',
        created_by=main_duty.approved_by or main_duty.created_by,
    )
    filename = f"duty_report_{main_duty.id}_{main_duty.duty_date}.pdf"
    duty_file.file.save(filename, ContentFile(pdf_content), save=True)

    return duty_file

"""
DutyDay va Event uchun PDF hisobot generatori.
Mavjud pdf_service.py dagi font/style yordamchi funksiyalarini ishlatadi.
"""
import html
import io

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from monitoring.services.pdf_service import (
    _get_styles, _get_font_name, _build_qr_block,
)


def _time_str(dt):
    if not dt:
        return ''
    local_tz = timezone.get_current_timezone()
    return dt.astimezone(local_tz).strftime('%H:%M')


def _date_str(d):
    return d.strftime('%d.%m.%Y') if d else ''


# ─────────────────────────────────────────────────────────────────────────────
# DutyDay PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_duty_day_pdf(duty_day) -> bytes:
    """
    DutyDay uchun rasmiy PDF hisobot (bytes) qaytaradi.

    Format:
      - «TASDIQLAYMAN» bloki (o'ng, approved_by)
      - Sarlavha: org nomi + sana
      - Har bir DutySection uchun: section sarlavhasi + jadval
        Jadval: # | Mahalla | F.I.O + Unvon | Lavozim | Transport | Rol | Telefon
      - Pastda: QR (submitted_by + approved_by)
    """
    styles = _get_styles()
    local_tz = timezone.get_current_timezone()

    sections = list(
        duty_day.sections
        .prefetch_related(
            'assignments__employee__special_rank',
            'assignments__employee__position',
            'assignments__mahalla',
            'assignments__transport__type',
        )
        .order_by('stage_number')
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1 * cm,
    )
    story = []

    # ── «TASDIQLAYMAN» ───────────────────────────────────────────────────────
    approved_by = duty_day.approved_by
    org_name = duty_day.organization.name if duty_day.organization else ''

    tasdiq = [Paragraph('«T A S D I Q L A Y M A N»', styles['right_bold'])]
    if org_name:
        tasdiq.append(Paragraph(html.escape(org_name), styles['right']))

    if approved_by:
        from monitoring.services.pdf_service import _get_user_position, _get_user_rank_name
        pos = _get_user_position(approved_by)
        name = _get_user_rank_name(approved_by)
        if pos:
            tasdiq.append(Paragraph(html.escape(pos), styles['right']))
        tasdiq.append(Spacer(1, 0.4 * cm))
        tasdiq.append(Paragraph(html.escape(name), styles['right']))
    else:
        tasdiq.append(Spacer(1, 0.4 * cm))
        tasdiq.append(Paragraph('___________________', styles['right']))

    ref_date = duty_day.approved_at or duty_day.duty_date
    if ref_date:
        d = ref_date.astimezone(local_tz) if hasattr(ref_date, 'astimezone') else ref_date
        tasdiq.append(Spacer(1, 0.3 * cm))
        tasdiq.append(Paragraph(
            f'{d.strftime("%Y")} yil « {d.strftime("%d")} » {d.strftime("%B")}',
            styles['right']
        ))

    for line in tasdiq:
        story.append(line)
    story.append(Spacer(1, 0.8 * cm))

    # ── Sarlavha ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"{html.escape(org_name)} — {_date_str(duty_day.duty_date)} kungi navbatchilik",
        styles['title']
    ))
    story.append(Spacer(1, 0.5 * cm))

    # ── Har bir bosqich ───────────────────────────────────────────────────────
    col_widths = [
        0.8 * cm,   # #
        3.5 * cm,   # Mahalla
        4.5 * cm,   # F.I.O + unvon
        3 * cm,     # Lavozim
        3.5 * cm,   # Transport
        2 * cm,     # Rol
        2.5 * cm,   # Telefon
    ]

    headers = [
        Paragraph('<b>#</b>', styles['header']),
        Paragraph('<b>Mahalla</b>', styles['header']),
        Paragraph('<b>F.I.O / Unvon</b>', styles['header']),
        Paragraph('<b>Lavozim</b>', styles['header']),
        Paragraph('<b>Transport</b>', styles['header']),
        Paragraph('<b>Rol</b>', styles['header']),
        Paragraph('<b>Telefon</b>', styles['header']),
    ]

    for section in sections:
        start = _time_str(section.start_time)
        end = _time_str(section.end_time)
        time_range = f" ({start} – {end})" if (start or end) else ''
        story.append(Paragraph(
            f"<b>{html.escape(section.name)}{time_range}</b>",
            styles['cell_bold']
        ))
        story.append(Spacer(1, 2 * mm))

        data = [headers[:]]
        assignments = list(section.assignments.all())

        if not assignments:
            data.append([
                Paragraph('—', styles['cell_center']),
                Paragraph('Tayinlanmagan', styles['cell']),
                *[Paragraph('', styles['cell'])] * 5,
            ])
        else:
            from monitoring.services.pdf_service import _get_user_rank_name, _get_user_position
            for i, a in enumerate(assignments, start=1):
                emp = a.employee
                mahalla_name = html.escape(a.mahalla.name if a.mahalla else '—')
                rank_name = html.escape(_get_user_rank_name(emp))
                position_name = html.escape(_get_user_position(emp))

                transport_text = '—'
                if a.transport:
                    t = a.transport
                    t_code = html.escape(t.name_or_code or t.model or '')
                    t_num = t.plate_number or t.number or ''
                    t_type = html.escape(t.type.name if t.type else '')
                    transport_text = f"{t_type}: {t_code}"
                    if t_num:
                        transport_text += f" ({html.escape(t_num)})"

                role_map = {'DRIVER': 'Haydovchi', 'PASSENGER': 'Yo\'lovchi', 'NONE': '—'}
                role_text = role_map.get(a.role_in_transport, '—')

                data.append([
                    Paragraph(str(i), styles['cell_center']),
                    Paragraph(mahalla_name, styles['cell']),
                    Paragraph(rank_name, styles['cell_bold']),
                    Paragraph(position_name, styles['cell']),
                    Paragraph(transport_text, styles['cell']),
                    Paragraph(role_text, styles['cell_center']),
                    Paragraph(html.escape(emp.phone_number or '—'), styles['cell']),
                ])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d0d0d0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]
        for row_i in range(1, len(data)):
            if row_i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), colors.HexColor('#f5f5f5')))
        table.setStyle(TableStyle(style_cmds))
        story.append(table)
        story.append(Spacer(1, 0.5 * cm))

    # ── QR bloklar ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    sent_by = duty_day.submitted_by or duty_day.created_by
    qr_cells = []
    if sent_by:
        qr_cells.append(_build_qr_block(sent_by, 'Navbatchilikni tuzgan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))
    qr_cells.append(Spacer(1, 1))
    if approved_by:
        qr_cells.append(_build_qr_block(approved_by, 'Tasdiqlagan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))

    qr_table = Table([qr_cells], colWidths=[7 * cm, 11.7 * cm, 7 * cm])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(qr_table)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Event PDF
# ─────────────────────────────────────────────────────────────────────────────

def generate_event_pdf(event) -> bytes:
    """Event uchun PDF hisobot (bytes) qaytaradi."""
    from monitoring.services.pdf_service import _get_user_rank_name, _get_user_position

    styles = _get_styles()
    local_tz = timezone.get_current_timezone()

    assignments = list(
        event.assignments
        .select_related(
            'employee__special_rank', 'employee__position',
            'transport__type',
        )
        .order_by('id')
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1 * cm,
    )
    story = []

    # ── «TASDIQLAYMAN» ───────────────────────────────────────────────────────
    approved_by = event.approved_by
    org_name = event.organization.name if event.organization else ''

    tasdiq = [Paragraph('«T A S D I Q L A Y M A N»', styles['right_bold'])]
    if org_name:
        tasdiq.append(Paragraph(html.escape(org_name), styles['right']))

    if approved_by:
        pos = _get_user_position(approved_by)
        name = _get_user_rank_name(approved_by)
        if pos:
            tasdiq.append(Paragraph(html.escape(pos), styles['right']))
        tasdiq.append(Spacer(1, 0.4 * cm))
        tasdiq.append(Paragraph(html.escape(name), styles['right']))
    else:
        tasdiq.append(Spacer(1, 0.4 * cm))
        tasdiq.append(Paragraph('___________________', styles['right']))

    ref_date = event.approved_at or event.event_date
    if ref_date:
        d = ref_date.astimezone(local_tz) if hasattr(ref_date, 'astimezone') else ref_date
        tasdiq.append(Spacer(1, 0.3 * cm))
        tasdiq.append(Paragraph(
            f'{d.strftime("%Y")} yil « {d.strftime("%d")} » {d.strftime("%B")}',
            styles['right']
        ))

    for line in tasdiq:
        story.append(line)
    story.append(Spacer(1, 0.8 * cm))

    # ── Sarlavha ─────────────────────────────────────────────────────────────
    mahalla_name = event.mahalla.name if event.mahalla else ''
    start = _time_str(event.start_time)
    end = _time_str(event.end_time)

    story.append(Paragraph(html.escape(event.title), styles['title']))
    meta = f"{html.escape(org_name)} | {_date_str(event.event_date)} | {start} – {end}"
    if mahalla_name:
        meta += f" | {html.escape(mahalla_name)}"
    story.append(Paragraph(meta, styles['center']))
    if event.description:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(html.escape(event.description), styles['cell']))
    story.append(Spacer(1, 0.5 * cm))

    # ── Jadval ───────────────────────────────────────────────────────────────
    col_widths = [0.8 * cm, 5 * cm, 4 * cm, 4 * cm, 2.5 * cm, 3 * cm]
    headers = [
        Paragraph('<b>#</b>', styles['header']),
        Paragraph('<b>F.I.O / Unvon</b>', styles['header']),
        Paragraph('<b>Lavozim</b>', styles['header']),
        Paragraph('<b>Transport</b>', styles['header']),
        Paragraph('<b>Rol</b>', styles['header']),
        Paragraph('<b>Telefon</b>', styles['header']),
    ]
    data = [headers]

    if not assignments:
        data.append([Paragraph('—', styles['cell_center'])] + [Paragraph('', styles['cell'])] * 5)
    else:
        role_map = {'DRIVER': 'Haydovchi', 'PASSENGER': "Yo'lovchi", 'NONE': '—'}
        for i, a in enumerate(assignments, start=1):
            emp = a.employee
            transport_text = '—'
            if a.transport:
                t = a.transport
                t_code = html.escape(t.name_or_code or t.model or '')
                t_num = t.plate_number or t.number or ''
                t_type = html.escape(t.type.name if t.type else '')
                transport_text = f"{t_type}: {t_code}" if t_type else t_code
                if t_num:
                    transport_text += f" ({html.escape(t_num)})"

            data.append([
                Paragraph(str(i), styles['cell_center']),
                Paragraph(html.escape(_get_user_rank_name(emp)), styles['cell_bold']),
                Paragraph(html.escape(_get_user_position(emp)), styles['cell']),
                Paragraph(transport_text, styles['cell']),
                Paragraph(role_map.get(a.role_in_transport, '—'), styles['cell_center']),
                Paragraph(html.escape(emp.phone_number or '—'), styles['cell']),
            ])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d0d0d0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    for row_i in range(1, len(data)):
        if row_i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), colors.HexColor('#f5f5f5')))
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    # ── QR ───────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    sent_by = event.submitted_by or event.created_by
    qr_cells = []
    if sent_by:
        qr_cells.append(_build_qr_block(sent_by, 'Tadbirni tuzgan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))
    qr_cells.append(Spacer(1, 1))
    if approved_by:
        qr_cells.append(_build_qr_block(approved_by, 'Tasdiqlagan', styles))
    else:
        qr_cells.append(Paragraph('', styles['cell']))

    qr_table = Table([qr_cells], colWidths=[7 * cm, 11.7 * cm, 7 * cm])
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(qr_table)

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

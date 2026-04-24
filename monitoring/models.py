from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from restapp.models import BaseModel

User = get_user_model()


# --- TextChoices ---

class MainDutyStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    SENT_FOR_APPROVAL = 'SENT_FOR_APPROVAL', _('Sent for approval')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')


class TaskType(models.TextChoices):
    DUTY = 'DUTY', _('Duty')
    EVENT = 'EVENT', _('Event')


class RoleInTransport(models.TextChoices):
    DRIVER = 'DRIVER', _('Driver')
    PASSENGER = 'PASSENGER', _('Passenger')
    NONE = 'NONE', _('None')


class AbsenceRequestStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')


class AttendanceStatus(models.TextChoices):
    ARRIVED = 'ARRIVED', _('Arrived')
    LEFT = 'LEFT', _('Left')


class DutyDayStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Tayyorlanmoqda')
    SUBMITTED = 'SUBMITTED', _("Yuborildi")
    COLLECTED = 'COLLECTED', _("Yig'uvchi tasdiqladi")
    APPROVED = 'APPROVED', _('Tasdiqlandi')
    REJECTED = 'REJECTED', _('Rad etildi')


class RejectedAtStage(models.TextChoices):
    COLLECTOR = 'COLLECTOR', _('Collector')
    DISTRICT_ADMIN = 'DISTRICT_ADMIN', _('District Admin')


# --- Models ---

class MainDuty(BaseModel):
    organization = models.ForeignKey(
        'directory.Organization', on_delete=models.CASCADE,
        related_name='main_duties', help_text=_("Navbatchilik tegishli tashkilot")
    )
    title = models.CharField(
        _('Title'), max_length=255, help_text=_("Navbatchilik nomi")
    )
    duty_date = models.DateField(
        _('Duty date'), help_text=_("Navbatchilik sanasi")
    )
    start_time = models.DateTimeField(
        _('Start time'), help_text=_("Boshlanish vaqti")
    )
    end_time = models.DateTimeField(
        _('End time'), help_text=_("Tugash vaqti")
    )
    status = models.CharField(
        _('Status'), max_length=30,
        choices=MainDutyStatus.choices, default=MainDutyStatus.DRAFT,
        help_text=_("Navbatchilik holati")
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_main_duties', help_text=_("Kim tasdiqladi")
    )
    approved_at = models.DateTimeField(
        _('Approved at'), null=True, blank=True,
        help_text=_("Tasdiqlangan vaqt")
    )
    rejection_reason = models.TextField(
        _('Rejection reason'), null=True, blank=True,
        help_text=_("Rad etish sababi")
    )

    class Meta:
        verbose_name = _("Main duty")
        verbose_name_plural = _("Main duties")
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['duty_date']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': _("Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")
            })


class Task(BaseModel):
    main_duty = models.ForeignKey(
        MainDuty, on_delete=models.CASCADE,
        related_name='tasks', help_text=_("Qaysi navbatchilikka tegishli")
    )
    title = models.CharField(
        _('Title'), max_length=255, help_text=_("Vazifa nomi")
    )
    task_type = models.CharField(
        _('Task type'), max_length=20,
        choices=TaskType.choices, default=TaskType.DUTY,
        help_text=_("Vazifa turi")
    )
    start_time = models.DateTimeField(
        _('Start time'), null=True, blank=True,
        help_text=_("Boshlanish vaqti")
    )
    end_time = models.DateTimeField(
        _('End time'), null=True, blank=True,
        help_text=_("Tugash vaqti")
    )
    location = models.ForeignKey(
        'directory.Location', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', help_text=_("Joy/hudud")
    )
    description = models.TextField(
        _('Description'), null=True, blank=True,
        help_text=_("Vazifa tavsifi")
    )

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ['id']
        indexes = [
            models.Index(fields=['main_duty', 'task_type']),
            models.Index(fields=['task_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_task_type_display()})"


class TaskAssignment(BaseModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='assignments', help_text=_("Qaysi vazifa")
    )
    employee = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='task_assignments', help_text=_("Tayinlangan xodim")
    )
    transport = models.ForeignKey(
        'fleet.Transport', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='task_assignments', help_text=_("Transport vositasi")
    )
    role_in_transport = models.CharField(
        _('Role in transport'), max_length=20,
        choices=RoleInTransport.choices, default=RoleInTransport.NONE,
        help_text=_("Transportdagi roli")
    )
    note = models.TextField(
        _('Note'), null=True, blank=True,
        help_text=_("Izoh")
    )

    class Meta:
        verbose_name = _("Task assignment")
        verbose_name_plural = _("Task assignments")
        ordering = ['id']
        unique_together = [['task', 'employee']]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.task.title}"

    def clean(self):
        super().clean()
        main_duty = self.task.main_duty
        if self.employee.organization_id != main_duty.organization_id:
            raise ValidationError({
                'employee': _("Xodim navbatchilik tashkilotiga tegishli bo'lishi kerak.")
            })
        if self.transport and self.transport.organization_id != main_duty.organization_id:
            raise ValidationError({
                'transport': _("Transport navbatchilik tashkilotiga tegishli bo'lishi kerak.")
            })


class AbsenceRequest(BaseModel):
    task_assignment = models.OneToOneField(
        TaskAssignment, on_delete=models.CASCADE,
        related_name='absence_request', help_text=_("Qaysi tayinlash uchun")
    )
    reason = models.TextField(
        _('Reason'), help_text=_("Kela olmaslik sababi")
    )
    file = models.FileField(
        _('File'), upload_to='absence_requests/%Y/%m/%d/',
        null=True, blank=True, help_text=_("Sabab hujjati")
    )
    status = models.CharField(
        _('Status'), max_length=20,
        choices=AbsenceRequestStatus.choices, default=AbsenceRequestStatus.PENDING,
        help_text=_("So'rov holati")
    )
    replacement_employee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='replacement_assignments', help_text=_("O'rinbosar xodim")
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_absence_requests', help_text=_("Kim ko'rib chiqdi")
    )
    reviewed_at = models.DateTimeField(
        _('Reviewed at'), null=True, blank=True, help_text=_("Ko'rib chiqilgan vaqt")
    )
    review_note = models.TextField(
        _('Review note'), null=True, blank=True, help_text=_("Izoh")
    )

    class Meta:
        verbose_name = _("Absence request")
        verbose_name_plural = _("Absence requests")
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.task_assignment} - {self.get_status_display()}"


class DutyFile(BaseModel):
    main_duty = models.ForeignKey(
        MainDuty, on_delete=models.CASCADE, null=True, blank=True,
        related_name='files', help_text=_("Qaysi navbatchilik uchun")
    )
    file = models.FileField(
        _('File'), upload_to='duties/%Y/%m/%d/',
        help_text=_("Fayl")
    )
    name = models.CharField(
        _('Name'), max_length=255, null=True, blank=True,
        help_text=_("Fayl nomi")
    )

    class Meta:
        verbose_name = _("Duty file")
        verbose_name_plural = _("Duty files")
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.name or self.file.name}"


class EmployeeAttendance(BaseModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='attendances', help_text=_("Qaysi vazifa")
    )
    employee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances', help_text=_("Topilgan xodim (pinfl mos bo'lsa)")
    )
    pinfl_hash_received = models.CharField(
        _('Received PINFL hash'), max_length=64,
        help_text=_("Tashqi tizimdan kelgan SHA256 PINFL")
    )
    is_verified = models.BooleanField(
        _('Verified'), default=False,
        help_text=_("PINFL bizning bazamizdagi bilan mos keldi")
    )
    status = models.CharField(
        _('Status'), max_length=10,
        choices=AttendanceStatus.choices,
        help_text=_("Keldi yoki ketdi")
    )
    event_datetime = models.DateTimeField(
        _('Event datetime'), help_text=_("Hodisa vaqti")
    )
    location = models.JSONField(
        _('Location'), null=True, blank=True,
        help_text=_('GPS koordinatalari: {"lat": 41.123, "lon": 69.456}')
    )
    photo = models.ImageField(
        _('Photo'), upload_to='attendances/photos/%Y/%m/%d/',
        null=True, blank=True,
        help_text=_("Xodim rasmi (base64 dan dekod qilingan)")
    )

    class Meta:
        verbose_name = _("Employee attendance")
        verbose_name_plural = _("Employee attendances")
        ordering = ['-event_datetime']
        indexes = [
            models.Index(fields=['task', 'status']),
            models.Index(fields=['pinfl_hash_received']),
            models.Index(fields=['event_datetime']),
        ]

    def __str__(self):
        emp = self.employee.get_full_name() if self.employee else self.pinfl_hash_received[:8]
        return f"{emp} — {self.get_status_display()} ({self.event_datetime})"


class DailyDutyOfficer(BaseModel):
    organization = models.ForeignKey(
        'directory.Organization', on_delete=models.CASCADE,
        related_name='daily_duty_officers', help_text=_("Qaysi tashkilot")
    )
    officer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='duty_officer_assignments', help_text=_("Tayinlangan dijur admin")
    )
    duty_date = models.DateField(
        _('Duty date'), help_text=_("Qaysi kun uchun")
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_duty_officers', help_text=_("Kim tayinladi (Manager)")
    )
    note = models.TextField(
        _('Note'), null=True, blank=True,
        help_text=_("Izoh")
    )

    class Meta:
        verbose_name = _("Daily duty officer")
        verbose_name_plural = _("Daily duty officers")
        ordering = ['-duty_date']
        unique_together = [['organization', 'duty_date']]
        indexes = [
            models.Index(fields=['organization', 'duty_date']),
        ]

    def __str__(self):
        return f"{self.officer.get_full_name()} - {self.duty_date}"

    def clean(self):
        super().clean()
        if self.officer and self.organization:
            if self.officer.organization_id != self.organization_id:
                raise ValidationError({
                    'officer': _("Dijur admin tashkilotga tegishli bo'lishi kerak.")
                })

# ============================================================
# Etap 2 — Yangi navbatchilik arxitekturasi
# ============================================================

class DutyDay(BaseModel):
    """
    Bir tashkilotning bir kundagi navbatchiligi.
    Bir tashkilot — bir kun — bitta DutyDay (unique_together).
    """
    organization = models.ForeignKey(
        'directory.Organization', on_delete=models.CASCADE,
        related_name='duty_days', help_text=_("Tashkilot")
    )
    duty_date = models.DateField(_('Duty date'), help_text=_("Navbatchilik sanasi"))
    status = models.CharField(
        _('Status'), max_length=20,
        choices=DutyDayStatus.choices, default=DutyDayStatus.DRAFT
    )

    # OFFICER tomonidan yuborilishi
    submitted_at = models.DateTimeField(_('Submitted at'), null=True, blank=True)
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submitted_duty_days'
    )

    # COLLECTOR (yig'uvchi) tasdiqlashi
    collected_at = models.DateTimeField(_('Collected at'), null=True, blank=True)
    collected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collected_duty_days'
    )

    # DISTRICT_ADMIN yakuniy tasdiqlashi
    approved_at = models.DateTimeField(_('Approved at'), null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_duty_days'
    )

    # Rad etish
    rejected_at = models.DateTimeField(_('Rejected at'), null=True, blank=True)
    rejected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rejected_duty_days'
    )
    rejection_reason = models.TextField(_('Rejection reason'), null=True, blank=True)
    rejected_at_stage = models.CharField(
        _('Rejected at stage'), max_length=20,
        choices=RejectedAtStage.choices, null=True, blank=True
    )

    class Meta:
        verbose_name = _('Duty day')
        verbose_name_plural = _('Duty days')
        unique_together = [['organization', 'duty_date']]
        ordering = ['-duty_date']
        indexes = [
            models.Index(fields=['organization', 'duty_date']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.organization.name} — {self.duty_date} ({self.get_status_display()})"


class DutySection(BaseModel):
    """
    DutyDay ichidagi bitta bosqich (shift).
    Masalan: 1-bosqich (08:00-20:00), 2-bosqich (20:00-08:00).
    """
    duty_day = models.ForeignKey(
        DutyDay, on_delete=models.CASCADE,
        related_name='sections', help_text=_("Qaysi navbatchilik kuni")
    )
    stage_number = models.PositiveIntegerField(
        _('Stage number'), help_text=_("Bosqich tartib raqami (1, 2, 3...)")
    )
    name = models.CharField(_('Name'), max_length=100, help_text=_("Bosqich nomi"))
    start_time = models.DateTimeField(_('Start time'), null=True, blank=True)
    end_time = models.DateTimeField(_('End time'), null=True, blank=True)

    class Meta:
        verbose_name = _('Duty section')
        verbose_name_plural = _('Duty sections')
        unique_together = [['duty_day', 'stage_number']]
        ordering = ['stage_number']

    def __str__(self):
        return f"{self.duty_day} — {self.name}"


class DutySectionAssignment(BaseModel):
    """
    Bitta bosqich uchun xodimlar + location + transportlar biriktirilishi.
    """
    duty_section = models.ForeignKey(
        DutySection, on_delete=models.CASCADE,
        related_name='assignments', help_text=_("Qaysi bosqich")
    )
    employees = models.ManyToManyField(
        User, blank=True,
        related_name='duty_section_assignments', help_text=_("Navbatchi xodimlar")
    )
    location = models.ForeignKey(
        'directory.Location', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='duty_section_assignments', help_text=_("Navbatchilik joyi (location)")
    )
    transports = models.ManyToManyField(
        'fleet.Transport', blank=True,
        related_name='duty_section_assignments', help_text=_("Transport vositalari")
    )
    note = models.TextField(_('Note'), null=True, blank=True)

    class Meta:
        verbose_name = _('Duty section assignment')
        verbose_name_plural = _('Duty section assignments')
        ordering = ['id']

    def __str__(self):
        return f"Assignment #{self.pk} — {self.duty_section.name}"


# ============================================================
# Etap 5 — Tadbir (Event)
# ============================================================

class Event(BaseModel):
    """
    Bir martalik tadbir. Bosqichlarsiz — faqat vaqt, xodimlar va transport.
    Xuddi DutyDay kabi 3 bosqichli tasdiqlash zanjiri bor.
    """
    organization = models.ForeignKey(
        'directory.Organization', on_delete=models.CASCADE,
        related_name='events', help_text=_("Tashkilot")
    )
    title = models.CharField(_('Title'), max_length=255, help_text=_("Tadbir nomi"))
    event_date = models.DateField(_('Event date'), help_text=_("Tadbir sanasi"))
    start_time = models.DateTimeField(_('Start time'), help_text=_("Boshlanish vaqti"))
    end_time = models.DateTimeField(_('End time'), help_text=_("Tugash vaqti"))
    description = models.TextField(_('Description'), null=True, blank=True)
    status = models.CharField(
        _('Status'), max_length=20,
        choices=DutyDayStatus.choices, default=DutyDayStatus.DRAFT
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submitted_events'
    )
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='collected_events'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_events'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rejected_events'
    )
    rejection_reason = models.TextField(null=True, blank=True)
    rejected_at_stage = models.CharField(
        max_length=20, choices=RejectedAtStage.choices, null=True, blank=True
    )

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        ordering = ['-event_date', '-start_time']
        indexes = [
            models.Index(fields=['organization', 'event_date']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['status']),
        ]

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            from django.core.exceptions import ValidationError
            raise ValidationError({'end_time': _("Tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak.")})

    def __str__(self):
        return f"{self.title} — {self.event_date} ({self.get_status_display()})"


class EventAssignment(BaseModel):
    """Tadbir uchun xodimlar + mahallalar + transportlar biriktirilishi."""
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE,
        related_name='assignments', help_text=_("Qaysi tadbir")
    )
    employees = models.ManyToManyField(
        User, blank=True,
        related_name='event_assignments', help_text=_("Tayinlangan xodimlar")
    )
    mahallas = models.ManyToManyField(
        'directory.Mahalla', blank=True,
        related_name='event_assignments', help_text=_("Navbatchilik hududlari (mahalla)")
    )
    transports = models.ManyToManyField(
        'fleet.Transport', blank=True,
        related_name='event_assignments', help_text=_("Transport vositalari")
    )
    note = models.TextField(_('Note'), null=True, blank=True)

    class Meta:
        verbose_name = _('Event assignment')
        verbose_name_plural = _('Event assignments')
        ordering = ['id']

    def __str__(self):
        return f"Assignment #{self.pk} — {self.event.title}"


# ============================================================
# Hudud tark etish jurnali (Tablet API)
# ============================================================

class TerritoryExitLog(BaseModel):
    """
    Xodim o'z hududini vaqtincha tark etganda sababini qayd etadi.
    Tablet orqali yuboriladi; admin panelda ro'yxat sifatida ko'rinadi.
    """
    employee = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='territory_exit_logs', help_text=_("Hududni tark etgan xodim")
    )
    duty_section_assignment = models.ForeignKey(
        DutySectionAssignment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='territory_exit_logs', help_text=_("Bog'liq navbatchilik tayinlanishi (ixtiyoriy)")
    )
    reason = models.TextField(
        _('Reason'), help_text=_("Hududni tark etish sababi")
    )
    exit_time = models.DateTimeField(
        _('Exit time'), help_text=_("Hududni tark etish vaqti")
    )
    return_time = models.DateTimeField(
        _('Return time'), null=True, blank=True,
        help_text=_("Hududga qaytish vaqti (keyinchalik to'ldiriladi)")
    )

    class Meta:
        verbose_name = _('Territory exit log')
        verbose_name_plural = _('Territory exit logs')
        ordering = ['-exit_time']
        indexes = [
            models.Index(fields=['employee', 'exit_time']),
            models.Index(fields=['exit_time']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.exit_time:%Y-%m-%d %H:%M}"


# ============================================================
# 112 Hodisa (Incident) — tashqi tizimdan keladi
# ============================================================

class Incident112(BaseModel):
    """
    112 xizmatidan kelgan hodisa kartasi.
    API key orqali POST qilinadi; barcha maydonlar saqlangan.
    """
    card_number = models.CharField(
        _('Card number'), max_length=100, unique=True,
        help_text=_("112 karta raqami (card112Number)")
    )
    dt_create = models.CharField(
        _('Created timestamp'), max_length=50, null=True, blank=True,
        help_text=_("dtCreate112 — sana yoki timestamp string")
    )
    operator = models.CharField(
        _('Operator'), max_length=255, null=True, blank=True,
        help_text=_("Kartani yaratgan operator (strCreator112)")
    )
    called_phone = models.CharField(
        _('Called phone'), max_length=50,
        help_text=_("Murojaat qilingan telefon (strCdPN)")
    )
    fabula = models.TextField(_('Fabula'), null=True, blank=True)
    call_type_id = models.IntegerField(_('Call type ID'), help_text=_("nCallTypeId"))
    incident_type_id = models.IntegerField(_('Incident type ID'), help_text=_("nIncidentTypeId"))
    incident_description = models.TextField(_('Incident description'), help_text=_("strIncidentDescription"))

    # Manzil ID lari
    country_area_id = models.IntegerField(null=True, blank=True)
    district_id_112 = models.CharField(max_length=50, null=True, blank=True)
    city_id = models.IntegerField(null=True, blank=True)
    local_district_id = models.IntegerField(null=True, blank=True)
    mahallya_id = models.IntegerField(null=True, blank=True)
    street_id = models.CharField(max_length=50, null=True, blank=True)
    building = models.CharField(max_length=100, null=True, blank=True)
    entrance = models.CharField(max_length=50, null=True, blank=True)
    floor = models.IntegerField(null=True, blank=True)
    flat = models.CharField(max_length=50, null=True, blank=True)
    block = models.CharField(max_length=50, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    # Hodisa koordinatalari
    latitude = models.FloatField(_('Latitude'), null=True, blank=True)
    longitude = models.FloatField(_('Longitude'), null=True, blank=True)

    # Qo'shimcha maydonlar
    l_control = models.IntegerField(null=True, blank=True)
    dt_time_from = models.CharField(max_length=50, null=True, blank=True)
    dt_time_to = models.CharField(max_length=50, null=True, blank=True)
    addendum_id = models.IntegerField(null=True, blank=True)
    dept_id = models.IntegerField(null=True, blank=True)
    priority_id = models.IntegerField(null=True, blank=True)
    l_hospital_application = models.BooleanField(null=True, blank=True)
    first_card_id = models.IntegerField(null=True, blank=True)
    new_card = models.BooleanField(null=True, blank=True)
    appeal_type_id = models.IntegerField(null=True, blank=True)
    card_creation_area_id = models.IntegerField(null=True, blank=True)
    call_id_112 = models.CharField(max_length=100, null=True, blank=True)

    # JSON nested obyektlar
    declarant_info = models.JSONField(null=True, blank=True, help_text=_("declarantInfo"))
    victim_info = models.JSONField(null=True, blank=True, help_text=_("victimInfo"))
    traffic_collision = models.JSONField(null=True, blank=True, help_text=_("trafficCollision"))
    hospital_application_data = models.JSONField(null=True, blank=True, help_text=_("hospitalApplication"))

    # 112 tizimining o'z ID si va string tavsiflar
    incident_id_112 = models.IntegerField(
        _('Incident ID 112'), null=True, blank=True,
        help_text=_("112 tizimidagi id maydoni")
    )
    incident_type_str = models.CharField(
        _('Incident type (string)'), max_length=255, null=True, blank=True,
        help_text=_("incidentType — '229 - ЎЗБОШИМЧАЛИК' kabi string")
    )
    priority_type_str = models.CharField(
        _('Priority type (string)'), max_length=255, null=True, blank=True,
        help_text=_("priorityType — '003 - НАРЯД ЮБОРИШ' kabi string")
    )
    appeal_type = models.CharField(
        _('Appeal type'), max_length=255, null=True, blank=True,
        help_text=_("appealType — 'Система 112' kabi string")
    )
    city_name = models.CharField(
        _('City name'), max_length=255, null=True, blank=True,
        help_text=_("nCity — shahar/tuman nomi string")
    )
    database_name = models.CharField(
        _('Database name'), max_length=50, null=True, blank=True,
        help_text=_("database_name maydoni")
    )

    # To'liq payload arxivi
    raw_payload = models.JSONField(help_text=_("Tashqi tizimdan kelgan to'liq JSON"))

    class Meta:
        verbose_name = _('Incident 112')
        verbose_name_plural = _('Incidents 112')
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['incident_type_id']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['created_time']),
        ]

    def __str__(self):
        return f"112-{self.card_number} ({self.incident_description[:50]})"


class Incident112Notification(models.Model):
    """Qaysi xodimga qaysi hodisa haqida xabar yuborildi."""
    incident = models.ForeignKey(
        Incident112, on_delete=models.CASCADE,
        related_name='notifications', help_text=_("Qaysi hodisa")
    )
    employee = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='incident_notifications', help_text=_("Xabar yuborilgan xodim")
    )
    distance_km = models.FloatField(
        _('Distance km'), null=True, blank=True,
        help_text=_("Xodimdan hodisa masofasi (km)")
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Incident notification')
        verbose_name_plural = _('Incident notifications')
        unique_together = [['incident', 'employee']]
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['employee', 'is_read']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} ← {self.incident.card_number}"


# ============================================================
# Alarm log — gRPC AlarmStream voqealari
# ============================================================

class AlarmLog(models.Model):
    """
    LocationService dan kelgan alarm voqeasi.
    Xodim yoki transport hududdan chiqqanda/kirganda yoziladi.
    """
    duty_section = models.ForeignKey(
        DutySection, on_delete=models.CASCADE,
        related_name='alarm_logs', help_text=_("Qaysi navbatchilik bosqichi")
    )
    employee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alarm_logs', help_text=_("Xodim (pinfl_hash orqali topilsa)")
    )
    alarm_type = models.CharField(
        _('Alarm type'), max_length=100,
        help_text=_("Alarm turi (out_of_zone, at_point, ...)")
    )
    paligon_id = models.IntegerField(null=True, blank=True)
    point_id = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    pinfl_hash = models.CharField(max_length=64, null=True, blank=True)
    plate_number = models.CharField(max_length=20, null=True, blank=True)
    event_timestamp = models.BigIntegerField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Alarm log')
        verbose_name_plural = _('Alarm logs')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['duty_section', 'received_at']),
            models.Index(fields=['employee', 'received_at']),
            models.Index(fields=['alarm_type']),
        ]

    def __str__(self):
        subj = self.pinfl_hash or self.plate_number or '?'
        return f"[{self.alarm_type}] {subj} — {self.received_at:%H:%M:%S}"

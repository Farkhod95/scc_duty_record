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


class DutySection(BaseModel):
    main_duty = models.ForeignKey(
        MainDuty, on_delete=models.CASCADE,
        related_name='sections', help_text=_("Qaysi navbatchilikka tegishli")
    )
    name = models.CharField(
        _('Name'), max_length=255, help_text=_("Bo'lim nomi")
    )
    sort_order = models.PositiveIntegerField(
        _('Sort order'), default=0, help_text=_("Tartiblash raqami")
    )

    class Meta:
        verbose_name = _("Duty section")
        verbose_name_plural = _("Duty sections")
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['main_duty', 'sort_order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.main_duty.title})"


class Task(BaseModel):
    duty_section = models.ForeignKey(
        DutySection, on_delete=models.CASCADE,
        related_name='tasks', help_text=_("Qaysi bo'limga tegishli")
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
    location = models.CharField(
        _('Location'), max_length=500, null=True, blank=True,
        help_text=_("Joy nomi")
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
            models.Index(fields=['duty_section', 'task_type']),
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
        main_duty = self.task.duty_section.main_duty
        if self.employee.organization_id != main_duty.organization_id:
            raise ValidationError({
                'employee': _("Xodim navbatchilik tashkilotiga tegishli bo'lishi kerak.")
            })
        if self.transport and self.transport.organization_id != main_duty.organization_id:
            raise ValidationError({
                'transport': _("Transport navbatchilik tashkilotiga tegishli bo'lishi kerak.")
            })


class DutyFile(BaseModel):
    main_duty = models.ForeignKey(
        MainDuty, on_delete=models.CASCADE,
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

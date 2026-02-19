from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, GroupManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token

from directory.models import Department, Position, Organization


class CommonInfo(models.Model):
    created_time = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_time = models.DateTimeField(auto_now_add=False, auto_now=True)


class Role(Group):
    objects = GroupManager()
    description = models.CharField(max_length=255)
    sorting = models.IntegerField(blank=True, null=True, unique=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')


class User(AbstractUser):
    class GENDERS(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')

    username = models.CharField(max_length=255, unique=True, help_text=_("Foydalanuvchi nomi"))
    last_name = models.CharField(max_length=100, help_text=_("Foydalanuvchi familiyasi"))
    first_name = models.CharField(max_length=100, help_text=_("Foydalanuvchi ismi"))
    second_name = models.CharField(max_length=100, null=True, blank=True, help_text=_("Foydalanuvchi otasining ismi"))
    is_active = models.BooleanField(_('Active'), default=True, help_text=_("Foydalanuvchi holati"))
    date_of_birthday = models.DateField(_('date of birthday'), null=True, blank=True, help_text=_("Tug‘ilgan sanasi"))
    gender = models.CharField(choices=GENDERS.choices, max_length=6, null=True, blank=True, help_text=_("Jinsi"))
    phone_number = models.CharField(_("Phone number"), max_length=100, help_text=_("Telefon raqami"))
    email = models.EmailField(_('email address'), blank=True, null=True, help_text=_("Email manzili"))
    date_joined = models.DateTimeField(_('Date joined'), auto_now_add=True, help_text=_("Ro‘yxatdan o‘tgan sana"))
    password = models.CharField(max_length=255, null=True, blank=True, help_text=_("Parol"))
    organization = models.ForeignKey(Organization, related_name='user_department', on_delete=models.SET_NULL, null=True,
                                     blank=True, help_text=_("Tashkilot"))
    department = models.ForeignKey(Department, related_name='user_department', on_delete=models.SET_NULL, null=True,
                                   blank=True, help_text=_("Bo‘lim"))
    position = models.ForeignKey(Position, related_name='user_position', on_delete=models.SET_NULL, null=True,
                                 blank=True, help_text=_("Lavozim"))
    region = models.ForeignKey("directory.Region", related_name='user_region', on_delete=models.SET_NULL, null=True,
                               blank=True,
                               help_text=_("Viloyat"))
    district = models.ForeignKey("directory.District", related_name='user_district', on_delete=models.SET_NULL,
                                 null=True, blank=True, help_text=_("Tuman"))
    # role = models.ForeignKey(Role, related_name='role_user', null=True, blank=True, on_delete=models.SET_NULL,
    #                          help_text=_("Foydalanuvchi roli"))
    roles = models.ManyToManyField(Role, related_name='users', blank=True, help_text=_("Foydalanuvchi rollari"))
    address = models.TextField(_("Address"), null=True, blank=True, help_text=_("Yashash manzili"))
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("Yangilangan vaqt"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_by_user', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yaratgan foydalanuvchi"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_by_user', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yangilagan foydalanuvchi"))
    pinfl = models.CharField(_('JSHSHIR'), max_length=14, unique=True, null=True, blank=True,
                             help_text=_("Jismoniy shaxsning shaxsiy identifikatsion raqami"))
    passport_series = models.CharField(_('passport series'), max_length=10, blank=True, help_text=_("Pasport seriyasi"))
    passport_number = models.CharField(_('Full name'), max_length=20, blank=True, help_text=_("Pasport raqami"))
    passport_given_by = models.CharField(_('Full name'), max_length=255, blank=True,
                                         help_text=_("Pasport berilgan joy"))
    begin_date = models.DateField(_('date of birthday'), null=True, blank=True, help_text=_("Pasport berilgan sana"))
    end_date = models.DateField(_('date of birthday'), null=True, blank=True,
                                help_text=_("Pasport amal qilish muddati"))
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d', null=True, blank=True, help_text=_("Profil rasmi"))
    avatar_base64 = models.TextField(_("Avatar base64"), null=True, blank=True)
    client_token = models.TextField(_("Client token"), null=True, blank=True)

    jeton_series = models.CharField(_('Jeton seriyasi'), max_length=10, null=True, blank=True,
                                    help_text=_("Jeton seriyasi (masalan: A)"))
    jeton_number = models.CharField(_('Jeton raqami'), max_length=50, null=True, blank=True,
                                    help_text=_("Jeton raqami (masalan: 120268)"))
    jeton_begin_date = models.DateField(_('Berilgan sanasi'), null=True, blank=True,
                                        help_text=_("Jeton berilgan sanasi"))
    special_rank = models.ForeignKey("directory.SpecialRank", related_name='user_special_rank',
                                     on_delete=models.SET_NULL,
                                     null=True, help_text=_("Maxsus unvon"))

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['pinfl']),
            models.Index(fields=['last_name']),
            models.Index(fields=['first_name']),
            models.Index(fields=['region']),
            models.Index(fields=['district']),
        ]

    def save(self, *args, **kwargs):
        # boshqa custom mantiqingiz bo‘lsa qolsin, token Y O‘ Q
        return super().save(*args, **kwargs)

    def __str__(self):
        if self.last_name or self.first_name:
            # "Familiya Ism" ko‘rinishida
            return " ".join([x for x in [self.last_name, self.first_name] if x])
        return self.username or str(self.pk)

    def is_admin(self) -> bool:
        return self.roles.filter(name__iexact='admin').exists()

    def is_manager(self) -> bool:
        return self.roles.filter(name__iexact='manager').exists()

    def is_superadmin(self) -> bool:
        return self.roles.filter(name__iexact='superadmin').exists()

    def is_employee(self) -> bool:
        return self.roles.filter(name__iexact='employee').exists()



class UserJeton(models.Model):
    user = models.ForeignKey("users.User", related_name="jetons", on_delete=models.SET_NULL, null=True, blank=True,
                             help_text=_("Foydalanuvchi bilan bog‘lanadi"))
    name = models.CharField(_('Jeton nomi'), max_length=255, null=True, blank=True,
                            help_text=_("Jeton nomi (ixtiyoriy)"))
    jeton_series = models.CharField(_('Jeton seriyasi'), max_length=10, null=True, blank=True,
                                    help_text=_("Jeton seriyasi (masalan: A)"))
    jeton_number = models.CharField(_('Jeton raqami'), max_length=50, null=True, blank=True,
                                    help_text=_("Jeton raqami (masalan: 120268)"))
    begin_date = models.DateField(_('Berilgan sanasi'), null=True, blank=True, help_text=_("Jeton berilgan sanasi"))
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("Yangilangan vaqt"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_by_jeton', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yaratgan foydalanuvchi"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_by_jeton', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yangilagan foydalanuvchi"))

    class Meta:
        verbose_name = _('User Jeton')  # Admin panelda ko‘rinadigan nom
        verbose_name_plural = _('User Jetons')

    def __str__(self):
        return f"{self.name or ''} ({self.jeton_series or ''}-{self.jeton_number or ''})"


class AppModule(models.Model):
    name = models.CharField(_('Module name'), max_length=125, blank=True)
    on_dashboard = models.BooleanField(default=False)
    content_types = models.ManyToManyField(ContentType)
    sorting = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = _('module')
        verbose_name_plural = _('modules')

from django_filters.rest_framework import FilterSet
from django_filters import rest_framework as df

from users.models import User, UserJeton


class NumberInFilter(df.BaseInFilter, df.NumberFilter):
    """?role_ids=1,2,3 kabi ro'yxatlarni qabul qiladi"""
    pass

MIN_TERM = 2

class UserFilter(FilterSet):
    last_name = df.CharFilter(method='filter_last_name')
    first_name = df.CharFilter(method='filter_first_name')
    second_name = df.CharFilter(method='filter_second_name')
    pinfl = df.CharFilter(method='filter_pinfl')

    class Meta:
        model = User
        fields = {
            'gender': ['exact'],
            'region': ['exact'],
            'pinfl': ['exact'],
            'district': ['exact'],
            'work_region': ['exact'],
            'work_district': ['exact'],
            'jeton_number': ['exact'],
            'first_name': ['exact'],
            'last_name': ['exact'],
        }
    def filter_pinfl(self, qs, name, value):
        v = (value or '').strip()
        if not v or len(v) < MIN_TERM:
            return qs
        return qs.filter(pinfl__istartswith=v)

    def filter_second_name(self, qs, name, value):
        # faqat '%%' kelsa SKIP
        if value == '%%':
            return qs
        v = (value or '').strip()
        if not v or len(v) < MIN_TERM:
            return qs
        return qs.filter(second_name__istartswith=v.lower())

    def filter_last_name(self, qs, name, value):
        # faqat '%%' kelsa SKIP
        if value == '%%':
            return qs
        v = (value or '').strip()
        if not v or len(v) < MIN_TERM:
            return qs
        # last_name_l LIKE 'v%'
        return qs.filter(last_name__istartswith=v.lower())

    def filter_first_name(self, qs, name, value):
        if value == '%%':
            return qs
        v = (value or '').strip()
        if not v or len(v) < MIN_TERM:
            return qs
        return qs.filter(first_name__istartswith=v.lower())


class UserJetonFilter(FilterSet):
    class Meta:
        model = UserJeton
        fields = {
            'user': ['exact'],
            'name': ['icontains'],
            'jeton_series': ['exact'],
            'jeton_number': ['exact'],
            'begin_date': ['exact'],
        }
from modeltranslation.translator import register, TranslationOptions

from .models import TransportType


@register(TransportType)
class TransportTypeTranslationOptions(TranslationOptions):
    fields = ('name',)

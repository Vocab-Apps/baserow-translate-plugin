from django.db import models
from django.core.exceptions import ValidationError

from rest_framework import serializers

from django.db import models
from baserow.contrib.database.fields.registries import FieldType

from .models import TranslationField

class TranslationFieldType(FieldType):
    type = 'translation'
    model_class = TranslationField

    allowed_fields = [
        'source_field_id',
        'source_language',
        'target_language'
    ]
    serializer_field_names = [
        'source_field_id',
        'source_language',
        'target_language'
    ]    

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def get_model_field(self, instance, **kwargs):
        return models.CharField(null=True, blank=True)

from django.db import models
from django.core.exceptions import ValidationError


from rest_framework import serializers

from baserow.contrib.database.views.handler import ViewHandler
from django.db import models
from baserow.contrib.database.fields.registries import FieldType
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.dependencies.models import FieldDependency

from .models import TranslationField
from . import translation

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


    serializer_field_overrides = {
        "source_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="source_field.id",
            help_text="The id of the field to translate",
        ),
        "source_language": serializers.CharField(
            required=True,
            allow_null=False,
            allow_blank=False
        ),
        "target_language": serializers.CharField(
            required=True,
            allow_null=False,
            allow_blank=False
        ),        
    }    

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return serializers.CharField(
            **{
                "required": required,
                "allow_null": not required,
                "allow_blank": not required,
                "default": None,
                **kwargs,
            }
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(
            default=None, blank=True, null=True, **kwargs
        )
    
    def get_field_dependencies(self, field_instance: Field, field_lookup_cache: FieldCache):
        if field_instance.source_field != None:
            return [
                FieldDependency(
                    dependency=field_instance.source_field,
                    dependant=field_instance
                )
            ]     
        return [] 

    def row_of_dependency_updated(
        self,
        field,
        starting_row,
        update_collector,
        field_cache: "FieldCache",
        via_path_to_starting_table,
    ):


        source_internal_field_name = f'field_{field.source_field.id}'
        target_internal_field_name = f'field_{field.id}'
        source_language = field.source_language
        target_language = field.target_language

        if isinstance(starting_row, list):
            row_list = starting_row
        else:
            row_list = [starting_row]

        rows_to_bulk_update = []
        for row in row_list:
            source_value = getattr(row, source_internal_field_name)
            translated_value = translation.translate(source_value, source_language, target_language)
            setattr(row, target_internal_field_name, translated_value)
            rows_to_bulk_update.append(row)

        model = field.table.get_model()
        model.objects.bulk_update(rows_to_bulk_update, fields=[field.db_column])

        ViewHandler().field_value_updated(field)     
        super().row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )        
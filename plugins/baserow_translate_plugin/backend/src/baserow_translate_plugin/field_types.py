import re
from typing import Dict, Any, Optional, List

from baserow.contrib.database.fields.deferred_field_fk_updater import \
    DeferredFieldFkUpdater
from baserow.contrib.database.formula import BaserowFormulaType, BaserowFormulaTextType
from django.db import models
from django.core.exceptions import ValidationError

from rest_framework import serializers

from baserow.contrib.database.views.handler import ViewHandler
from django.db import models
from baserow.contrib.database.fields.registries import FieldType
from baserow.contrib.database.fields.models import Field, TextField, LinkRowField
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.dependencies.models import FieldDependency
from baserow.contrib.database.fields.field_filters import (
    contains_filter,
    contains_word_filter,
)
from baserow.contrib.database.table.models import TableModelQuerySet

from .models import TranslationField, ChatGPTField
from . import translation


class TranslationFieldType(FieldType):
    type = 'translation'
    model_class = TranslationField

    # I went through the default properties and had some ideas etc, in the future
    # should be moved to some sort of "So you want to make a new FieldType" doc! :)

    # First of all, I don't think users are ever allowed to directly edit the
    # translation field cells I think? Like the formula field etc. So i've set read_only
    # to True:
    read_only = True

    # Given we are read only, then probably not allowed in a form
    can_be_in_form_view = False

    # This one is interesting. I've not changed it from the default but added it here
    # to point it out / discuss.
    #
    # When this is false, and you edit the field and say change it's type or settings,
    # the undo redo system will create a duplicate postgres column and back up all
    # of the fields original data into it. THis is so, you can undo the field settings
    # change and get all your data back.
    #
    # Now we could set this to True, because we can re-create all of the fields
    # column data from just the old settings, just like the formula field for example.
    # However perhaps i'm not thinking its worth taking this trade off, as recomputing
    # all of the translated values after pressing undo sounds a ton slower than just
    # copying from another postgres column.
    field_data_is_derived_from_attrs = False

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

    def get_field_dependencies(self, field_instance: Field,
                               field_lookup_cache: FieldCache):
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

        # Minor change, can use this property to get the internal/db column name
        source_internal_field_name = field.source_field.db_column
        target_internal_field_name = field.db_column
        source_language = field.source_language
        target_language = field.target_language

        # Would be nice if instead Baserow did this for you before calling this func!
        # Not suggesting you do anything, but instead the Baserow project itself should
        # have a nicer API here :)

        if isinstance(starting_row, TableModelQuerySet):
            # if starting_row is TableModelQuerySet (when creating multiple rows in a batch), we want to iterate over its TableModel objects
            row_list = starting_row
        elif isinstance(starting_row, list):
            # if we have a list, it's a list of TableModels, iterate over them
            row_list = starting_row            
        else:
            # we got a single TableModel, transform it into a list of one element
            row_list = [starting_row]

        rows_to_bulk_update = []
        for row in row_list:
            source_value = getattr(row, source_internal_field_name)
            translated_value = translation.translate(source_value, source_language,
                                                     target_language)
            setattr(row, target_internal_field_name, translated_value)
            rows_to_bulk_update.append(row)

        model = field.table.get_model()
        model.objects.bulk_update(rows_to_bulk_update,
                                  fields=[target_internal_field_name])

        ViewHandler().field_value_updated(field)
        super().row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def after_create(self, field, model, user, connection, before, field_kwargs):
        self.update_all_rows(field)

    def after_update(
            self,
            from_field,
            to_field,
            from_model,
            to_model,
            user,
            connection,
            altered_column,
            before,
            to_field_kwargs
    ):
        self.update_all_rows(to_field)

    def update_all_rows(self, field):
        source_internal_field_name = field.source_field.db_column
        target_internal_field_name = field.db_column

        source_language = field.source_language
        target_language = field.target_language

        table_id = field.table.id

        translation.translate_all_rows(table_id, source_internal_field_name,
                                       target_internal_field_name,
                                       source_language,
                                       target_language)

    # Used by some of our helper scripts
    def random_value(self, instance, fake, cache):
        return fake.name()

    # Lets this field type work with the contains view filter
    def contains_query(self, *args):
        return contains_filter(*args)

    # Lets this field type work with the contains word view filter
    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    # Lets this field type be referenced (and treated like it is text) by the formula
    # field:
    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaTextType(nullable=True)

    def from_baserow_formula_type(
            self, formula_type: BaserowFormulaTextType
    ) -> TextField:
        # Pretend to be a text field from the formula systems perspective
        return TextField()

    # Baserow supports serializing all data and metadata in a workspace/database/table
    # to a JSON format.  We use this for templates/duplication etc.
    #
    # This import/export process completely remakes all the metadata in the
    # new duplicated table/db/workspace. This means all the PKs will be brand new,
    # so for the TranslateFieldType the source_field_id PK which will have been exported
    # will no longer point to the correct PK in the new duplicated table.
    #
    # To solve this, we can just use the deferred_fk_update_collector which will
    # wait until all fields have been remade with their new Pks, and then apply the
    # mapping from old PK to new PK for us so things remain consistant in the new
    # duplicated table.
    def import_serialized(
            self,
            table: "Table",
            serialized_values: Dict[str, Any],
            id_mapping: Dict[str, Any],
            deferred_fk_update_collector: DeferredFieldFkUpdater,
    ) -> "Field":
        serialized_copy = serialized_values.copy()
        # We have to temporarily remove the `source_field_id`, because it can be
        # that they haven't been created yet, which prevents us from finding it in
        # the mapping.
        original_source_field_id = serialized_copy.pop("source_field_id")
        field = super().import_serialized(
            table, serialized_copy, id_mapping, deferred_fk_update_collector
        )
        deferred_fk_update_collector.add_deferred_fk_to_update(
            field, "source_field_id", original_source_field_id
        )
        return field

    # So you already correctly update when rows/cell this field depends on change which
    # is great.
    # However, we also need to override this hook as if the source field we depend on
    # is updated (think we convert a text field to a formula field, any time a field
    # itself is editted it might re-compute all of its values).
    def field_dependency_updated(
            self,
            field: TranslationField,
            updated_field: Field,
            updated_old_field: Field,
            update_collector: "FieldUpdateCollector",
            field_cache: "FieldCache",
            via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self.update_all_rows(field)

        super().field_dependency_updated(
            field,
            updated_field,
            updated_old_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )



class ChatGPTFieldType(FieldType):
    type = 'chatgpt'
    model_class = ChatGPTField

    # the field can be edited
    read_only = False

    # will be displayed in form view
    can_be_in_form_view = True

    field_data_is_derived_from_attrs = False

    allowed_fields = [
        'prompt'
    ]
    serializer_field_names = [
        'prompt'
    ]

    serializer_field_overrides = {
        "prompt": serializers.CharField(
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

    def get_fields_in_prompt(self, prompt):
        fields_to_expand = re.findall(r'{(.*?)}', prompt)
        return fields_to_expand

    def get_field_dependencies(self, field_instance: Field,
                               field_lookup_cache: FieldCache):
        if field_instance.prompt != None:
            # need to parse the prompt to find the fields it depends on
            fields_to_expand = self.get_fields_in_prompt(field_instance.prompt)
            result = []
            for field_name in fields_to_expand:
                # for each field that we found in the prompt, add a dependency
                result.append(
                    FieldDependency(
                        dependency=field_lookup_cache.lookup_by_name(field_instance.table, field_name),
                        dependant=field_instance
                    )
                )   
            return result
        return []

    def row_of_dependency_updated(
            self,
            field,
            starting_row,
            update_collector,
            field_cache: "FieldCache",
            via_path_to_starting_table,
    ):

        prompt_template = field.prompt
        fields_to_expand = self.get_fields_in_prompt(prompt_template)
        # need to expand the variables inside prompt_template
        target_internal_field_name = field.db_column

        if isinstance(starting_row, TableModelQuerySet):
            # if starting_row is TableModelQuerySet (when creating multiple rows in a batch), we want to iterate over its TableModel objects
            row_list = starting_row
        elif isinstance(starting_row, list):
            # if we have a list, it's a list of TableModels, iterate over them
            row_list = starting_row            
        else:
            # we got a single TableModel, transform it into a list of one element
            row_list = [starting_row]

        rows_to_bulk_update = []
        for row in row_list:
            # fully expand the prompt
            expanded_prompt = prompt_template
            for field_name in fields_to_expand:
                internal_field_name = field_cache.lookup_by_name(field.table, field_name).db_column
                field_value = getattr(row, internal_field_name)
                # now, replace inside the prompt
                expanded_prompt = expanded_prompt.replace('{' + field_name + '}', field_value)
            # call chatgpt API
            translated_value = translation.chatgpt(expanded_prompt)
            setattr(row, target_internal_field_name, translated_value)
            rows_to_bulk_update.append(row)

        model = field.table.get_model()
        model.objects.bulk_update(rows_to_bulk_update,
                                  fields=[target_internal_field_name])

        ViewHandler().field_value_updated(field)
        super().row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def after_create(self, field, model, user, connection, before, field_kwargs):
        self.update_all_rows(field)

    def after_update(
            self,
            from_field,
            to_field,
            from_model,
            to_model,
            user,
            connection,
            altered_column,
            before,
            to_field_kwargs
    ):
        self.update_all_rows(to_field)

    def update_all_rows(self, field):
        # not implemented yet
        return

        source_internal_field_name = field.source_field.db_column
        target_internal_field_name = field.db_column

        source_language = field.source_language
        target_language = field.target_language

        table_id = field.table.id

        translation.translate_all_rows(table_id, source_internal_field_name,
                                       target_internal_field_name,
                                       source_language,
                                       target_language)

    # Used by some of our helper scripts
    def random_value(self, instance, fake, cache):
        return fake.name()

    # Lets this field type work with the contains view filter
    def contains_query(self, *args):
        return contains_filter(*args)

    # Lets this field type work with the contains word view filter
    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    # Lets this field type be referenced (and treated like it is text) by the formula
    # field:
    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaTextType(nullable=True)

    def from_baserow_formula_type(
            self, formula_type: BaserowFormulaTextType
    ) -> TextField:
        # Pretend to be a text field from the formula systems perspective
        return TextField()

    # Baserow supports serializing all data and metadata in a workspace/database/table
    # to a JSON format.  We use this for templates/duplication etc.
    #
    # This import/export process completely remakes all the metadata in the
    # new duplicated table/db/workspace. This means all the PKs will be brand new,
    # so for the TranslateFieldType the source_field_id PK which will have been exported
    # will no longer point to the correct PK in the new duplicated table.
    #
    # To solve this, we can just use the deferred_fk_update_collector which will
    # wait until all fields have been remade with their new Pks, and then apply the
    # mapping from old PK to new PK for us so things remain consistant in the new
    # duplicated table.
    def import_serialized(
            self,
            table: "Table",
            serialized_values: Dict[str, Any],
            id_mapping: Dict[str, Any],
            deferred_fk_update_collector: DeferredFieldFkUpdater,
    ) -> "Field":
        serialized_copy = serialized_values.copy()
        # We have to temporarily remove the `source_field_id`, because it can be
        # that they haven't been created yet, which prevents us from finding it in
        # the mapping.
        original_source_field_id = serialized_copy.pop("source_field_id")
        field = super().import_serialized(
            table, serialized_copy, id_mapping, deferred_fk_update_collector
        )
        deferred_fk_update_collector.add_deferred_fk_to_update(
            field, "source_field_id", original_source_field_id
        )
        return field

    # So you already correctly update when rows/cell this field depends on change which
    # is great.
    # However, we also need to override this hook as if the source field we depend on
    # is updated (think we convert a text field to a formula field, any time a field
    # itself is editted it might re-compute all of its values).
    def field_dependency_updated(
            self,
            field: TranslationField,
            updated_field: Field,
            updated_old_field: Field,
            update_collector: "FieldUpdateCollector",
            field_cache: "FieldCache",
            via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self.update_all_rows(field)

        super().field_dependency_updated(
            field,
            updated_field,
            updated_old_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

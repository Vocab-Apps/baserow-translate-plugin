# Adding Field Models and Field Types
## Field Models
This plugin introduces new field types. When you add those fields to a table in your Baserow instance, the configuration of these fields needs to be stored somewhere, and in a particular format. We use a field **model** for that. Create the following file: `plugins/translate_plugin/backend/src/translate_plugin/models.py`

The content should be the following:
```
from django.db import models

from baserow.contrib.database.fields.models import Field

class TranslationField(Field):
    source_field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        help_text="The field to translate.",
        null=True,
        blank=True,
        related_name='+'
    )
    source_language = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Target Language",
    )
    target_language = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Target Language",
    )

class ChatGPTField(Field):
    prompt = models.CharField(
        max_length=4096,
        blank=True,
        default="",
        help_text="Prompt for chatgpt",
    )
```

The `TranslationField` model is more complicated. It references another field (which contains the text to translate), which is a `ForeignKey` (a link to another table row in database terminology), and also the *to* and *from* languages, which are strings.
The `ChatGPTField` model is very simple, it just contains a string, long enough to contain a ChatGPT prompt.

## Field Types
After creating the field models, we need to tell our Baserow plugin how these new fields will behave. Let's open a new file: `plugins/translate_plugin/backend/src/translate_plugin/field_types.py`

The code for the field types will be complicated, so I won't copy it entirely here, you can look at the sample code and copy from there. But i'll cover a few points.

First, we need to declare the field type properly, the *type* wil uniquely identify the filed, and model_class indicates the field model we'll use to store the atttributes of the field.
```
class TranslationFieldType(FieldType):
    type = 'translation'
    model_class = TranslationField
```
Here's an important method: `get_field_dependencies`. It tells Baserow what fields we depend on. If we change the source field, we want the translation field's content to change.
```
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
```
Let's also look at the code for `row_of_dependency_updated`. This is the method which will get called when the source field content changes. Let's say we want to translate from French to English. If you modify the text in the French column, the method `row_of_dependency_updated` will get called, and the translation code will get called. Notice that it can get called for a single row or multiple rows. Ultimately it calls the `translation.translate` method, which we'll define later.
```
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
```
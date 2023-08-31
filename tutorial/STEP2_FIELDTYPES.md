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

### TranslationFieldType

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
So we saw above that `row_of_dependency_updated` gets called when a single row is being edited. What if we add the Translation field to an existing table which already full of rows ? That's when the `after_create` and `after_update` methods come in. If your table already contains the *French* column, and you want to add a translation to *German*, then after the field is created, `after_create` will be called, and the code will be expected to populate all the translations. If you later change your mind and decide you want to translate to Italian instead, you'll edit the field properties, and then the `after_update` method will get called, populating the German translation for every row.

```
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
```

### ChatGPTFieldType
This field type is simpler, it only stores a single piece of text, the prompt. However to make it useful, that prompt can references other fields in your Baserow table. The goal is to be able to do things like that:
```
Translate from German to French: {German Field}
```
and *German Field* is a text field in baserow. For each row, Baserow will expand this to for example *Translate from German to French: Guten Tag* before sending it to the OpenAI API.

So we need some logic to expand the variables in the prompt, and here it is. The `get_field_dependencies` method will examine the prompt and correctly declare which fields we depend on.
```
    def get_fields_in_prompt(self, prompt):
        fields_to_expand = re.findall(r'{(.*?)}', prompt)
        return fields_to_expand

    def get_field_dependencies(self, field_instance: Field,
                               field_lookup_cache: FieldCache):
        """getting field dependencies is more complex here, because the user can add new field 
        variables, which creates a new dependency"""

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
```

`row_of_dependency_updated` also has some special logic, to fully expand the variables inside the prompt:
```
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
```
Besides that, the `ChatGPTFieldType` shares a lot of similarities with `TranslationFieldType`.

## Translation Logic
We need to call the translation APIs somewhere. Let's create the file `plugins/translate_plugin/backend/src/translate_plugin/translation.py`. Refer to the sample code for full contents, but i'll comment on some methods here.

This method translates a single field. It calls the ArgosTranslate library, which is a free open source machine translation library.
```
def translate(text, source_language, target_language):
    # call argos translate
    logger.info(f'translating [{text}] from {source_language} to {target_language}')
    return argostranslate.translate.translate(text, source_language, target_language)
```

If we added a translation field to an existing table, we need to populate a translation for every row of the table. We use the following method, which will iterate over all the rows, identify the source and target fields, call the translation method and save the new record.
```
def translate_all_rows(table_id, source_field_id, target_field_id, source_language, target_language):
    base_queryset = Table.objects
    # Didn't see like we needed to select the workspace for every row that we get?
    table = base_queryset.get(id=table_id)
    # https://docs.djangoproject.com/en/4.0/ref/models/querysets/
    table_model = table.get_model()
    for row in table_model.objects.all():
        text = getattr(row, source_field_id)
        translated_text = translate(text, source_language, target_language)
        setattr(row, target_field_id, translated_text)
        row.save()
    # notify the front-end that rows have been updated
    table_updated.send(None, table=table, user=None, force_table_refresh=True)
```

The ChatGPT method is simple, it takes a single prompt and returns the output:
```
def chatgpt(prompt):
    # call OpenAI chatgpt
    logger.info(f'calling chatgpt with prompt [{prompt}]')
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return chat_completion['choices'][0]['message']['content']
```

However, populating a chatgpt field on all rows requires doing this prompt template expansion logic again:
```
def chatgpt_all_rows(table_id, target_field_id, prompt, prompt_field_names):
    base_queryset = Table.objects
    table = base_queryset.get(id=table_id)
    table_model = table.get_model()

    # we'll build this map on the first row
    field_name_to_field_id_map = {}

    for row in table_model.objects.all():
        # do we need to build the map ?
        if len(field_name_to_field_id_map) == 0:
            for field in row.get_fields():
                field_name_to_field_id_map[field.name] = field.db_column

        # full expand the prompt
        expanded_prompt = prompt
        for field_name in prompt_field_names:
            internal_field_name = field_name_to_field_id_map[field_name]
            field_value = getattr(row, internal_field_name)
            if field_value == None:
                field_value = ''
            expanded_prompt = expanded_prompt.replace('{' + field_name + '}', field_value)

        # call chatgpt api, and save row.
        chatgpt_result = chatgpt(expanded_prompt)
        setattr(row, target_field_id, chatgpt_result)
        row.save()

    # notify the front-end that rows have been updated
    table_updated.send(None, table=table, user=None, force_table_refresh=True)    
```

## Registering our field types
We're almost done with the backend code. One more thing, we need to register our two new field types. Open `plugins/translate_plugin/backend/src/translate_plugin/apps.py`. At the end of the `ready(self)`, add the following:
```
        # register our new field type
        from baserow.contrib.database.fields.registries import field_type_registry
        from .field_types import TranslationFieldType, ChatGPTFieldType

        field_type_registry.register(TranslationFieldType())
        field_type_registry.register(ChatGPTFieldType())
```

After that's done, let's restart our instance again:
```
docker compose -f docker-compose.dev.yml up --build
```
We need to do one more thing, we have to apply a *django migration*, because we added a new model. In database terminology, a migration just means you're updating your table schema in some automated way. This is documented here: https://baserow.io/docs/plugins%2Ffield-type

```
# Set these env vars to make sure mounting your source code into the container uses
# the correct user and permissions.
export PLUGIN_BUILD_UID=$(id -u)
export PLUGIN_BUILD_GID=$(id -g)
docker container exec translate-plugin /baserow.sh backend-cmd manage makemigrations translate_plugin
docker container exec translate-plugin /baserow.sh backend-cmd manage migrate translate_plugin
```
You should see the following output:
```
~/python/translate-plugin
luc@vocabai$ docker container exec translate-plugin /baserow.sh backend-cmd manage makemigrations translate_plugin
 [STARTUP][2023-08-30 15:04:20] No DATABASE_HOST or DATABASE_URL provided, using embedded postgres.
 [STARTUP][2023-08-30 15:04:20] Using embedded baserow redis as no REDIS_HOST or REDIS_URL provided.
 [STARTUP][2023-08-30 15:04:20] Importing REDIS_PASSWORD secret from /baserow/data/.redispass
 [STARTUP][2023-08-30 15:04:20] Importing SECRET_KEY secret from /baserow/data/.secret
 [STARTUP][2023-08-30 15:04:20] Importing BASEROW_JWT_SIGNING_KEY secret from /baserow/data/.jwt_signing_key
 [STARTUP][2023-08-30 15:04:20] Importing DATABASE_PASSWORD secret from /baserow/data/.pgpass
OTEL_RESOURCE_ATTRIBUTES=service.namespace=Baserow,service.version=1.19.1,deployment.environment=unknown
Loaded backend plugins: translate_plugin
Migrations for 'translate_plugin':
  /baserow/data/plugins/translate_plugin/backend/src/translate_plugin/migrations/0001_initial.py
    - Create model ChatGPTField
    - Create model TranslationField

~/python/translate-plugin
luc@vocabai$ docker container exec translate-plugin /baserow.sh backend-cmd manage migrate translate_plugin
 [STARTUP][2023-08-30 15:04:33] No DATABASE_HOST or DATABASE_URL provided, using embedded postgres.
 [STARTUP][2023-08-30 15:04:33] Using embedded baserow redis as no REDIS_HOST or REDIS_URL provided.
 [STARTUP][2023-08-30 15:04:33] Importing REDIS_PASSWORD secret from /baserow/data/.redispass
 [STARTUP][2023-08-30 15:04:33] Importing SECRET_KEY secret from /baserow/data/.secret
 [STARTUP][2023-08-30 15:04:33] Importing BASEROW_JWT_SIGNING_KEY secret from /baserow/data/.jwt_signing_key
 [STARTUP][2023-08-30 15:04:33] Importing DATABASE_PASSWORD secret from /baserow/data/.pgpass
OTEL_RESOURCE_ATTRIBUTES=service.namespace=Baserow,service.version=1.19.1,deployment.environment=unknown
Loaded backend plugins: translate_plugin
Operations to perform:
  Apply all migrations: translate_plugin
Clearing Baserow's internal generated model cache...
Done clearing cache.
Running migrations:
  Applying translate_plugin.0001_initial... OK
Submitting the sync templates task to run asynchronously in celery after the migration...
Created 133 operations...
Deleted 27 un-registered operations...
Checking to see if formulas need updating...
2023-08-30 15:04:37.304 | INFO     | baserow.contrib.database.formula.migrations.handler:migrate_formulas:167 - Found 0 batches of formulas to migrate from version None to 5.
Finished migrating formulas: : 0it [00:00, ?it/s]
Syncing default roles: 100%|██████████| 7/7 [00:00<00:00, 64.91it/s]
```

And we are now completely done with the backend changes. Let's move on to the frontend.

[Step 3: Front End Changes](STEP3_FRONTEND.md)
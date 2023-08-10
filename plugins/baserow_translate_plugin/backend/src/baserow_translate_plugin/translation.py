""" 
this file contains translation logic, interfacing with actual libraries or REST APIs 
responsible for translation
"""

import logging

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.signals import table_updated

import argostranslate.translate

logger = logging.getLogger(__name__)

TEST_MODE = False

def translate(text, source_language, target_language):
    if TEST_MODE:
        return f'translation ({source_language} to {target_language}): {text}'
    else:
        # call argos translate
        logger.info(f'translating [{text}] from {source_language} to {target_language}')
        return argostranslate.translate.translate(text, source_language, target_language)


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

def chatgpt(prompt):
    # to be replaced with call to actual call to chatgpt later
    return f'chatgpt: {prompt}'


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
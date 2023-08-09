""" 
this file contains translation logic, interfacing with actual libraries or REST APIs 
responsible for translation
"""

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.signals import table_updated

def translate(text, source_language, target_language):
    # to be replaced with call to actual translation library later
    return f'translation ({source_language} to {target_language}): {text}'


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
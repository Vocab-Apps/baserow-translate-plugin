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



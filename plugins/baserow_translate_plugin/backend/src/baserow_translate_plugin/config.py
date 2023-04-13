from django.apps import AppConfig

from baserow.core.registries import plugin_registry
from baserow.contrib.database.fields.registries import field_type_registry


class PluginNameConfig(AppConfig):
    name = 'baserow_translate_plugin'

    def ready(self):
        from .plugins import PluginNamePlugin
        from .field_types import TranslationFieldType

        plugin_registry.register(PluginNamePlugin())
        field_type_registry.register(TranslationFieldType())
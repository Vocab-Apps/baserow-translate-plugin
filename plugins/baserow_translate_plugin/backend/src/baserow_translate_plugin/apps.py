from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = "baserow_translate_plugin"

    def ready(self):
        from .plugins import PluginNamePlugin

        plugin_registry.register(PluginNamePlugin())

        # register our new field type
        from baserow.contrib.database.fields.registries import field_type_registry
        from .field_types import TranslationFieldType

        field_type_registry.register(TranslationFieldType())        

from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = 'baserow_translate_plugin'

    def ready(self):
        from baserow.core.registries import plugin_registry
        from baserow.contrib.database.fields.registries import field_type_registry        

        from .plugins import PluginNamePlugin
        from .field_types import TranslationFieldType

        plugin_registry.register(PluginNamePlugin())
        field_type_registry.register(TranslationFieldType())
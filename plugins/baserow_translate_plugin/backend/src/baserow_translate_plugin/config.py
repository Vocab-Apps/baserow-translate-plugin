from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = 'baserow_translate_plugin'

    def ready(self):
        from baserow.core.registries import plugin_registry
        from baserow.contrib.database.fields.registries import field_type_registry        

        from .plugins import BaserowTranslatePlugin
        from .field_types import TranslationFieldType

        plugin_registry.register(BaserowTranslatePlugin())
        field_type_registry.register(TranslationFieldType())
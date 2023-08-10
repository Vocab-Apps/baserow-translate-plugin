from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class BaserowTranslatePluginDjangoAppConfig(AppConfig):
    name = "baserow_translate_plugin"

    def ready(self):
        from .plugins import BaserowTranslatePlugin

        plugin_registry.register(BaserowTranslatePlugin())

        # register our new field type
        from baserow.contrib.database.fields.registries import field_type_registry
        from .field_types import TranslationFieldType, ChatGPTFieldType

        field_type_registry.register(TranslationFieldType())
        field_type_registry.register(ChatGPTFieldType())

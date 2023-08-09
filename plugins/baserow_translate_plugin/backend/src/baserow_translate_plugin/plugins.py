from loguru import logger
from baserow.core.registries import Plugin
from django.urls import path, include

from .api import urls as api_urls


class BaserowTranslatePlugin(Plugin):
    type = "baserow_translate_plugin"

    def get_api_urls(self):
        return [
            path(
                "baserow_translate_plugin/",
                include(api_urls, namespace=self.type),
            ),
        ]

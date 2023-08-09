from loguru import logger
from baserow.core.registries import Plugin
from django.urls import path, include


class BaserowTranslatePlugin(Plugin):
    type = "baserow_translate_plugin"

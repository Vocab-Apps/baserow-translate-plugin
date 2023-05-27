FROM baserow/baserow:1.17.2

COPY ./plugins/baserow_translate_plugin/ /baserow/plugins/baserow_translate_plugin/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/baserow_translate_plugin

FROM baserow/backend:1.19.1

USER root

COPY ./plugins/baserow_translate_plugin/ $BASEROW_PLUGIN_DIR/baserow_translate_plugin/
RUN /baserow/plugins/install_plugin.sh --folder $BASEROW_PLUGIN_DIR/baserow_translate_plugin

USER $UID:$GID

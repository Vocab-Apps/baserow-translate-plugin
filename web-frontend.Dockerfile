FROM baserow/web-frontend:1.17.2

USER root

COPY ./plugins/baserow_translate_plugin/ /baserow/plugins/baserow_translate_plugin/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/baserow_translate_plugin

USER $UID:$GID

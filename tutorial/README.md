# Creating a Baserow plugin for language  translation (and yes we'll use ChatGPT)

In this tutorial, we'll go over how to create a plugin for the open source online database Baserow. There is existing documentation here: https://baserow.io/docs/plugins%2Fintroduction but in this tutorial we'll go into more detail at every step, and I will share my thoughts as a newcomer to Baserow.

We will introduce two new *field types*:
 1. a **Translation** field, which takes a source field, and translates it from one language to another, for example from English to French.
 2. a **ChatGPT** field, which takes a prompt and more or more source fields, and retrieves output from the OpenAI API.

The full example code is here: https://github.com/Language-Tools/baserow-translate-plugin

 ## Actually, what can Baserow plugins do ?
 At a super high level, Baserow is a Python Django app, and by writing python code, you can extend it in various ways. This tutorial focuses on introducing new *field types* (think Text, Date, Number, Formula, etc) which take input from another field, and produce a result.

 ## Do I need a plugin ?
 As always with programming, start with the most simple solution that works. Baserow has various import methods, a REST API, and webhooks. In most cases, you can use Baserow with no or very little programming. In this case, we are introducing some new logic as well as GUI changes, so the plugin framework is suitable for us.

 ## What are limitations of plugins ?
 Technically, you can do lots of things with plugins, and pretty much customize every aspect of Baserow. Right now, plugins need to be installed offline and deployed in a standalone Baserow instance, there is no such thing as an online marketplace where anyone can install a plugin with a click. If you are familiar with self-hosting apps, this is not a concern.

 # Let's get started
 What do you need ? A Linux server with docker and python 3.9. You also need to either be running  on the machine (like a linux desktop), or you need some way to access the machine over the internet since Baserow is a web app. More info here: https://baserow.io/docs/installation%2Finstall-on-ubuntu
 ## Create the plugin directory
 You need the python cookiecutter module (it's essentially a python module which lets you clone a directory in a certain way). These days the only way to install python modules is using a virtual env, so let's do that.
 ```
 # create the virtual env
 python3.9 -m venv translate-plugin
 # activate it
 source translate-plugin/bin/activate
 # update pip
 pip install --upgrade pip
 # finally, install cookiecutter pip module
 pip install cookiecutter
 ```
 Now, go to the directory where you want to create your plugin code. I put all my python projects in `~/python`
 ```
 cd ~/python
 cookiecutter gl:baserow/baserow --directory plugin-boilerplate
 # now, enter the project name, it's up to you what you choose
   [1/3] project_name (My Baserow Plugin): Translate Plugin
   [2/3] project_slug (translate-plugin):
   [3/3] project_module (translate_plugin):
 ```
ok, now we have a directory here: `~/python/translate-plugin`
```
luc@vocabai$ ls -ltr
total 56
-rw-r--r--. 1 luc luc  467 Aug 23 06:08 Caddyfile
-rw-r--r--. 1 luc luc  250 Aug 23 06:08 Caddyfile.dev
-rw-r--r--. 1 luc luc  179 Aug 23 06:08 Dockerfile
-rw-r--r--. 1 luc luc 2249 Aug 23 06:08 README.md
-rw-r--r--. 1 luc luc 1211 Aug 23 06:08 backend-dev.Dockerfile
-rw-r--r--. 1 luc luc  212 Aug 23 06:08 backend.Dockerfile
-rw-r--r--. 1 luc luc 1169 Aug 23 06:08 dev.Dockerfile
-rw-r--r--. 1 luc luc 1371 Aug 23 06:08 docker-compose.dev.yml
-rw-r--r--. 1 luc luc 6769 Aug 23 06:08 docker-compose.multi-service.dev.yml
-rw-r--r--. 1 luc luc 3599 Aug 23 06:08 docker-compose.multi-service.yml
-rw-r--r--. 1 luc luc  344 Aug 23 06:08 docker-compose.yml
-rw-r--r--. 1 luc luc  211 Aug 23 06:08 web-frontend.Dockerfile
-rw-r--r--. 1 luc luc  884 Aug 23 06:08 web-frontend-dev.Dockerfile
drwxr-xr-x. 1 luc luc   32 Aug 23 06:08 plugins
```

## Startup Baserow with the plugin installed
First, we're going to start up Baserow. We haven't added any custom code, so when things start up, you'll just have a self-hosted Baserow instance, but we want to make sure everything is working. Because I am overriding `$BASEROW_PUBLIC_URL`, and because i've already got a reverse proxy running on port 443, I need to make a small change to `docker-compose.dev.yml` first:
change this:
```
    ports:
      - "80:80"
      - "443:443"
    environment:
      BASEROW_PUBLIC_URL: http://localhost:8000
```
to this:
```
    ports:
      - "8000:80"
      - "8443:443"
    environment:
      BASEROW_PUBLIC_URL: ${BASEROW_PUBLIC_URL:-http://localhost:8000}
```

Now we can pretty much follow the official instructions from Baserow:
```
# Enable Docker buildkit
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
# Set these variables so the images are built and run with the same uid/gid as your 
# user. This prevents permission issues when mounting your local source into
# the images.
export PLUGIN_BUILD_UID=$(id -u)
export PLUGIN_BUILD_GID=$(id -g)
# this is specific to my machine. I have a special firewall setup, so I need to use port 8000 and a particular hostname
export BASEROW_PUBLIC_URL=http://`hostname -s`.webdev.ipv6n.net:8000
# and now, this command builds the docker contains and starts up everything
docker compose -f docker-compose.dev.yml up --build
```
Note that the last command for me is `docker compose`. You may also see `docker-compose`, and to be completely honest, I have no idea what the difference is, but `docker compose` works for me. After running this, the docker containers will get built, and this will take a while, a few minutes. Even after Baserow is up, it needs to do stuff like migrations and downloading templates. So you'll need to be patient. You should be seeing output like this:
```
luc@vocabai$ docker compose -f docker-compose.dev.yml up --build
[+] Building 23.6s (10/11)
 => [translate-plugin internal] load build definition from dev.Dockerfile                                                                0.0s
 => => transferring dockerfile: 1.27kB                                                                                                   0.0s
 => [translate-plugin internal] load .dockerignore                                                                                       0.0s
 => => transferring context: 2B                                                                                                          0.0s
 => [translate-plugin internal] load metadata for docker.io/baserow/baserow:1.19.1                                                       0.4s
 => [translate-plugin base 1/1] FROM docker.io/baserow/baserow:1.19.1@sha256:74a9f6a34af69488d82280a918231cbe10ae9ac68ab5b0582ae9b30844  0.0s
 => [translate-plugin internal] load build context                                                                                       0.0s
 => => transferring context: 16.64kB                                                                                                     0.0s
 => CACHED [translate-plugin stage-1 2/7] COPY --from=base --chown=1000:1000 /baserow /baserow                                           0.0s
 => CACHED [translate-plugin stage-1 3/7] RUN groupmod -g 1000 baserow_docker_group && usermod -u 1000 baserow_docker_user               0.0s
 => CACHED [translate-plugin stage-1 4/7] COPY --chown=1000:1000 ./plugins/translate_plugin/backend/requirements/dev.txt /tmp/plugin-de  0.0s
 => CACHED [translate-plugin stage-1 5/7] RUN . /baserow/venv/bin/activate && pip3 install -r /tmp/plugin-dev-requirements.txt && chown  0.0s
 => [translate-plugin stage-1 6/7] COPY --chown=1000:1000 ./plugins/translate_plugin/ /baserow/data/plugins/translate_plugin/            0.0s
 => [translate-plugin stage-1 7/7] RUN /baserow/plugins/install_plugin.sh --folder /baserow/data/plugins/translate_plugin --dev         23.2s
 => => # warning " > eslint-loader@4.0.2" has unmet peer dependency "webpack@^4.0.0 || ^5.0.0".
 => => # warning "eslint-plugin-jest > @typescript-eslint/utils > @typescript-eslint/typescript-estree > tsutils@3.21.0" has unmet peer depen
 => => # dency "typescript@>=2.8.0 || >= 3.2.0-dev || >= 3.3.0-dev || >= 3.4.0-dev || >= 3.5.0-dev || >= 3.6.0-dev || >= 3.6.0-beta || >= 3.7
 => => # .0-dev || >= 3.7.0-beta".
 [...]
```

Eventually you should get to this:
```
translate-plugin  |  [WEBFRONTEND][2023-08-22 22:28:14] ℹ Compiling Server
translate-plugin  |  [WEBFRONTEND][2023-08-22 22:28:16] ✔ Server: Compiled successfully in 32.66s
translate-plugin  |  [WEBFRONTEND][2023-08-22 22:28:17] ✔ Client: Compiled successfully in 34.91s
translate-plugin  |  [WEBFRONTEND][2023-08-22 22:28:17] ℹ Waiting for file changes
translate-plugin  |  [WEBFRONTEND][2023-08-22 22:28:17] ℹ Memory usage: 905 MB (RSS: 1.77 GB)
translate-plugin  |  [BACKEND][2023-08-22 22:28:17] INFO 2023-08-22 22:27:46,801 daphne.server.listen_success:159- Listening on TCP address 127.0.0.1:8000

translate-plugin  |  [BACKEND][2023-08-22 22:28:17] INFO 2023-08-22 22:28:17,126 django.channels.server.log_action:168- HTTP GET /api/_health/ 200 [0.02, 127.0.0.1:34740]
translate-plugin  |  [BASEROW-WATCHER][2023-08-22 22:28:17] Waiting for Baserow to become available, this might take 30+ seconds...
translate-plugin  |  [BASEROW-WATCHER][2023-08-22 22:28:17] =======================================================================
translate-plugin  |  [BASEROW-WATCHER][2023-08-22 22:28:17] Baserow is now available at http://vocabai.webdev.ipv6n.net:8000
```

And that's when you know you can open the web interface. In my case, I go to http://vocabai.webdev.ipv6n.net:8000. If you see the Baserow login page, you know that everything is up and running. You'll need to create a user so you can access Baserow and enter some data for later.

# Let's start making code changes

## Additional python modules
Open `backend/requirements/base.txt`. You can add additional python modules there, and we need the two following modules, so just append them at the end of the file:
```
argostranslate
openai
```
`argostranslate` is the open source machine translation module (https://github.com/argosopentech/argos-translate), and `openai` is the module you need to make OpenAI ChatGPT API calls.

Now, open `plugins/translate_plugin/backend/src/translate_plugin/apps.py`. We want to add some initialization code when the plugin first starts up. Add a new function:
```
def install_argos_translate_package(from_code, to_code):
    import argostranslate.package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(lambda x: x.from_code == from_code and x.to_code == to_code, available_packages)
    )
    argostranslate.package.install_from_path(package_to_install.download())        
```
and add this at the beginning of the `ready(self)` function:
```
        # install argostranslate language packs. they need to be installed by the user id running baserow,
        # as their data will be stored in $HOME/.local/share/argos-translate/
        install_argos_translate_package('en', 'fr')
        install_argos_translate_package('fr', 'en')

        # configure OpenAI
        openai_api_key = os.environ.get('OPENAI_API_KEY', '')
        if openai_api_key:
            import openai
            openai.api_key = openai_api_key
```
add `import os` at the top of the file.

What does this do ? The ArgosTranslate library requires to install language packs, and we're installing just French and English, to keep things simple. We're also configuring the OpenAI API key (you'll need one to try the ChatGPT field).

Now start up again. You should see docker install the argostranslate and openai python modules, then Baserow will start up again.
```
docker compose -f docker-compose.dev.yml up --build
```
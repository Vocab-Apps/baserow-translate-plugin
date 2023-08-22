# Creating a Baserow plugin for language  translation (and yes we'll use ChatGPT)

In this tutorial, we'll go over how to create a plugin for the open source online database Baserow. There is existing documentation here: https://baserow.io/docs/plugins%2Fintroduction but in this tutorial we'll go into more detail.

We will introduce two new field types:
 1. a **Translation** field, which takes a source field, and translates it from one language to another, for example from English to French.
 2. a **ChatGPT** field, which takes a prompt and more or more source fields, and retrieves output from the OpenAI API.

The full example code is here: https://github.com/Language-Tools/baserow-translate-plugin

 ## Actually, what can Baserow plugins do ?
 At a super high level, Baserow is a Python Django app, and by writing python code, you can extend it in various ways. This tutorial focuses on introducing new *field types* which take input from another field, and produce a result. 

 ## Do I need a plugin ?
 As always with programming, start with the most simple solution that works. Baserow has various import methods, a REST API, and webhooks. In most cases, you can use Baserow with no or very little programming. In this case, we are introducing some new logic as well as GUI changes, so the plugin framework is suitable for us.

 ## What are limitations of plugins ?
 Technically, you can do lots of things with plugins, and pretty much customize every aspect of Baserow. Right now, plugins need to be installed offline, there is no such thing as an online marketplace where anyone can install a plugin with a click. If you are familiar with self-hosting apps, this is not a concern.

 # Let's get started
 What do you need ? A Linux server with docker and python 3.9. More info here: https://baserow.io/docs/installation%2Finstall-on-ubuntu
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

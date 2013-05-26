#########################
Integrating a text editor
#########################

In django CMS, text - like any other content - is managed with a plugin.

In earlier versions of django CMS, a text plugin was provided, with the option
of two editors (WYMEditor, the default, and TinyMCE).

This is no longer the case, and now any text editor will need to be implemented
as an external plugin.

One is already provided by https://github.com/divio/djangocms-text-ckeditor.

But what if that's not the editor you want? In that case, if you can't find a
plugin that someone else has already built around the text editor you want,
you'll have to implement it yourself.
                                              
****************
The special case
****************

A text editing plugin is just a plugin like any other - it lives in a
placeholder, has the same needs (model subclass of
:class:`cms.models.pluginmodel.CMSPlugin`, its own
:class:`cms.plugin_base.CMSPluginBase` subclass, template and so on) - but it also has some special features.

In particular:

* complexity - an editor is a complex piece of software in its own right 
* admin furniture - an editor far more work to do on the admin side than most
  plugins, and needs the furniture to support this (JavaScript, complex
  templates, configuration)
* text plugins can contain, and need to manage, other plugins 

*************************
Let's build a text plugin
*************************

Name it
=======

Follow the naming convention already established. Call it
``djangocms_text_<whatever>``.

The model - ``Text(CMSPlugin)``
===============================
                      
The plugin class - ``TextPlugin(CMSPluginBase)``
================================================

HTML and JavaScript
===================

Now we have to integrate the business end of the text editor into the plugin;
this will largely be the editor's HTML and JavaScript.

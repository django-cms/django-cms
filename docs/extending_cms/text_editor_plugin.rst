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

This example will build a WYMeditor-based django CMS plugin from scratch.
Though the implementation details will be different for other editors, the
principles will be the same.

Name it
=======

Follow the naming convention already established. This one's 
``djangocms_text_wymeditor``.


The model - ``Text(CMSPlugin)``
===============================

Start with your model::

    class Text(CMSPlugin):
        body = models.TextField(_("body"))
                                               

The plugin class - ``TextPlugin(CMSPluginBase)``
================================================

The plugin class applies a special widget to the form::

    class TextPlugin(CMSPluginBase):
        model = Text # refer back to the model

        def get_form_class(self, request, plugins):
            """
            Returns a subclass of Form to be used by this plugin
            """
            # We avoid mutating the Form declared above by subclassing
            class TextPluginForm(self.form):
                pass
            widget = WYMEditor(installed_plugins=plugins)
            TextPluginForm.declared_fields["body"] = CharField(widget=widget, required=False)
            return TextPluginForm


The widget
==========

Now, we need to define the widget. The widget is going to render to a Django
template, which itself will initialise the editor. So, in your widget class,
you'll need something like::

    def render_additions():
        return mark_safe(render_to_string(
            'cms/plugins/widgets/wymeditor.html', context))  

Your widget class should have an inner ``Media`` class, in the WYMEditor case for:

* jQuery
* the main WYMeditor JS

                    
HTML and JavaScript
===================

Now we have to integrate the business end of the text editor into the plugin;
this will largely be the editor's HTML and JavaScript.

One important thing to realise that the HTML files that are part of the editor
itself *need to be treated as static assets, not as templates*. They are not
Django templates; they need to be served, raw, to the JS that will use them.

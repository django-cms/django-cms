Plugin Reference
================

model
-----

Is the CMSPlugin model we created earlier. If you don't need a model because
you just want to display some template logic, use CMSPlugin from
``cms.models`` as the model instead.

name
----

Will be displayed in the plugin editor.

module
------

Will be group the plugin in the plugin editor. If module is None, plugin is
grouped "Generic" group.

render_template
---------------

Will be rendered with the context returned by the render function

render
------

The render function takes 3 arguments:

**context**:

The context of the template placeholder was placed.

**instance**:

The instance of the GalleryPlugin model

**placeholder**:

The name of the placeholder this plugin appears. It is normally a good idea to
give the placeholder to the template so you can style the content differently
in the template based on which placeholder it is placed.

If you want to process forms in the render function or if you want to see if
the user is logged in you may want to access the request. You can accomplish
this simply with::

	request = context['request']

Because the request will always be in the context as the requestcontext
processor is required by the CMS.

PluginMedia
-----------

With a PluginMedia Class you can define a list of javascript and css files
that should get loaded with the html. You will need to palce a ``{%
plugin_media %}`` templatetag in your ``<head>``

example::

	class GalleryPlugin(CMSPluginBase):
		model = Gallery
		name = _("Gallery")
 		render_template = "cms/plugins/gallery.html"
   
 		def render(self, context, instance, placeholder):
 			context.update({
 				'instance': instance,
 				'gallery': instance.gallery,
 				'placeholder': placeholder,
 			})
 			return context
    
		class PluginMedia:
 			css = {
 				'all': ('%scss/jquery.lightbox-0.5.css' % settings.MEDIA_URL,)
 			}
 			js = ('%sgallery/js/jquery.cycle.min.js'% settings.MEDIA_URL,
 				'%sgallery/js/jquery.cycle.trans.min.js'% settings.MEDIA_URL,
 				'%sgallery/js/jquery.lightbox-0.5.min.js'% settings.MEDIA_URL,)

	plugin_pool.register_plugin(GalleryPlugin)

In this example a Gallery Plugin loads jquery lightbox and jquery cicle plugin
with some CSS

text_enabled
------------

*** icon_src ***

*** icon_alt ***

form
----

The form that will be displayed if you edit the plugin.
Have a read on django forms for this.

change_form_template
--------------------

The template that renders the form.

admin_preview
-------------

default = True

Should the plugin be rendered in the admin for a preview?

render_plugin
-------------

default = True

Should the plugin be rendered at all, or doesn't it have any output?


You have three options to extend Django CMS: Custom plugins, plugin context
processors, and plugin processors.

Custom Plugins
==============

You can use ``python manage.py startapp`` to get some basefiles for your plugin,
or just add a folder ``gallery`` to your project's root folder, add an empty ``__init__.py``, so that
the module gets detected.

Suppose you have the following gallery model::

	class Gallery(models.Model):
		name = models.CharField(max_length=30)

	class Picture(models.Model):
		gallery = models.ForeignKey(Gallery)
		image = models.ImageField(upload_to="uploads/images/")
		description = models.CharField(max_length=60)

And that you want to display this gallery between two text blocks.

You can do this with a CMS plugin. To create a CMS plugin you need two
components: a CMSPlugin model and a cms_plugins.py file.

Plugin Model
------------

First create a model that links to the gallery via a ForeignKey field::

	from cms.models import CMSPlugin

	class GalleryPlugin(CMSPlugin):
		gallery = models.ForeignKey(Gallery)

Be sure that your model inherits the CMSPlugin class.
The plugin model can have any fields it wants. They are the fields that
get displayed if you edit the plugin.

Now models.py looks like the following::

	from django.db import models
	from cms.models import CMSPlugin

	class Gallery(models.Model):
		parent = models.ForeignKey('self', blank=True, null=True)
		name = models.CharField(max_length=30)

		def __unicode__(self):
			return self.name
    
		def get_absolute_url(self):
			return reverse('gallery_view', args=[self.pk])
    
		class Meta:
			verbose_name_plural = 'gallery'


	class Picture(models.Model):
		gallery = models.ForeignKey(Gallery)
		image = models.ImageField(upload_to="uploads/images/")
		description = models.CharField(max_length=60)


	class GalleryPlugin(CMSPlugin):
		gallery = models.ForeignKey(Gallery)


Handling Relations
~~~~~~~~~~~~~~~~~~

If your custom plugin has foreign key or many-to-many relations you are
responsible for copying those if necessary whenever the CMS copies the plugin.

To do this you can implement a method called ``copy_relations`` on your plugin
model which get's the *old* instance of the plugin as argument.

Lets assume this is your plugin::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections =  models.ManyToManyField(Section)
        
        def __unicode__(self):
            return self.title
            
Now when the plugin gets copied, you want to make sure the sections stay::

        def copy_relations(self, oldinstance):
            self.sections = oldinstance.sections.all()
            
Your full model now::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections =  models.ManyToManyField(Section)
        
        def __unicode__(self):
            return self.title
        
        def copy_relations(self, oldinstance):
            self.sections = oldinstance.sections.all()


cms_plugins.py
--------------

After that create in the application folder (the same one where models.py is) a cms_plugins.py file.

In there write the following::

	from cms.plugin_base import CMSPluginBase
	from cms.plugin_pool import plugin_pool
	from models import GalleryPlugin
	from django.utils.translation import ugettext as _

	class CMSGalleryPlugin(CMSPluginBase):
		model = GalleryPlugin
		name = _("Gallery")
		render_template = "gallery/gallery.html"

		def render(self, context, instance, placeholder):
			context.update({
				'gallery':instance.gallery,
				'object':instance,
				'placeholder':placeholder
			})
			return context

	plugin_pool.register_plugin(CMSGalleryPlugin)


CMSPluginBase itself inherits from ModelAdmin so you can use all the things (inlines for example) you would
use in a regular admin class.


For a list of all the options you have on CMSPluginBase have a look at the plugin reference


Template
--------
Now create a gallery.html template in ``templates/gallery/`` and write the following in there::

	{% for image in gallery.picture_set.all %}
		<img src="{{ image.image.url }}" alt="{{ image.description }}" />
	{% endfor %}

Add a file ``admin.py`` in your plugin root-folder and insert the following::

	from django.contrib import admin
	from cms.admin.placeholderadmin import PlaceholderAdmin
	from models import Gallery,Picture

	class PictureInline(admin.StackedInline):
		model = Picture

	class GalleryAdmin(admin.ModelAdmin):
		inlines = [PictureInline]

	admin.site.register(Gallery, GalleryAdmin)


Now go into the admin create a gallery and afterwards go into a page and add a gallery plugin and some
pictures should appear in your page.

Limiting Plugins per Placeholder
--------------------------------

You can limit in which placeholder certain plugins can appear. Add a ``CMS_PLACEHOLDER_CONF`` to your ``settings.py``.

Example::

	CMS_PLACEHOLDER_CONF = {
	    'col_sidebar': {
        	'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin'),
        	'name': gettext("sidebar column")
    	},                    
                        
    	'col_left': {
	        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin','GoogleMapPlugin','CMSTextWithTitlePlugin','CMSGalleryPlugin'),
        	'name': gettext("left column")
    	},                  
                        
    	'col_right': {
	        'plugins': ('FilePlugin', 'FlashPlugin', 'LinkPlugin', 'PicturePlugin', 'TextPlugin', 'SnippetPlugin','GoogleMapPlugin',),
        	'name': gettext("right column")
    	},
	}

"**col_left**" and "**col_right**" are the names of two placeholders. The plugins list are filled with
Plugin class names you find in the ``cms_plugins.py``. You can add extra context to each placeholder so
plugin-templates can react to them. 

You can change the displayed name in the admin with the **name** parameter. In combination with gettext
you can translate this names according to the language of the user. Additionally you can limit the number
of plugins (either total or by type) for each placeholder with the **limits** parameter (see
``Configuration`` for details).


Advanced
--------

CMSGalleryPlugin can be even further customized:

Because CMSPluginBase extends ModelAdmin from django.contrib.admin you can use all the things you are used
to with normal admin classes. You can defined inlines, the form, the form template etc.

Note: If you want to overwrite the form be sure to extend from ``admin/cms/page/plugin_change_form.html``
to have an unified look across the plugins and to have the preview functionality automatically installed.


Plugin Context Processors
-------------------------

Plugin context processors are callables that modify all plugin's context before rendering. They are enabled
using the ``CMS_PLUGIN_CONTEXT_PROCESSORS`` setting.

A plugin context processor takes 2 arguments:

**instance**:

The instance of the plugin model

**placeholder**:

The instance of the placeholder this plugin appears in.

The return value should be a dictionary containing any variables to be added to the context.

Example::

    # settings.py:
    CMS_PLUGIN_CONTEXT_PROCESSORS = (
        'yourapp.cms_plugin_context_processors.add_verbose_name',
    )

    # yourapp.cms_plugin_context_processors.py:
    def add_verbose_name(instance, placeholder):
        '''
        This plugin context processor adds the plugin model's verbose_name to context.
        '''
        return {'verbose_name': instance._meta.verbose_name}

Plugin Processors
-----------------

Plugin processors are callables that modify all plugin's output after rendering. They are enabled using
the ``CMS_PLUGIN_PROCESSORS`` setting.

A plugin processor takes 4 arguments:

**instance**:

The instance of the plugin model

**placeholder**:

The instance of the placeholder this plugin appears in.

**rendered_content**:

A string containing the rendered content of the plugin.

**original_context**:

The original context for the template used to render the plugin.

Note that plugin processors are also applied to plugins embedded in Text. Depending on what your processor
does, this might break the output. For example, if your processor wraps the output in a DIV tag, you might
end up having DIVs inside of P tags, which is invalid. You can prevent such cases by returning
`rendered_content` unchanged if `instance._render_meta.text_enabled` is True, which is the case when
rendering an embedded plugin.

Example:

Suppose you want to put wrap each plugin in the main placeholder in a colored box, but it would be too
complicated to edit each individual plugin's template:

In your settings.py::

    CMS_PLUGIN_PROCESSORS = (
        'yourapp.cms_plugin_processors.wrap_in_colored_box',
    )

In your yourapp.cms_plugin_processors.py::

    def wrap_in_colored_box(instance, placeholder, rendered_content, original_context):
        '''
        This plugin processor wraps each plugin's output in a colored box if it is in the "main" placeholder.
        '''
        if placeholder.slot != 'main' \                   # Plugins not in the main placeholder should remain unchanged
            or (instance._render_meta.text_enabled   # Plugins embedded in Text should remain unchanged in order not to break output
                            and instance.parent):
                return rendered_content
        else:
            from django.template import Context, Template
            # For simplicity's sake, construct the template from a string:
            t = Template('<div style="border: 10px {{ border_color }} solid; background: {{ background_color }};">{{ content|safe }}</div>')
            # Prepare that template's context:
            c = Context({
                'content': rendered_content,
                # Some plugin models might allow you to customize the colors,
                # for others, use default colors:
                'background_color': instance.background_color if hasattr(instance, 'background_color') else 'lightyellow',
                'border_color': instance.border_color if hasattr(instance, 'border_color') else 'lightblue',
            })
            # Finally, render the content through that template, and return the output
            return t.render(c)


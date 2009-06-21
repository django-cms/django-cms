Plugins
=======

Suppose you have the following gallery model

	class Gallery(models.Model):
		name = models.CharField(max_length=30)
	
	class Picture(models.Model):
		gallery = models.ForeignKey(Gallery)
		image = models.ImageField(upload_to="uploads/images/")
		description = models.CharField(max_length=60)

and that you want to display this gallery between two text blocks.
You can do this with a CMS plugin.
To create a CMS plugin you need two components: a CMSPlugin model and a cms_plugins.py file.

Plugin Model
------------

First create a model that links to the gallery via a ForeignKey field:

	from cms.models import CMSPlugin
	
	class GalleryPlugin(CMSPlugin):
		gallery = models.ForeignKey(Gallery)

Be sure that your model inherits the CMSPlugin class.
The plugin model can have any fields it wants. They are the fields that
get displayed if you edit the plugin.

cms_plugins.py
--------------

After that create in the application folder (the same one where models.py is) a cms_plugins.py file.

In there write the following:

	from cms.plugin_base import CMSPluginBase
	from cms.plugin_pool import plugin_pool
	from models import GalleryPlugin
	from django.utils.translation import ugettext as _
	
	class CMSGalleryPlugin(CMSPluginBase):
		model = GalleryPlugin
		name = _("Gallery")
		render_template = "gallery/gallery.html"
	
		def render(self, context, instance, placeholder):
			return context.update({'gallery':instance.gallery, 'placeholder':placeholder})
	
	plugin_pool.register_plugin(CMSGalleryPlugin)		

### model ###

is the CMSPlugin model we created earlier.
If you don't need a model because you just want to display some template logic, use CMSPlugin from cms.models as the model instead.

### name ###

will be displayed in the plugin editor

### render\_template ###

will be rendered with the context returned by the render function

### render ###

the render function takes 3 arguments:

**context**:

the context of the template placeholder was placed.

**instance**:

the instance of the GalleryPlugin model

**placeholder**:

the name of the placeholder this plugin appears.
It is normally a good idea to give the placeholder to the template so you can style
the content differently in the template based on which placeholder it is placed.

If you want to process forms in the render function or if you want to see if the user is logged in you may want to access the request. 
You can accomplish this simply with:

	request = context['request']

because the request will always be in the context as the requestcontext processor is required by the CMS.

Template
--------
now create a gallery.html template in templates/gallery/ and write the following in there.

	{% for image in gallery.picture_set.all %}
		<img src="{{ image.image.url }}" alt="{{ image.description }}" />
	{% endfor %}

Now go into the admin create a gallery and afterwards go into a page and add a gallery plugin and some pictures should appear in your page.

Limiting Plugins per Placeholder
--------------------------------

You can limit in which placeholder certain plugins can appear. Add a CMS\_PLACEHOLDER\_CONF to your settings.py

Example:

	CMS_PLACEHOLDER_CONF = {                        
	    'content': {
	        "plugins": ('ContactFormPlugin','FilePlugin','FlashPlugin','LinkPlugin','PicturePlugin','TextPlugin'),
	        "extra_context": {"theme":"16_16"},
	    },

	    'right-column': {
	        "plugins": ('ContactFormPlugin','TextPlugin', 'SimpleGalleryPublicationPlugin'),
	        "extra_context": {"theme":"16_5"},
	    },
	
"content" and "right-column" are the names of two placeholders. The plugins list are filled with Plugin class names you find in the cms\_plugins.py. You can add extra context to each placeholder so plugin-templates can react to them. In this example we give them some parameters that used in CSS Grid Framework.


Advanced
--------

CMSGalleryPlugin can be even further customized:

Because CMSPluginBase extends ModelAdmin from django.contrib.admin you can use all the things you are used to with normal admin classes. You can defined inlines, the form, the form template etc.

Note: If you want to overwrite the form be sure to extend from "admin/cms/page/plugin\_change\_form.html" to have an unified look across the plugins and to have the preview functionality automatically installed.


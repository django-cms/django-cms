Placeholders
============

Placeholders are special model fields that DjangoCMS uses to render user-editable 
content (plugins) in templates. That is, it's the place where a user can add text, 
video or any other plugin to a webpage, using either the normal Django admin 
interface or the so called `frontend editing`.

Placeholders can be viewed as containers of `CMSPlugins`, and can be used outside 
the CMS in custom applications using the `PlaceholderField`.

By defining one (or serveral) `PlaceholderField` on a custom model you can take
advantage of the full power of `CMSPlugins`, including frontend editing.


Quickstart
----------

You need to define a `PlaceholderField` on the model you would like to use::

	from django.db import models
	from cms.models.fields import PlaceholderField
	
	class MyModel(models.Model):
		# your fields
		my_placeholder = PlaceholderField('placeholder_name')
		# your methods
		
The `PlaceholderField` takes a string as first argument which will be used to
configure which plugins can be used in this placeholder. The configuration is
the same as for placeholders in the CMS.

If you install this model in the admin application, you have to use
`PlaceholderAdmin` instead of `ModelAdmin` so the interface renders correctly::

	from django.contrib import admin
	from cms.admin.placeholderadmin import PlaceholderAdmin
	from myapp import MyModel
	
	admin.site.register(MyModel, PlaceholderAdmin)
	
Now to render the placeholder in a template you use the `render_placeholder` tag
from the `placeholder_tags` template tag library::

	{% load placeholder_tags %}
	
	{% render_placeholder mymodel_instance.my_placeholder "640" %}
	
"640" is the width to be used for width-sensitive plugins in this context. This
argument is optional.

Adding content to a placeholder
-------------------------------

There are two ways to add or edit content to a placeholder, the front-end admin view
and the back-end view.

Using the front-end editor
**************************

Probably the most simple way to add content to a placeholder, simply visit the page
displaying your model (where you put the ``render_placeholder`` tag), then append "?edit" to the page's URL. 
This will make a top banner appear, and after switching the "Edit mode" button to "on", 
the banner will prompt you for your username/password (the user should be allowed to edit the page, obviously)

You are now using the so-called *front-end edit mode*:

|edit-banner|

.. |edit-banner| image:: images/edit-banner.png

Once in Front-end editing mode, your placeholders should display a menu, allowing you to add ``plugins`` to them: 
the following screenshot shows a default selection of plugins in an empty placeholder.

|frontend-placeholder-add-plugin|

.. |frontend-placeholder-add-plugin| image:: images/frontend-placeholder-add-plugin.png

Plugins are rendered at once, so you can have an idea what it will look like `in fine`, but to view the final
look of a plugin simply leave edit mode by clicking the "Edit mode" button in the banner again.




Fieldsets
---------

There are some hard restrictions if you want to add custom fieldsets to an admin 
page with PlaceholderFields:

1. PlacehoderFields *must* be in their own fieldsets, one per fieldset.
2. You *must* include the following two classes: `plugin-holder` and `plugin-holder-nopage`



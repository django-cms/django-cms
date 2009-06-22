Installation
============

Copy the cms and mptt folders into your project or pythonpath.

Apps
----

Add the following to your INSTALLED_APPS in settings.py:

	INSTALLED_APPS = (
		...
		'cms',
		'cms.plugins.text',
		'cms.plugins.picture',
		'cms.plugins.link',
		'cms.plugins.file',
		'mptt',
		...
	)
    
Django-cms 2.0 is compatible with [django-reversion](http://code.google.com/p/django-reversion/) for versioning all the page content and its plugins.

Middleware
----------

Add the following middleware classes:

	MIDDLEWARE_CLASSES = (
		...
		'cms.middleware.CurrentPageMiddleware',
		'cms.middleware.MultilingualURLMiddleware',
		...
	)
    
If your site is not multilingual you can leave out the MutilingualURLMiddleware.

Context Processors
------------------

Add the following context processors if not already present:

	TEMPLATE_CONTEXT_PROCESSORS = (
		...
		"django.core.context_processors.request",
		"cms.context_processors.media",
		...
	)

Templates
---------

If you don't have already a gettext stub in your settings.py put this in your settings.py after the imports:

	gettext = lambda s: s
	
This allows you to use gettext in settings.py.

Add some templates you want to use within Django-cms 2.0 that contain at least one {% placeholder %} templatetag, to your settings.py:
	
	CMS_TEMPLATES = (
    	('base.html', gettext('default')),
    	('2col.html', gettext('2 Column')),
    	('3col.html', gettext('3 Column')),
    	('extra.html', gettext('Some extra fancy template')),
	)
	
For some template examples see the templates used in the example project.

A quick example:

	{% load cms_tags %}
	
	<div id="menu">{% show_menu 0 100 100 100 %}</div> 
	<div id="breadcrumb">{% show_breadcrumb %}</div>
	<div id="languagechooser">{% language_chooser %}</div>
	<div id="content">{% placeholder "content" %}</div>
	<div id="left_column">{% placeholder "left_column" %}</div>

i18n
----

If your site is multilingual be sure to have the LANGUAGES setting present in your settings.py file:

	LANGUAGES = (
		('fr', gettext('French')),
		('de', gettext('German')),
		('en', gettext('English')),
	)

Other settings
--------------

For a list of all settings that can be overridden in your settings.py have a look at cms/settings.py.

More information is available in the docs folder: [cms/docs/](http://github.com/digi604/django-cms-2.0/tree/master/cms/docs)
or have a look at the example project.

Media Files
-----------

If you don't use something like [django-appmedia](http://code.google.com/p/django-appmedia/) be sure that you copy all files located in cms/media to your static files folder.


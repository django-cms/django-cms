Plugins
=======

File
----

Allows you to upload a file. An filetype icon will be assigned based on the file extension.

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.file',
		...
	)

Flash
-----

Allows you to upload and display a .swf file on your page

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.flash',
		...
	)
	

GoogleMap
---------

Displays a map of an address on your page.

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.googlemap',
		...
	)
	
the google maps api key is also required:

either put this in your settings:

	GOOGLE_MAPS_API_KEY = "yourkey"
	
or be sure the context has a variable: GOOGLE\_MAPS\_API\_KEY


Link
----

Displays a link to an url or to a page. If a page is moved the url still is correct.

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.link',
		...
	)


Picture
-------

Displays a picture in a page

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.picture',
		...
	)
	
If you want to resize the picture you can get a thumbnail library. We recommend [sorl.thumbnail](http://code.google.com/p/sorl-thumbnail/)
In your project template directory create a folder called cms/plugins and create a picture.html in there.

Here is an example we use:

	{% load i18n thumbnail %}
	{% spaceless %}
	
	{% if picture.url %}<a href="{{ picture.url }}">{% endif %}
	{% ifequal placeholder "content" %}
		<img src="{% thumbnail image.url 484x1500 upscale %}" {% if picture.alt %}alt="{{ picture.alt }}" {% endif %}/>
	{% endifequal %}
	{% ifequal placeholder "teaser" %}
		<img src="{% thumbnail image.url 320x1500 upscale %}" {% if picture.alt %}alt="{{ picture.alt }}" {% endif %}/>
	{% endifequal %}
	{% if picture.url %}</a>{% endif %}
	
	{% endspaceless %}

The size of the pictures is different based on which placeholder it was placed.

Snippet
-------

Just renders some HTML Snippet. Mostly used for development or hackery.

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.snippet',
		...
	)


Teaser
------

Displays a teaser box for an other page or an url. A picture and a description can be added.

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.teaser',
		...
	)

Text
----

Displays text.
If plugins are text-enabled they can be placed inside the text-flow. At this moment the following plugins are text-enabled:

- link
- picture
- file
- snippet

The current editor is Wymeditor. If you want to use TinyMce you need to install [django-tinymce](http://code.google.com/p/django-tinymce/) first and put the following  in your settings.py:

	CMS_USE_TINYMCE = True

For installation be sure you have the following in your INSTALLED\_APPS in your settings.py:

	INSTALLED_APPS = (
		...
		'cms.plugins.text',
		...
	)
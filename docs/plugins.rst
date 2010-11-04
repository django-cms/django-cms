Plugins
=======

File
----

Allows you to upload a file. A filetype icon will be assigned based on the file extension.

For installation be sure you have the following in the ``INSTALLED_APPS`` setting
in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.file',
		# ...
	)

Flash
-----

Allows you to upload and display a Flash SWF file on your page.

For installation be sure you have the following in the ``INSTALLED_APPS``
setting in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.flash',
		# ...
	)


GoogleMap
---------

Displays a map of an address on your page.

For installation be sure you have the following in the ``INSTALLED_APPS``
setting in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.googlemap',
		# ...
	)

The Google Maps API key is also required. You can either put this in a project
setting called ``GOOGLE_MAPS_API_KEY`` or be sure the template context has a
variable with the same name.

Link
----

Displays a link to an arbitrary URL or to a page. If a page is moved the URL
will still be correct.

For installation be sure to have the following in the ``INSTALLED_APPS``
setting in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.link',
		# ...
	)

Picture
-------

Displays a picture in a page.

For installation be sure you have the following in the ``INSTALLED_APPS``
setting in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.picture',
		# ...
	)

If you want to resize the picture you can get a thumbnail library. We
recommend `sorl.thumbnail <http://code.google.com/p/sorl-thumbnail/>`_.

In your project template directory create a folder called ``cms/plugins`` and
create a file called ``picture.html`` in there. Here is an example
``picture.html`` template::

	{% load i18n thumbnail %}
	{% spaceless %}

	{% if picture.url %}<a href="{{ picture.url }}">{% endif %}
	{% ifequal placeholder "content" %}
		<img src="{% thumbnail picture.image.name 484x1500 upscale %}" {% if picture.alt %}alt="{{ picture.alt }}" {% endif %}/>
	{% endifequal %}
	{% ifequal placeholder "teaser" %}
		<img src="{% thumbnail picture.image.name 484x1500 upscale %}" {% if picture.alt %}alt="{{ picture.alt }}" {% endif %}/>
	{% endifequal %}
	{% if picture.url %}</a>{% endif %}

	{% endspaceless %}

In this template the picture is scaled differently based on which placeholder
it was placed in.

Snippet
-------

Just renders some HTML snippet. Mostly used for development or hackery.

For installation be sure you have the following in the ``INSTALLED_APPS``
setting in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.snippet',
		# ...
	)

Teaser
------

Displays a teaser box for another page or a URL. A picture and a description
can be added.

For installation be sure you have the following in the ``INSTALLED_APPS``
settings in your project's ``settings.py`` file::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.teaser',
		# ...
	)

Text
----

Displays text. If plugins are text-enabled they can be placed inside the
text-flow. At this moment the following plugins are text-enabled:

- link
- picture
- file
- snippet

The current editor is `Wymeditor <http://www.wymeditor.org/>`_. If you want to
use TinyMce you need to install `django-tinymce
<http://code.google.com/p/django-tinymce/>`_. If ``tinymce`` is in your
``INSTALLED_APPS`` it will be automatically enabled. If you have tinymce
installed but don't want to use it in the cms put the following in your
``settings.py``::

	CMS_USE_TINYMCE = False

For installation be sure you have the following in your project's
``INSTALLED_APPS`` setting::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.text',
		# ...
	)

Video
-----

Plays Video Files or Youtube / Vimeo Videos. Uses the `OSFlashVideoPlayer
<http://github.com/FlashJunior/OSFlashVideoPlayer>`_. If you upload a file use
.flv files or h264 encoded video files.

For installation be sure you have the following in your project's ``INSTALLED_APPS`` setting::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.video',
		# ...
	)

There are some settings you can set in your settings.py to overwrite some
default behavior:

- VIDEO_AUTOPLAY default=False
- VIDEO_AUTOHIDE default=False
- VIDEO_FULLSCREEN default=True
- VIDEO_LOOP default=False
- VIDEO_AUTOPLAY default=False
- VIDEO_AUTOPLAY default=False

- VIDEO_BG_COLOR default="000000"
- VIDEO_TEXT_COLOR default="FFFFFF"
- VIDEO_SEEKBAR_COLOR default="13ABEC"
- VIDEO_SEEKBARBG_COLOR default="333333"
- VIDEO_LOADINGBAR_COLOR default="828282"
- VIDEO_BUTTON_OUT_COLOR default="333333"
- VIDEO_BUTTON_OVER_COLOR default="000000"
- VIDEO_BUTTON_HIGHLIGHT_COLOR default="FFFFFF"


Twitter
-------

Displays the last number of post of a twitter user.

For installation be sure you have the following in your project's ``INSTALLED_APPS`` setting::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.twitter',
		# ...
	)

Inherit
-------

Displays all plugins of an other page or an other language. Great if you need always the same
plugins on a lot of pages.

For installation be sure you have the following in your project's ``INSTALLED_APPS`` setting::

	INSTALLED_APPS = (
		# ...
		'cms.plugins.inherit',
		# ...
	)

.. warning:: The inherit plugin is currently the only core-plugin which can
			 **not** be used in non-cms placeholders.
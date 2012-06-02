#################
Plugins reference
#################

.. :module:: cms.plugins.file

.. :class:: cms.plugins.file.models.FilePlugin

****
File
****

Allows you to upload a file. A filetype icon will be assigned based on the file
extension.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.file',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

You might consider using `django-filer`_ with `django CMS plugin`_ and its
``cmsplugin_filer_file`` component instead.

.. warning::

    The builtin file plugin does only work with local storages. If you need
    more advanced solutions, please look at alternative file plugins for the
    django CMS, such as `django-filer`_.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.flash

.. :class:: cms.plugins.flash.cms_plugins.FlashPlugin

*****
Flash
*****

Allows you to upload and display a Flash SWF file on your page.

For installation be sure you have the following in the
:setting:`django:INSTALLED_APPS` setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.flash',
        # ...
    )

.. :module:: cms.plugins.googlemap

.. :class:: cms.plugins.googlemap.cms_plugins.GoogleMapPlugin

*********
GoogleMap
*********

Displays a map of an address on your page.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.googlemap',
        # ...
    )

.. :module:: cms.plugins.link

.. :class:: cms.plugins.link.cms_plugins.LinkPlugin

****
Link
****

Displays a link to an arbitrary URL or to a page. If a page is moved the URL
will still be correct.

For installation be sure to have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.link',
        # ...
    )

.. note:: As of version 2.2, the link plugin no longer verifies the existance of
          link targets.


.. :module:: cms.plugins.picture

.. :class:: cms.plugins.picture.cms_plugins.PicturePlugin


*******
Picture
*******

Displays a picture in a page.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
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
``picture.html`` template:

.. code-block:: html+django

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

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.



.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_video`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.snippet

.. :class:: cms.plugins.snippet.cms_plugins.SnippetPlugin

*******
Snippet
*******

Renders a HTML snippet from a HTML file in your templates directories or a
snippet given via direct input.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.snippet',
        # ...
    )

.. note:: This plugin should mainly be used during development to quickly test
          HTML snippets.


.. :module:: cms.plugins.teaser

.. :class:: cms.plugins.teaser.cms_plugins.TeaserPlugin

******
Teaser
******

Displays a teaser box for another page or a URL. A picture and a description
can be added.

For installation be sure you have the following in the :setting:`django:INSTALLED_APPS`
settings in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.teaser',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_video`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.text

.. :class:: cms.plugins.text.cms_plugins.TextPlugin

****
Text
****

Displays text. If plugins are text-enabled they can be placed inside the
text-flow. At this moment the following core plugins are text-enabled:

- :mod:`cms.plugins.link`
- :mod:`cms.plugins.picture`
- :mod:`cms.plugins.file`
- :mod:`cms.plugins.snippet`

The current editor is `Wymeditor <http://www.wymeditor.org/>`_. If you want to
use TinyMce you need to install `django-tinymce`_. If ``tinymce`` is in your
:setting:`django:INSTALLED_APPS` it will be automatically enabled. If you have tinymce
installed but don't want to use it in the cms put the following in your
``settings.py``::

    CMS_USE_TINYMCE = False

.. note:: When using django-tinymce, you also need to configure it. See the
          `django-tinymce docs`_ for more information.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.text',
        # ...
    )

.. _django-tinymce: http://code.google.com/p/django-tinymce/
.. _django-tinymce docs: http://django-tinymce.googlecode.com/svn/tags/release-1.5/docs/.build/html/installation.html#id2

.. :module:: cms.plugins.video

.. :class:: cms.plugins.video.cms_plugins.VideoPlugin

*****
Video
*****

Plays Video Files or Youtube / Vimeo Videos. Uses the `OSFlashVideoPlayer
<http://github.com/FlashJunior/OSFlashVideoPlayer>`_. If you upload a file use
.flv files or h264 encoded video files.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.video',
        # ...
    )

There are some settings you can set in your settings.py to overwrite some
default behavior:

* ``VIDEO_AUTOPLAY`` ((default: ``False``)
* ``VIDEO_AUTOHIDE`` (default: ``False``)
* ``VIDEO_FULLSCREEN`` (default: ``True``)
* ``VIDEO_LOOP`` (default: ``False``)
* ``VIDEO_AUTOPLAY`` (default: ``False``)
* ``VIDEO_BG_COLOR`` (default: ``"000000"``)
* ``VIDEO_TEXT_COLOR`` (default: ``"FFFFFF"``)
* ``VIDEO_SEEKBAR_COLOR`` (default: ``"13ABEC"``)
* ``VIDEO_SEEKBARBG_COLOR`` (default: ``"333333"``)
* ``VIDEO_LOADINGBAR_COLOR`` (default: ``"828282"``)
* ``VIDEO_BUTTON_OUT_COLOR`` (default: ``"333333"``)
* ``VIDEO_BUTTON_OVER_COLOR`` (default: ``"000000"``)
* ``VIDEO_BUTTON_HIGHLIGHT_COLOR`` (default: ``"FFFFFF"``)

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django CMS plugin`_ and its ``cmsplugin_filer_video`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: cms.plugins.twitter

.. :class:: cms.plugins.twitter.cms_plugins.TwitterRecentEntriesPlugin

.. :class:: cms.plugins.twitter.cms_plugins.TwitterSearchPlugin

*******
Twitter
*******

Displays the last number of post of a twitter user.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.twitter',
        # ...
    )

.. note:: Since avatars are not guaranteed to be available over SSL (HTTPS), by
          default the Twitter plugin does not use avatars on secure sites.

.. :module:: cms.plugins.inherit

.. :class:: cms.plugins.twitter.cms_plugins.InheritPagePlaceholderPlugin

*******
Inherit
*******

Displays all plugins of another page or another language. Great if you need
always the same plugins on a lot of pages.

For installation be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'cms.plugins.inherit',
        # ...
    )

.. warning:: The inherit plugin is currently the only core-plugin which can
             **not** be used in non-cms placeholders.

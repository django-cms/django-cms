##########################
Some commonly-used plugins
##########################

.. warning::
    In version 3 of the CMS we removed all the plugins from the main repository
    into separate repositories to continue their development there.
    you are upgrading from a previous version. Please refer to
    :ref:`Upgrading from previous versions <upgrade-to-3.0>`

These are the recommended plugins to use with django CMS.

.. :module:: djangocms_file

.. :class:: djangocms_file.cms_plugins.FilePlugin

.. important::
    See the note on :ref:`installed_apps` about ordering.

****
File
****

Available on `GitHub (divio/djangocms-file) <http://github.com/divio/djangocms-file>`_ and on `PyPi (djangocms-file) <https://pypi.python.org/pypi/djangocms-file>`_.

Allows you to upload a file. A file-type icon will be assigned based on the file
extension.

Please install it using ``pip`` or similar and be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'djangocms_file',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writeable by the user under which django will be
running.

You might consider using `django-filer`_ with `django filer CMS plugin`_ and its
``cmsplugin_filer_file`` component instead.

.. warning::

    The ``djangocms_file`` file plugin only works with local storages. If you need
    more advanced solutions, please look at alternative file plugins for the
    django CMS, such as `django-filer`_.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django filer CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

*********
GoogleMap
*********

Available on `GitHub (divio/djangocms-googlemap) <http://github.com/divio/djangocms-googlemap>`_
and on `PyPi (djangocms-googlemap) <https://pypi.python.org/pypi/djangocms-googlemap>`_.

Displays a map of an address on your page.

Both address and coordinates are supported to centre the map; zoom level and
route planner can be set when adding/editing plugin in the admin.

.. versionadded:: 2.3.2
    width/height parameter has been added, so it's no longer required to set
    plugin container size in CSS or template.

.. versionchanged:: 2.3.2
    Zoom level is set via a select field which ensure only legal values are used.

.. note:: Due to the above change, `level` field is now marked as `NOT NULL`,
    and a data migration has been introduced to modify existing Googlemap plugin
    instance to set the default value if `level` if is `NULL`.

Please install it using ``pip`` or similar and be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'djangocms_googlemap',
        # ...
    )


.. :module:: djangocms_picture

.. :class:: djangocms_picture.cms_plugins.PicturePlugin

*******
Picture
*******

Available on `GitHub (divio/djangocms-picture) <http://github.com/divio/djangocms-picture>`_
and on `PyPi (djangocms-picture) <https://pypi.python.org/pypi/djangocms-picture>`_.

Displays a picture in a page.

Please install it using ``pip`` or similar and be sure you have the following in the :setting:`django:INSTALLED_APPS`
setting in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'djangocms_picture',
        # ...
    )

There are several solutions for Python and Django out there to automatically
re-size your pictures, you can find some on `Django Packages`_ and compare them
there.

In your project template directory create a folder called ``cms/plugins`` and
in it create a file called ``picture.html``. Here is an example
``picture.html`` template using `easy-thumbnails`_:

.. code-block:: html+django

    {% load thumbnail %}

    {% if link %}<a href="{{ link }}">{% endif %}
    {% if placeholder == "content" %}
        <img src="{% thumbnail picture.image 300x600 %}"{% if picture.alt %} alt="{{ picture.alt }}"{% endif %} />
    {% else %}
        {% if placeholder == "teaser" %}
            <img src="{% thumbnail picture.image 150x150 %}"{% if picture.alt %} alt="{{ picture.alt }}"{% endif %} />
        {% endif %}
    {% endif %}
    {% if link %}</a>{% endif %}


In this template the picture is scaled differently based on which placeholder
it was placed in.

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writeable by the user under which django will be
running.

.. note:: In order to improve clarity, some Picture fields have been omitted in
          the example template code.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django filer CMS plugin`_ and its ``cmsplugin_filer_image`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django filer CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

******
Teaser
******

Available on `GitHub (divio/djangocms-teaser) <http://github.com/divio/djangocms-teaser>`_
and on `PyPi (djangocms-teaser) <https://pypi.python.org/pypi/djangocms-teaser>`_.

Displays a teaser box for another page or a URL. A picture and a description
can be added.

Please install it using ``pip`` or similar and be sure you have the following in the :setting:`django:INSTALLED_APPS`
settings in your project's ``settings.py`` file::

    INSTALLED_APPS = (
        # ...
        'djangocms_teaser',
        # ...
    )

You should take care that the directory defined by the configuration setting
:setting:`CMS_PAGE_MEDIA_PATH` (by default ``cms_page_media/`` relative to
:setting:`django:MEDIA_ROOT`) is writeable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django filer CMS plugin`_ and its ``cmsplugin_filer_teaser`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django filer CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

****
Text
****

Consider using `djangocms-text-ckeditor
<https://github.com/divio/djangocms-text-ckeditor>`_ for displaying text. You
may of course use your preferred editor; others are available.

.. :module:: djangocms_video

.. :class:: djangocms_video.cms_plugins.VideoPlugin

*****
Video
*****

Available on `GitHub (divio/djangocms-video) <http://github.com/divio/djangocms-video>`_
and on `PyPi (djangocms-video) <https://pypi.python.org/pypi/djangocms-video>`_.

Plays Video Files or YouTube / Vimeo Videos. Uses the `OSFlashVideoPlayer
<http://github.com/FlashJunior/OSFlashVideoPlayer>`_. When uploading videos use either
``.flv`` files or H264 encoded video files.

Please install it using ``pip`` or similar and be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'djangocms_video',
        # ...
    )

There are some settings you can set in your ``settings.py`` to overwrite some
default behaviour:

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
:setting:`django:MEDIA_ROOT`) is writeable by the user under which django will be
running.

.. note:: For more advanced use cases where you would like to upload your media
          to a central location, consider using  `django-filer`_ with
          `django filer CMS plugin`_ and its ``cmsplugin_filer_video`` component
          instead.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django filer CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer

.. :module:: djangocms_twitter

.. :class:: djangocms_twitter.cms_plugins.TwitterRecentEntriesPlugin

.. :class:: djangocms_twitter.cms_plugins.TwitterSearchPlugin

*******
Twitter
*******

We recommend one of the following plugins:

* https://github.com/nephila/djangocms_twitter
* https://github.com/changer/cmsplugin-twitter

.. warning:: These plugins are not currently compatible with Django 1.7.

.. :module:: djangocms_inherit

.. :class:: djangocms_inherit.cms_plugins.InheritPagePlaceholderPlugin

*******
Inherit
*******

Available on `GitHub (divio/djangocms-inherit) <http://github.com/divio/djangocms-inherit>`_
and on `PyPi (djangocms-inherit) <https://pypi.python.org/pypi/djangocms-inherit>`_.

Displays all plugins of another page or another language. Great if you always
need the same plugins on a lot of pages.

Please install it using ``pip`` or similar and be sure you have the following in your project's
:setting:`django:INSTALLED_APPS` setting::

    INSTALLED_APPS = (
        # ...
        'djangocms_inherit',
        # ...
    )

.. warning:: The inherit plugin **cannot** be used in non-cms placeholders.

.. _Django Packages: http://djangopackages.com/grids/g/thumbnails/
.. _easy-thumbnails: https://github.com/SmileyChris/easy-thumbnails

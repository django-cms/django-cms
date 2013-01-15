.. _configuration:

#############
Configuration
#############

The django CMS has a lot of settings you can use to customize your installation
so that it is exactly as you'd like it to be.

*****************
Required Settings
*****************

.. setting:: CMS_TEMPLATES

CMS_TEMPLATES
=============

Default: ``()`` (Not a valid setting!)

A list of templates you can select for a page.

Example::

    CMS_TEMPLATES = (
        ('base.html', gettext('default')),
        ('2col.html', gettext('2 Column')),
        ('3col.html', gettext('3 Column')),
        ('extra.html', gettext('Some extra fancy template')),
    )

.. note::

    All templates defined in :setting:`CMS_TEMPLATES` must contain at least the
    ``js`` and ``css`` sekizai namespaces, for more information, see 
    :ref:`sekizai-namespaces`.

.. warning::

    django CMS internally relies on a number of templates to function correctly.
    These exist beneath ``cms`` within the templates directory. As such, it
    is highly recommended you avoid using the same directory name for your own
    project templates.

*******************
Basic Customization
*******************

.. setting:: CMS_TEMPLATE_INHERITANCE

CMS_TEMPLATE_INHERITANCE
========================

Default: ``True``

*Optional*
Enables the inheritance of templates from parent pages.

If this is enabled, pages have the additional template option to inherit their
template from the nearest ancestor. New pages default to this setting if the
new page is not a root page.


.. setting:: CMS_PLACEHOLDER_CONF

CMS_PLACEHOLDER_CONF
====================

Default: ``{}``
**Optional**

Used to configure placeholders. If not given, all plugins are available in all
placeholders.

Example::

    CMS_PLACEHOLDER_CONF = {
        'content': {
            'plugins': ['TextPlugin', 'PicturePlugin'],
            'text_only_plugins': ['LinkPlugin']
            'extra_context': {"width":640},
            'name':gettext("Content"),
        },
        'right-column': {
            "plugins": ['TeaserPlugin', 'LinkPlugin'],
            "extra_context": {"width":280},
            'name':gettext("Right Column"),
            'limits': {
                'global': 2,
                'TeaserPlugin': 1,
                'LinkPlugin': 1,
            },
        },
        'base.html content': {
            "plugins": ['TextPlugin', 'PicturePlugin', 'TeaserPlugin']
        },
    }

You can combine template names and placeholder names to granularly define
plugins, as shown above with ''base.html content''.

**plugins**

A list of plugins that can be added to this placeholder. If not supplied, all
plugins can be selected.

**text_only_plugins**

A list of additional plugins available only in the TextPlugin,
these plugins can't be added directly to this placeholder.

**extra_context**

Extra context that plugins in this placeholder receive.

**name**

The name displayed in the Django admin. With the gettext stub, the name can be
internationalized.

**limits**

Limit the number of plugins that can be placed inside this placeholder.
Dictionary keys are plugin names and the values are their respective limits. Special
case: "global" - Limit the absolute number of plugins in this placeholder
regardless of type (takes precedence over the type-specific limits).

.. setting:: CMS_PLUGIN_CONTEXT_PROCESSORS

CMS_PLUGIN_CONTEXT_PROCESSORS
=============================

Default: ``[]``

A list of plugin context processors. Plugin context processors are callables
that modify all plugins' context before rendering. See
:doc:`../extending_cms/custom_plugins` for more information.

.. setting:: CMS_PLUGIN_PROCESSORS

CMS_PLUGIN_PROCESSORS
=====================

Default: ``[]``

A list of plugin processors. Plugin processors are callables that modify all
plugin's output after rendering. See :doc:`../extending_cms/custom_plugins` for
more information.

.. setting:: CMS_APPHOOKS

CMS_APPHOOKS
============

Default: ``()``

A list of import paths for :class:`cms.app_base.CMSApp` subclasses.

Defaults to an empty list which means CMS applications are auto-discovered in
all :setting:`django:INSTALLED_APPS` by trying to import their ``cms_app`` module.

If this setting is set, the auto-discovery is disabled.

Example::

    CMS_APPHOOKS = (
        'myapp.cms_app.MyApp',
        'otherapp.cms_app.MyFancyApp',
        'sampleapp.cms_app.SampleApp',
    )

.. setting:: PLACEHOLDER_FRONTEND_EDITING

PLACEHOLDER_FRONTEND_EDITING
============================

Default: ``True``

If set to ``False``, frontend editing is not available for models using
:class:`cms.models.fields.PlaceholderField`.

********************
Editor configuration
********************

The Wymeditor from :mod:`cms.plugins.text` plugin can take the same
configuration as vanilla Wymeditor. Therefore you will need to learn 
how to configure that. The best thing to do is to head 
over to the `Wymeditor examples page 
<http://files.wymeditor.org/wymeditor/examples/>`_
in order to understand how Wymeditor works. 

The :mod:`cms.plugins.text` plugin exposes several variables named
WYM_* that correspond to the wym configuration. The simplest 
way to get started with this is to go to ``cms/plugins/text/settings.py``
and copy over the WYM_* variables and you will realize they 
match one to one to Wymeditor's.

Currently the following variables are available:

* ``WYM_TOOLS``
* ``WYM_CONTAINERS``
* ``WYM_CLASSES``
* ``WYM_STYLES``
* ``WYM_STYLESHEET``

*************
I18N and L10N
*************

.. setting:: CMS_LANGUAGES

CMS_LANGUAGES
=============

Default: Value of :setting:`django:LANGUAGES` converted to this format

Defines the languages available in django CMS.

Example::

    CMS_LANGUAGES = {
        1: [
            {
                'code': 'en',
                'name': gettext('English'),
                'fallbacks': ['de', 'fr'],
                'public': True,
                'hide_untranslated': True,
                'redirect_on_fallback':False,
            },
            {
                'code': 'de',
                'name': gettext('Deutsch'),
                'fallbacks': ['en', 'fr'],
                'public': True,
            },
            {
                'code': 'fr',
                'name': gettext('French'),
                'public': False,
            },
        ],
        2: [
            {
                'code': 'nl',
                'name': gettext('Dutch'),
                'public': True,
                'fallbacks': ['en'],
            },
        ],
        'default': {
            'fallbacks': ['en', 'de', 'fr'],
            'redirect_on_fallback':True,
            'public': False,
            'hide_untranslated': False,
        }
    }

.. note:: Make sure you only define languages which are also in :setting:`django:LANGUAGES`.

CMS_LANGUAGES has different options where you can granular define how different languages behave.

On the first level you can define SITE_IDs and default values. In the example above we define two sites. The first site
has 3 languages (English, German and French) and the second site has only Dutch. The `default` node defines
default behavior for all languages. You can overwrite the default settings with language specific properties.
For example we define `hide_untranslated` as False globally. The English language overwrites this behavior.

Every language node needs at least a `code` and a `name` property. `code` is the iso 2 code for the language. And
name is the verbose name of the language.

.. note:: With a gettext() lambda function you can make language names translatable. To enable this add
          `gettext = lambda s: s` at the beginning of your settings file. But maybe you want to leave the language name
          as it is.

What are the properties a language node can have?

.. setting::code

code
----

String. RFC5646 code of the language.

Example: ``"en"``.

.. note:: Is required for every language.

name
----
String. The verbose name of the language.

.. note:: Is required for every language.

.. setting::public

public
------
Is this language accessible in the frontend? For example, if you decide you want to add a new language to your page
but don't want to show it to the world yet.

Type: Boolean
Default: ``True``

.. setting::fallbacks

fallbacks
---------

A list of languages that are used if a page is not translated yet. The ordering is relevant.

Example: ``['de', 'fr']``
Default: ``[]``

.. setting::hide_untranslated

hide_untranslated
-----------------
Should untranslated pages be hidden in the menu?

Type: Boolean
Default: ``True``

.. setting::redirect_on_fallback

redirect_on_fallback
--------------------

If a page is not available should there be a redirect to a language that is, or should the content be displayed
in the other language in this page?

Type: Boolean
Default:``True``


**************
Media Settings
**************

.. setting:: CMS_MEDIA_PATH

CMS_MEDIA_PATH
==============

default: ``cms/``

The path from :setting:`django:MEDIA_ROOT` to the media files located in ``cms/media/``

.. setting:: CMS_MEDIA_ROOT

CMS_MEDIA_ROOT
==============

Default: :setting:`django:MEDIA_ROOT` + :setting:`CMS_MEDIA_PATH`

The path to the media root of the cms media files.

.. setting:: CMS_MEDIA_URL

CMS_MEDIA_URL
=============

default: :setting:`django:MEDIA_URL` + :setting:`CMS_MEDIA_PATH`

The location of the media files that are located in ``cms/media/cms/``

.. setting:: CMS_PAGE_MEDIA_PATH

CMS_PAGE_MEDIA_PATH
===================

Default: ``'cms_page_media/'``

By default, django CMS creates a folder called ``cms_page_media`` in your
static files folder where all uploaded media files are stored. The media files
are stored in subfolders numbered with the id of the page.

You should take care that the directory to which it points is writable by the
user under which Django will be running.


****
URLs
****

.. setting:: CMS_URL_OVERWRITE

CMS_URL_OVERWRITE
=================

Default: ``True``

This adds a new field "url overwrite" to the "advanced settings" tab of your
page. With this field you can overwrite the whole relative url of the page.

.. setting:: CMS_MENU_TITLE_OVERWRITE

CMS_MENU_TITLE_OVERWRITE
========================

Default: ``False``

This adds a new "menu title" field beside the title field.

With this field you can overwrite the title that is displayed in the menu.

To access the menu title in the template, use:

.. code-block:: html+django

    {{ page.get_menu_title }}

.. setting:: CMS_REDIRECTS

CMS_REDIRECTS
=============

Default: ``False``

This adds a new "redirect" field to the "advanced settings" tab of the page.

You can set a url here to which visitors will be redirected when the page is
accessed.

Note: Don't use this too much. :mod:`django.contrib.redirects` is much more
flexible, handy, and is designed exactly for this purpose.

.. setting:: CMS_SOFTROOT

CMS_SOFTROOT
============

Default: ``False``

This adds a new "softroot" field to the "advanced settings" tab of the page. If
a page is marked as softroot the menu will only display items until it finds
the softroot.

If you have a huge site you can easily partition the menu with this.


*****************
Advanced Settings
*****************

.. setting:: CMS_PERMISSION

CMS_PERMISSION
==============

Default: ``False``

If this is enabled you get 3 new models in Admin:

- Pages global permissions
- User groups - page
- Users - page

In the edit-view of the pages you can now assign users to pages and grant them
permissions. In the global permissions you can set the permissions for users
globally.

If a user has the right to create new users he can now do so in the "Users -
page". But he will only see the users he created. The users he created can also
only inherit the rights he has. So if he only has been granted the right to edit
a certain page all users he creates can, in turn, only edit this page. Naturally
he can limit the rights of the users he creates even further, allowing them to see
only a subset of the pages to which he is allowed access.

.. setting:: CMS_PUBLIC_FOR

CMS_PUBLIC_FOR
==============

Default: ``all``

Decides if pages without any view restrictions are public by default or staff
only. Possible values are ``all`` and ``staff``.

.. setting:: CMS_SHOW_START_DATE
.. setting:: CMS_SHOW_END_DATE

CMS_SHOW_START_DATE & CMS_SHOW_END_DATE
=======================================

Default: ``False`` for both

This adds two new :class:`~django.db.models.DateTimeField` fields in the
"advanced settings" tab of the page. With this option you can limit the time a
page is published.

.. setting:: CMS_SEO_FIELDS

CMS_SEO_FIELDS
==============

Default: ``False``

This adds a new "SEO Fields" fieldset to the page admin. You can set the
Page Title, Meta Keywords and Meta Description in there.

To access these fields in the template use:

.. code-block:: html+django

    {% load cms_tags %}
    <head>
        <title>{% page_attribute page_title %}</title>
        <meta name="description" content="{% page_attribute meta_description %}"/>
        <meta name="keywords" content="{% page_attribute meta_keywords %}"/>
        ...
        ...
    </head>

.. setting:: CMS_CACHE_DURATIONS

CMS_CACHE_DURATIONS
===================

This dictionary carries the various cache duration settings.

``'content'``
-------------

Default: ``60``

Cache expiration (in seconds) for :ttag:`show_placeholder` and :ttag:`page_url`
template tags.

.. note::

    This settings was previously called :setting:`CMS_CONTENT_CACHE_DURATION`

``'menus'``
-----------

Default: ``3600``

Cache expiration (in seconds) for the menu tree.

.. note::

    This settings was previously called :setting:`MENU_CACHE_DURATION`

``'permissions'``
-----------------

Default: ``3600``

Cache expiration (in seconds) for view and other permissions.

.. setting:: CMS_CACHE_PREFIX

CMS_CACHE_PREFIX
================

Default: ``cms-``


The CMS will prepend the value associated with this key to every cache access (set and get).
This is useful when you have several django CMS installations, and you don't want them
to share cache objects.

Example::

    CMS_CACHE_PREFIX = 'mysite-live'

.. note::

    Django 1.3 introduced a site-wide cache key prefix. See Django's own docs on
    :ref:`cache key prefixing <django:cache_key_prefixing>`

.. _configuration:

#############
Configuration
#############

django CMS has a number of settings to configure its behaviour. These should
be available in your ``settings.py`` file.

.. _installed_apps:

******************************
The ``INSTALLED_APPS`` setting
******************************

The ordering of items in ``INSTALLED_APPS`` matters. Entries for applications with plugins
should come *after* ``cms``.


.. _middleware:

**********************************
The ``MIDDLEWARE_CLASSES`` setting
**********************************

.. _ApphookReloadMiddleware:

``cms.middleware.utils.ApphookReloadMiddleware``
================================================

Adding ``ApphookReloadMiddleware`` to the ``MIDDLEWARE_CLASSES`` tuple will enable automatic server
restarts when changes are made to apphook configurations. It should be placed as near to the top of
the classes as possible.

.. note::

   This has been tested and works in many production environments and deployment configurations,
   but we haven't been able to test it with all possible set-ups. Please file an issue if you
   discover one where it fails.


************************
Custom User Requirements
************************

.. setting:: AUTH_USER_MODEL

When using a custom user model (i.e. the ``AUTH_USER_MODEL`` Django setting), there are a few
requirements that must be met.

django CMS expects a user model with at minimum the following fields: ``email``, ``password``,
``is_active``, ``is_staff``, and ``is_superuser``. Additionally, it should inherit from
``AbstractBaseUser`` and ``PermissionsMixin`` (or ``AbstractUser``), and must define one field as
the ``USERNAME_FIELD`` (see Django documentation for more details) and define a ``get_full_name()``
method.

The models must also be editable via Django's admin and have an admin class registered.

Additionally, the application in which the model is defined **must** be loaded before ``cms`` in ``INSTALLED_APPS``.

.. note::

    In most cases, it is better to create a ``UserProfile`` model with a one to one relationship to
    ``auth.User`` rather than creating a custom user model. Custom user models are only necessary if
    you intended to alter the default behaviour of the User model, not simply extend it.

    Additionally, if you do intend to use a custom user model, it is generally advisable to do so
    only at the beginning of a project, before the database is created.




*****************
Required Settings
*****************

.. setting:: CMS_TEMPLATES

CMS_TEMPLATES
=============

default
    ``()`` (Not a valid setting!)

A list of templates you can select for a page.

Example::

    CMS_TEMPLATES = (
        ('base.html', gettext('default')),
        ('2col.html', gettext('2 Column')),
        ('3col.html', gettext('3 Column')),
        ('extra.html', gettext('Some extra fancy template')),
    )

.. note::

    All templates defined in :setting:`CMS_TEMPLATES` **must** contain at least
    the ``js`` and ``css`` sekizai namespaces. For more information, see
    :ref:`sekizai-namespaces`.

.. note::

    Alternatively you can use :setting:`CMS_TEMPLATES_DIR` to define a directory
    containing templates for django CMS.

.. warning::

    django CMS requires some special templates to function correctly. These are
    provided within ``cms/templates/cms``. You are strongly advised not to use
    ``cms`` as a directory name for your own project templates.


*******************
Basic Customisation
*******************

.. setting:: CMS_TEMPLATE_INHERITANCE

CMS_TEMPLATE_INHERITANCE
========================

default
    ``True``

Enables the inheritance of templates from parent pages.

When enabled, pages' ``Template`` options will include a new default: *Inherit
from the parent page* (unless the page is a root page).


.. setting:: CMS_TEMPLATES_DIR

CMS_TEMPLATES_DIR
=================

default
    ``None``

Instead of explicitly providing a set of templates via :setting:`CMS_TEMPLATES`
a directory can be provided using this configuration.

`CMS_TEMPLATES_DIR` can be set to the (absolute) path of the templates directory,
or set to a dictionary with `SITE_ID: template path` items::

    CMS_TEMPLATES_DIR: {
        1: '/absolute/path/for/site/1/',
        2: '/absolute/path/for/site/2/',
    }


The provided directory is scanned and all templates in it are loaded as templates for
django CMS.

Template loaded and their names can be customised using the templates dir as a
python module, by creating a ``__init__.py`` file in the templates directory.
The file contains a single ``TEMPLATES`` dictionary with the list of templates
as keys and template names as values::::

    # -*- coding: utf-8 -*-
    from django.utils.translation import ugettext_lazy as _
    TEMPLATES = {
        'col_two.html': _('Two columns'),
        'col_three.html': _('Three columns'),
    }

Being a normal python file, templates labels can be passed through gettext
for translation.

.. note::

    As templates are still loaded by the Django template loader, the given
    directory **must** be reachable by the template loading system.
    Currently **filesystem** and **app_directory** loader schemas are tested and
    supported.


.. setting:: CMS_PLACEHOLDER_CONF

CMS_PLACEHOLDER_CONF
====================

default
    ``{}``

Used to configure placeholders. If not given, all plugins will be available in
all placeholders.

Example::

    CMS_PLACEHOLDER_CONF = {
        'content': {
            'plugins': ['TextPlugin', 'PicturePlugin'],
            'text_only_plugins': ['LinkPlugin'],
            'extra_context': {"width":640},
            'name': gettext("Content"),
            'language_fallback': True,
            'default_plugins': [
                {
                    'plugin_type': 'TextPlugin',
                    'values': {
                        'body':'<p>Lorem ipsum dolor sit amet...</p>',
                    },
                },
            ],
            'child_classes': {
                'TextPlugin': ['PicturePlugin', 'LinkPlugin'],
            },
            'parent_classes': {
                'LinkPlugin': ['TextPlugin'],
            },
        },
        'right-column': {
            "plugins": ['TeaserPlugin', 'LinkPlugin'],
            "extra_context": {"width": 280},
            'name': gettext("Right Column"),
            'limits': {
                'global': 2,
                'TeaserPlugin': 1,
                'LinkPlugin': 1,
            },
            'plugin_modules': {
                'LinkPlugin': 'Extra',
            },
            'plugin_labels': {
                'LinkPlugin': 'Add a link',
            },
        },
        'base.html content': {
            "plugins": ['TextPlugin', 'PicturePlugin', 'TeaserPlugin'],
            'inherit': 'content',
        },
    }

You can combine template names and placeholder names to define
plugins in a granular fashion, as shown above with ``base.html content``.

``plugins``
    A list of plugins that can be added to this placeholder. If not supplied,
    all plugins can be selected.

``text_only_plugins``
    A list of additional plugins available only in the TextPlugin, these
    plugins can't be added directly to this placeholder.

``extra_context``
    Extra context that plugins in this placeholder receive.

``name``
    The name displayed in the Django admin. With the gettext stub, the name can
    be internationalised.

``limits``
    Limit the number of plugins that can be placed inside this placeholder.
    Dictionary keys are plugin names and the values are their respective
    limits. Special case: ``global`` - Limit the absolute number of plugins in
    this placeholder regardless of type (takes precedence over the
    type-specific limits).

``language_fallback``
    When ``True``, if the placeholder has no plugin for the current language
    it falls back to the fallback languages as specified in :setting:`CMS_LANGUAGES`.
    Defaults to ``True`` since version 3.1.

.. _placeholder_default_plugins:

``default_plugins``
    You can specify the list of default plugins which will be automatically
    added when the placeholder will be created (or rendered).
    Each element of the list is a dictionary with following keys :

    ``plugin_type``
        The plugin type to add to the placeholder
        Example : ``TextPlugin``

    ``values``
        Dictionary to use for the plugin creation.
        It depends on the ``plugin_type``. See the documentation of each
        plugin type to see which parameters are required and available.
        Example for a text plugin:
        ``{'body':'<p>Lorem ipsum</p>'}``
        Example for a link plugin:
        ``{'name':'Django-CMS','url':'https://www.django-cms.org'}``

    ``children``
        It is a list of dictionaries to configure default plugins
        to add as children for the current plugin (it must accepts children).
        Each dictionary accepts same args than dictionaries of
        ``default_plugins`` : ``plugin_type``, ``values``, ``children``
        (yes, it is recursive).

    Complete example of default_plugins usage::

        CMS_PLACEHOLDER_CONF = {
            'content': {
                'name' : _('Content'),
                'plugins': ['TextPlugin', 'LinkPlugin'],
                'default_plugins':[
                    {
                        'plugin_type':'TextPlugin',
                        'values':{
                            'body':'<p>Great websites : %(_tag_child_1)s and %(_tag_child_2)s</p>'
                        },
                        'children':[
                            {
                                'plugin_type':'LinkPlugin',
                                'values':{
                                    'name':'django',
                                    'url':'https://www.djangoproject.com/'
                                },
                            },
                            {
                                'plugin_type':'LinkPlugin',
                                'values':{
                                    'name':'django-cms',
                                    'url':'https://www.django-cms.org'
                                },
                                # If using LinkPlugin from djangocms-link which
                                # accepts children, you could add some grandchildren :
                                # 'children' : [
                                #     ...
                                # ]
                            },
                        ]
                    },
                ]
            }
        }

``plugin_modules``
    A dictionary of plugins and custom module names to group plugin in the
    toolbar UI.

``plugin_labels``
    A dictionary of plugins and custom labels to show in the toolbar UI.

``child_classes``
    A dictionary of plugin names with lists describing which plugins may be
    placed inside each plugin. If not supplied, all plugins can be selected.

``parent_classes``
    A dictionary of plugin names with lists describing which plugins may contain
    each plugin. If not supplied, all plugins can be selected.

``require_parent``
    A Boolean indication whether that plugin requires another plugin as parent or
    not.

``inherit``
    Placeholder name or template name + placeholder name which inherit. In the
    example, the configuration for ``base.html content`` inherits from ``content``
    and just overwrites the ``plugins`` setting to allow ``TeaserPlugin``, thus you
    have not to duplicate the configuration of ``content``.

.. setting:: CMS_PLUGIN_CONTEXT_PROCESSORS


CMS_PLUGIN_CONTEXT_PROCESSORS
=============================

default
    ``[]``

A list of plugin context processors. Plugin context processors are callables
that modify all plugins' context *before* rendering. See
:doc:`/how_to/custom_plugins` for more information.

.. setting:: CMS_PLUGIN_PROCESSORS


CMS_PLUGIN_PROCESSORS
=====================

default
    ``[]``

A list of plugin processors. Plugin processors are callables that modify all
plugins' output *after* rendering. See :doc:`/how_to/custom_plugins`
for more information.

.. setting:: CMS_APPHOOKS


CMS_APPHOOKS
============

default:
    ``()``

A list of import paths for :class:`cms.app_base.CMSApp` sub-classes.

By default, apphooks are auto-discovered in applications listed in all
:setting:`django:INSTALLED_APPS`, by trying to import their ``cms_app`` module.

When ``CMS_APPHOOKS`` is set, auto-discovery is disabled.

Example::

    CMS_APPHOOKS = (
        'myapp.cms_app.MyApp',
        'otherapp.cms_app.MyFancyApp',
        'sampleapp.cms_app.SampleApp',
    )


*************
I18N and L10N
*************

.. setting:: CMS_LANGUAGES

CMS_LANGUAGES
=============

default
    Value of :setting:`django:LANGUAGES` converted to this format

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
            'public': True,
            'hide_untranslated': False,
        }
    }

.. note:: Make sure you only define languages which are also in :setting:`django:LANGUAGES`.

.. warning::

    Make sure you use **language codes** (`en-us`) and not **locale names**
    (`en_US`) here and in :setting:`django:LANGUAGES`.
    Use :ref:`check command <cms-check-command>` to check for correct syntax.

``CMS_LANGUAGES`` has different options where you can define how different
languages behave, with granular control.

On the first level you can set values for each ``SITE_ID``. In the example
above we define two sites. The first site has 3 languages (English, German and
French) and the second site has only Dutch.

The ``default`` node defines default behaviour for all languages. You can
overwrite the default settings with language-specific properties. For example
we define ``hide_untranslated`` as ``False`` globally, but the English language
overwrites this behaviour.

Every language node needs at least a ``code`` and a ``name`` property. ``code``
is the ISO 2 code for the language, and ``name`` is the verbose name of the
language.

.. note::

    With a ``gettext()`` lambda function you can make language names translatable.
    To enable this add ``gettext = lambda s: s`` at the beginning of your
    settings file.

What are the properties a language node can have?

.. setting::code


code
----
String. RFC5646 code of the language.

example
    ``"en"``.


.. note:: Is required for every language.

name
----
String. The verbose name of the language.

.. note:: Is required for every language.


.. setting::public

public
------
Determines whether this language is accessible in the frontend. You may want for example to keep a language private until your content has been fully translated.

type
    Boolean
default
    ``True``

.. setting::fallbacks


fallbacks
---------
A list of alternative languages, in order of preference, that are to be used if
a page is not translated yet..

example
    ``['de', 'fr']``
default
    ``[]``

.. setting::hide_untranslated


hide_untranslated
-----------------
Hide untranslated pages in menus

type
    Boolean
default
    ``True``

.. setting::redirect_on_fallback


redirect_on_fallback
--------------------
Determines behaviour when the preferred language is not available. If ``True``,
will redirect to the URL of the same page in the fallback language. If
``False``, the content will be displayed in the fallback language, but there
will be no redirect.

Note that this applies to the fallback behaviour of *pages*. Starting for 3.1 *placeholders*
**will** default to the same behaviour. If you do not want a placeholder to follow a page's
fallback behaviour, you must set its ``language_fallback`` to ``False``
in :setting:`CMS_PLACEHOLDER_CONF`, above.

type
    Boolean
default
    ``True``


Unicode support for automated slugs
===================================

django CMS supports automated slug generation from page titles that contain
Unicode characters via the unihandecode.js project. To enable support for
unihandecode.js, at least :setting:`CMS_UNIHANDECODE_HOST` and
:setting:`CMS_UNIHANDECODE_VERSION` must be set.


.. setting:: CMS_UNIHANDECODE_HOST

CMS_UNIHANDECODE_HOST
---------------------

default
    ``None``

Must be set to the URL where you host your unihandecode.js files. For licensing
reasons, django CMS does not include unihandecode.js.

If set to ``None``, the default, unihandecode.js is not used.


.. note::

    Unihandecode.js is a rather large library, especially when loading support
    for Japanese. It is therefore very important that you serve it from a
    server that supports gzip compression. Further, make sure that those files
    can be cached by the browser for a very long period.


.. setting:: CMS_UNIHANDECODE_VERSION

CMS_UNIHANDECODE_VERSION
------------------------

default
    ``None``

Must be set to the version number (eg ``'1.0.0'``) you want to use. Together
with :setting:`CMS_UNIHANDECODE_HOST` this setting is used to build the full
URLs for the javascript files. URLs are built like this:
``<CMS_UNIHANDECODE_HOST>-<CMS_UNIHANDECODE_VERSION>.<DECODER>.min.js``.


.. setting:: CMS_UNIHANDECODE_DECODERS

CMS_UNIHANDECODE_DECODERS
-------------------------

default
    ``['ja', 'zh', 'vn', 'kr', 'diacritic']``

If you add additional decoders to your :setting:`CMS_UNIHANDECODE_HOST`, you can add them to this setting.


.. setting:: CMS_UNIHANDECODE_DEFAULT_DECODER

CMS_UNIHANDECODE_DEFAULT_DECODER
--------------------------------

default
    ``'diacritic'``

The default decoder to use when unihandecode.js support is enabled, but the
current language does not provide a specific decoder in
:setting:`CMS_UNIHANDECODE_DECODERS`. If set to ``None``, failing to find a
specific decoder will disable unihandecode.js for this language.


Example
-------

Add these to your project's settings::

    CMS_UNIHANDECODE_HOST = '/static/unihandecode/'
    CMS_UNIHANDECODE_VERSION = '1.0.0'
    CMS_UNIHANDECODE_DECODERS = ['ja', 'zh', 'vn', 'kr', 'diacritic']

Add the library files from `GitHub ojii/unihandecode.js tree/dist <https://github.com/ojii/unihandecode.js/tree/master/dist>`_ to your static folder::

    project/
        static/
            unihandecode/
                unihandecode-1.0.0.core.min.js
                unihandecode-1.0.0.diacritic.min.js
                unihandecode-1.0.0.ja.min.js
                unihandecode-1.0.0.kr.min.js
                unihandecode-1.0.0.vn.min.js
                unihandecode-1.0.0.zh.min.js

More documentation is available on `unihandecode.js' Read the Docs <https://unihandecodejs.readthedocs.org/>`_.


**************
Media Settings
**************

.. setting:: CMS_MEDIA_PATH

CMS_MEDIA_PATH
==============

default
    ``cms/``

The path from :setting:`django:MEDIA_ROOT` to the media files located in ``cms/media/``


.. setting:: CMS_MEDIA_ROOT

CMS_MEDIA_ROOT
==============

default
    :setting:`django:MEDIA_ROOT` + :setting:`CMS_MEDIA_PATH`

The path to the media root of the cms media files.


.. setting:: CMS_MEDIA_URL

CMS_MEDIA_URL
=============

default
    :setting:`django:MEDIA_URL` + :setting:`CMS_MEDIA_PATH`

The location of the media files that are located in ``cms/media/cms/``


.. setting:: CMS_PAGE_MEDIA_PATH

CMS_PAGE_MEDIA_PATH
===================

default
    ``'cms_page_media/'``

By default, django CMS creates a folder called ``cms_page_media`` in your
static files folder where all uploaded media files are stored. The media files
are stored in sub-folders numbered with the id of the page.

You need to ensure that the directory to which it points is writeable by the
user under which Django will be running.


*****************
Advanced Settings
*****************

.. setting:: CMS_PERMISSION

CMS_PERMISSION
==============

default
    ``False``

When enabled, 3 new models are provided in Admin:

- Pages global permissions
- User groups - page
- Users - page

In the edit-view of the pages you can now assign users to pages and grant them
permissions. In the global permissions you can set the permissions for users
globally.

If a user has the right to create new users he can now do so in the "Users -
page", but he will only see the users he created. The users he created can also
only inherit the rights he has. So if he only has been granted the right to
edit a certain page all users he creates can, in turn, only edit this page.
Naturally he can limit the rights of the users he creates even further,
allowing them to see only a subset of the pages to which he is allowed access.


.. setting:: CMS_RAW_ID_USERS

CMS_RAW_ID_USERS
================

default
    ``False``

This setting only applies if :setting:`CMS_PERMISSION` is ``True``

The ``view restrictions`` and ``page permissions`` inlines on the
:class:`cms.models.Page` admin change forms can cause performance problems
where there are many thousands of users being put into simple select boxes. If
set to a positive integer, this setting forces the inlines on that page to use
standard Django admin raw ID widgets rather than select boxes if the number of
users in the system is greater than that number, dramatically improving
performance.

.. note:: Using raw ID fields in combination with ``limit_choices_to`` causes
          errors due to excessively long URLs if you have many thousands of
          users (the PKs are all included in the URL of the popup window). For
          this reason, we only apply this limit if the number of users is
          relatively small (fewer than 500). If the number of users we need to
          limit to is greater than that, we use the usual input field instead
          unless the user is a CMS superuser, in which case we bypass the
          limit.  Unfortunately, this means that non-superusers won't see any
          benefit from this setting.

.. versionchanged:: 3.2.1: CMS_RAW_ID_USERS also applies to
                           :class:`cms.model.GlobalPagePermission`` admin.


.. setting:: CMS_PUBLIC_FOR

CMS_PUBLIC_FOR
==============

default
    ``all``

Determines whether pages without any view restrictions are public by default or
staff only. Possible values are ``all`` and ``staff``.


.. setting:: CMS_CACHE_DURATIONS

CMS_CACHE_DURATIONS
===================

This dictionary carries the various cache duration settings.


``'content'``
-------------

default
    ``60``

Cache expiration (in seconds) for :ttag:`show_placeholder`, :ttag:`page_url`, :ttag:`placeholder` and :ttag:`static_placeholder`
template tags.

.. note::

    This settings was previously called :setting:`CMS_CONTENT_CACHE_DURATION`


``'menus'``
-----------

default
    ``3600``

Cache expiration (in seconds) for the menu tree.

.. note::

    This settings was previously called :setting:`MENU_CACHE_DURATION`


``'permissions'``
-----------------

default
    ``3600``

Cache expiration (in seconds) for view and other permissions.


.. setting:: CMS_CACHE_PREFIX

CMS_CACHE_PREFIX
================

default
    ``cms-``


The CMS will prepend the value associated with this key to every cache access
(set and get). This is useful when you have several django CMS installations,
and you don't want them to share cache objects.

Example::

    CMS_CACHE_PREFIX = 'mysite-live'

.. note::

    Django 1.3 introduced a site-wide cache key prefix. See Django's own docs
    on :ref:`cache key prefixing <django:cache_key_prefixing>`


.. setting:: CMS_PAGE_CACHE

CMS_PAGE_CACHE
==============

default
    ``True``

Should the output of pages be cached?
Takes the language, and time zone into account. Pages for logged in users are not cached.
If the toolbar is visible the page is not cached as well.


.. setting:: CMS_PLACEHOLDER_CACHE

CMS_PLACEHOLDER_CACHE
=====================

default
    ``True``

Should the output of the various placeholder template tags be cached?
Takes the current language and time zone into account. If the toolbar is in edit mode or a plugin with ``cache=False`` is
present the placeholders will not be cached.


.. setting:: CMS_PLUGIN_CACHE

CMS_PLUGIN_CACHE
================

default
    ``True``

Default value of the ``cache`` attribute of plugins. Should plugins be cached by default if not set explicitly?

.. warning::
    If you disable the plugin cache be sure to restart the server and clear the cache afterwards.


.. setting:: CMS_MAX_PAGE_PUBLISH_REVERSIONS

CMS_MAX_PAGE_HISTORY_REVERSIONS
===============================

default
    ``15``

Configures how many undo steps are saved in the db excluding publish steps.
In the page admin there is a ``History`` button to revert to previous version
of a page. In the past, databases using django-reversion could grow huge. To
help address this issue, only a limited number of *edit* revisions will now be saved.

This setting declares how many edit revisions are saved in the database.
By default the newest 15 edit revisions are kept.


CMS_MAX_PAGE_PUBLISH_REVERSIONS
===============================

default
    ``10``

If `django-reversion`_ is installed everything you do with a page and all
plugin changes will be saved in a revision.

In the page admin there is a ``History`` button to revert to previous version
of a page. In the past, databases using django-reversion could grow huge. To
help address this issue, only a limited number of *published* revisions will now be saved.

This setting declares how many published revisions are saved in the database.
By default the newest 10 published revisions are kept; all others are deleted
when you publish a page.

If set to *0* all published revisions are kept, but you will need to ensure
that the revision table does not grow excessively large.


.. setting:: CMS_TOOLBARS

CMS_TOOLBARS
============

default
    ``None``

If defined, specifies the list of toolbar modifiers to be used to populate the
toolbar as import paths. Otherwise, all available toolbars from both the CMS and
the third-party apps will be loaded.

Example::

    CMS_TOOLBARS = [
        # CMS Toolbars
        'cms.cms_toolbar.PlaceholderToolbar',
        'cms.cms_toolbar.BasicToolbar',
        'cms.cms_toolbar.PageToolbar',

        # third-party Toolbar
        'aldryn_blog.cms_toolbar.BlogToolbar',
    ]

.. _django-reversion: https://github.com/etianen/django-reversion
.. _unihandecode.js: https://github.com/ojii/unihandecode.js


CMS_TOOLBAR_ANONYMOUS_ON
========================

default
    ``True``

This setting controls if anonymous users can see the CMS toolbar with
a login form when ``?edit`` is appended to a URL. The default behaviour
is to show the toolbar to anonymous users.


CMS_TOOLBAR_HIDE
================

default
    ``False``

If True, the toolbar is hidden in the pages out django CMS.

.. versionchanged:: 3.2.1: CMS_APP_NAME has been removed as it's no longer required.


CMS_DEFAULT_X_FRAME_OPTIONS
===========================

default
    ``Page.X_FRAME_OPTIONS_INHERIT``

This setting is the default value for a Page's X Frame Options setting.
This should be an integer preferably taken from the Page object e.g.

- X_FRAME_OPTIONS_INHERIT
- X_FRAME_OPTIONS_ALLOW
- X_FRAME_OPTIONS_SAMEORIGIN
- X_FRAME_OPTIONS_DENY


.. _CMS_TOOLBAR_SIMPLE_STRUCTURE_MODE:

CMS_TOOLBAR_SIMPLE_STRUCTURE_MODE
=================================

default:
    ``True``

The new structure board operates by default in "simple" mode. The older mode used absolute
positioning. Setting this attribute to ``False`` will allow the absolute positioning used in
versions prior to 3.2. This setting will be removed in 3.3.


Example::

    CMS_TOOLBAR_SIMPLE_STRUCTURE_MODE = False

.. setting:: WIZARD_DEFAULT_TEMPLATE

WIZARD_DEFAULT_TEMPLATE
=======================

default
    ``TEMPLATE_INHERITANCE_MAGIC``

This is the path of the template used to create pages in the wizard. It must be one
of the templates in :setting:`CMS_TEMPLATES`.

.. setting:: CMS_WIZARD_CONTENT_PLUGIN

CMS_WIZARD_CONTENT_PLUGIN
=========================

default
    ``TextPlugin``

This is the name of the plugin created in the Page Wizard when the "Content" field is
filled in.
There should be no need to change it, unless you **don't** use
``djangocms-text-ckeditor`` in your project.

.. setting:: CMS_WIZARD_CONTENT_PLUGIN_BODY

CMS_WIZARD_CONTENT_PLUGIN_BODY
==============================

default
    ``body``

This is the name of the body field in the plugin created in the Page Wizard when the
"Content" field is filled in.
There should be no need to change it, unless you **don't** use
``djangocms-text-ckeditor`` in your project **and** your custom plugin defined in
:setting:`CMS_WIZARD_CONTENT_PLUGIN` have a body field **different** than ``body``.

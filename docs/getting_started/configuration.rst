#############
Configuration
#############

The Django-CMS has a lot of settings you can use to customize your installation
of the CMS to be exactly like you want it to be.

*****************
Required Settings
*****************

CMS_TEMPLATES
=============

Default: ``None`` (Not a valid setting!)

A list of templates you can select for a page.

Example::

    CMS_TEMPLATES = (
        ('base.html', gettext('default')),
        ('2col.html', gettext('2 Column')),
        ('3col.html', gettext('3 Column')),
        ('extra.html', gettext('Some extra fancy template')),
    )


*******************
Basic Customization
*******************

CMS_TEMPLATE_INHERITANCE
========================

Default: ``True``

*Optional*
Enables the inheritance of templates from parent pages.

If this is enabled, pages have the additional template option to inherit their
template from the nearest ancestor. New pages default to this setting if the
new page is not a root page.


CMS_PLACEHOLDER_CONF
====================

Default: ``{}``
**Optional**

Used to configure placeholders. If not given, all plugins are available in all
placeholders.

Example::

    CMS_PLACEHOLDER_CONF = {
        'content': {
            'plugins': ('TextPlugin', 'PicturePlugin'),
            'text_only_plugins': ('LinkPlugin',)
            'extra_context': {"width":640},
            'name':gettext("Content"),
        },
        'right-column': {
            "plugins": ('TeaserPlugin', 'LinkPlugin'),
            "extra_context": {"width":280},
            'name':gettext("Right Column"),
            'limits': {
                'global': 2,
                'TeaserPlugin': 1,
                'LinkPlugin': 1,
            },
        },
        'base.html content': {
            "plugins": {'TextPlugin', 'PicturePlugin', 'TeaserPlugin'}
        },
    }

You can combine template names and placeholder names to granually define
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
Dictionary keys are plugin names; values are their respective limits. Special
case: "global" - Limit the absolute number of plugins in this placeholder
regardless of type (takes precedence over the type-specific limits).


CMS_PLUGIN_CONTEXT_PROCESSORS
=============================

Default: ``[]``

A list of plugin context processors. Plugin context processors are callables
that modify all plugin's context before rendering. See
:doc:`../extending_cms/custom_plugins` for more information.


CMS_PLUGIN_PROCESSORS
=====================

Default: ``[]``

A list of plugin processors. Plugin processors are callables that modify all
plugin's output after rendering. See :doc:`../extending_cms/custom_plugins` for
more information.


CMS_APPHOOKS
============

Default: ``()``

A list of import paths for ``cms.app_base.CMSApp`` subclasses.

Defaults to an empty list which means CMS applications are auto-discovered in
all ``INSTALLED_APPS`` by trying to import their ``cms_app`` module.

If this setting is set, the auto-discovery is disabled.

Example::

    CMS_APPHOOKS = (
        'myapp.cms_app.MyApp',
        'otherapp.cms_app.MyFancyApp',
        'sampleapp.cms_app.SampleApp',
    )

PLACEHOLDER_FRONTEND_EDITING
============================

Default: ``True``

If set to ``False``, frontend editing is not available for models using
``cms.models.fields.PlaceholderField``.


*************
I18N and L10N
*************

CMS_HIDE_UNTRANSLATED
=====================

Default: ``True``

By default django-cms hides menu items that are not yet translated into the
current language. With this setting set to False they will show up anyway.

CMS_LANGUAGES
=============

Default: Value of ``LANGUAGES``

Defines the languages available in the CMS.

Example::

    CMS_LANGUAGES = (
        ('fr', gettext('French')),
        ('de', gettext('German')),
        ('en', gettext('English')),
    )

.. note:: Make sure you only define languages which are also in ``LANGUAGES``.


CMS_LANGUAGE_FALLBACK
=====================

Default: ``True``

This will redirect the browser to the same page in another language if the
page is not available in the current language.


CMS_LANGUAGE_CONF
=================

Default: ``{}``

Language fallback ordering for each language.

Example::

    CMS_LANGUAGE_CONF = {
        'de': ['en', 'fr'],
        'en': ['de'],
    }

CMS_SITE_LANGUAGES
==================

Default: ``{}``

If you have more than one site and CMS_LANGUAGES differs between the sites, you
may want to fill this out so if you switch between the sites in the admin you
only get the languages available on this site.

Example::

    CMS_SITE_LANGUAGES = {
        1:['en','de'],
        2:['en','fr'],
        3:['en'],
    }


CMS_FRONTEND_LANGUAGES
======================

Default: Value of ``CMS_LANGUAGES``

A list of languages Django CMS uses in the frontend. For example, if
you decide you want to add a new language to your page but don't want to
show it to the world yet.

Example::

    CMS_FRONTEND_LANGUAGES = ("de", "en", "pt-BR")


CMS_DBGETTEXT
=============

Default: ``False`` (unless ``dbgettext`` is in ``settings.INSTALLED_APPS``)

Enable gettext-based translation of CMS content rather than use the standard
administration interface. Requires `django-dbgettext
<http://http://bitbucket.org/drmeers/django-dbgettext>`_.

.. warning:: This feature is deprecated and will be removed in 2.2.

CMS_DBGETTEXT_SLUGS
===================

Default: ``False``

Enable gettext-based translation of page paths/slugs. Experimental at this
stage, as resulting translations cannot be guaranteed to be unique.

For general dbgettext settings, see the `dbgettext documentation
<http://bitbucket.org/drmeers/django-dbgettext/src/tip/docs>`_.

.. warning:: This feature is deprecated and will be removed in 2.2.


**************
Media Settings
**************


CMS_MEDIA_PATH
==============

default: ``cms/``

The path from MEDIA_ROOT to the media files located in ``cms/media/``

CMS_MEDIA_ROOT
==============

Default: ``settings.MEDIA_ROOT + CMS_MEDIA_PATH``

The path to the media root of the cms media files.


CMS_MEDIA_URL
=============

default: ``MEDIA_URL + CMS_MEDIA_PATH``

The location of the media files that are located in cms/media/cms/

CMS_PAGE_MEDIA_PATH
===================

Default: ``'cms_page_media/'``

By default, Django CMS creates a folder called 'cms_page_media' in your static
files folder where all uploaded media files are stored. The media files are
stored in subfolders numbered with the id of the page.


****
URLs
****

CMS_URL_OVERWRITE
=================

Default: ``True``

This adds a new field "url overwrite" to the "advanced settings" tab of your
page. With this field you can overwrite the whole relative url of the page.


CMS_MENU_TITLE_OVERWRITE
========================

Default: ``False``

This adds a new "menu title" field beside the title field.

With this field you can overwrite the title that is displayed in the menu.

To access the menu title in the template, use::

    {{ page.get_menu_title }}

CMS_REDIRECTS
=============

Default: ``False``

This adds a new "redirect" field to the "advanced settings" tab of the page.

You can set a url here, which a visitor will be redirected to when the page is
accessed.

Note: Don't use this too much. django.contrib.redirect is much more flexible,
handy, and is designed exactly for this purpose.


CMS_REDIRECTS_TO_PAGES
======================

Default: ``False``

This adds a new "redirect to page" field to the "advanced settings" tab of the
page.

You can select a page here, which a visitor will be redirected to when the page is
accessed.

Note: ``CMS_REDIRECTS`` has precedence over ``CMS_REDIRECTS_TO_PAGES``, i.e. if
both are enabled and a redirect URL is set for a page then this will be used for
the redirecting and a page redirection that might also be set will not be taken
into account. 


CMS_FLAT_URLS
=============

Default: ``False``

If this is enabled the slugs are not nested in the urls.

So a page with a "world" slug will have a "/world" url, even it is a child of
the "hello" page. If disabled the page would have the url: "/hello/world/"


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
only a subset of the pages he's allowed access to, for example.

CMS_MODERATOR
=============

Default: ``False``

If set to true, gives you a new "moderation" column in the tree view.

You can select to moderate pages or whole trees. If a page is under moderation
you will receive an email if somebody changes a page and you will be asked to
approve the changes. Only after you approved the changes will they be updated
on the "live" site. If you make changes to a page you moderate yourself, you
will need to approve it anyway. This allows you to change a lot of pages for
a new version of the site, for example, and go live with all the changes at the
same time.


CMS_SHOW_START_DATE & CMS_SHOW_END_DATE
=======================================

Default: ``False`` for both

This adds 2 new date-time fields in the advanced-settings tab of the page.
With this option you can limit the time a page is published.

CMS_SEO_FIELDS
==============

Default: ``False``

This adds a new "SEO Fields" fieldset to the page admin. You can set the
Page Title, Meta Keywords and Meta Description in there.

To access these fields in the template use::

    {% load cms_tags %}
    <head>
        <title>{% page_attribute page_title %}</title>
        <meta name="description" content="{% page_attribute meta_description %}"/>
        <meta name="keywords" content="{% page_attribute meta_keywords %}"/>
        ...
        ...
    </head>

CMS_CONTENT_CACHE_DURATION
==========================

Default: ``60``

Cache expiration (in seconds) for ``show_placeholder`` and ``page_url`` template tags.

MENU_CACHE_DURATION
===================

Default: ``3600``

Cache expiration (in seconds) for the menu tree.

CMS_CACHE_PREFIX
================

Default: ``None``


The CMS will prepend the value associated with this key to every cache access (set and get).
This is useful when you have several Django-CMS installations, and you don't want them
to share cache objects.

Example::

    CMS_CACHE_PREFIX = 'mysite-live'
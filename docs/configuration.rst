#############
Configuration
#############

django-cms doesn't come with a lot of features out-of-the-box. But with
a few settings you can extend it to an enterprise ready solution. All settings
described here are in cms/settings.py or in any installed plugin's settings.py file (if present).

Required Settings
=================

CMS_TEMPLATES
--------------

A list of templates you can select for a page.

Example::

	CMS_TEMPLATES = (
		('base.html', gettext('default')),
		('2col.html', gettext('2 Column')),
		('3col.html', gettext('3 Column')),
		('extra.html', gettext('Some extra fancy template')),
	)


Basic Customization
===================

CMS_TEMPLATE_INHERITANCE
------------------------

*Optional*
Enables the inheritance of templates from parent pages.

Default: ``True``

Example::

    CMS_TEMPLATE_INHERITANCE = True

If this is enabled, pages have the additional template option to inherit their
template from the nearest ancestor. New pages default to this setting if the
new page is not a root page.


CMS_PLACEHOLDER_CONF
----------------------

Used to configure placeholders.

*Optional*

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
-----------------------------

A list of plugin context processors. Plugin context processors are callables
that modify all plugin's context before rendering. See "Custom Plugins" for
more information.


CMS_PLUGIN_PROCESSORS
---------------------

A list of plugin processors. Plugin processors are callables that modify all
plugin's output after rendering. See "Custom Plugins" for more information.



CMS_APPHOOKS
------------

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



I18N and L10N
=============

CMS_HIDE_UNTRANSLATED
-----------------------

Example::

	CMS_HIDE_UNTRANSLATED = False

By default django-cms hides menu items that are not yet translated into the
current language. With this setting set to False they will show up anyway.

CMS_LANGUAGES
--------------

Which language should be used by the cms?

Example::

	CMS_LANGUAGES = (
	    ('fr', gettext('French')),
	    ('de', gettext('German')),
	    ('en', gettext('English')),
	)

Default is LANGUAGES. Be sure you don't have more languages in here than
in the LANGUAGES setting.


CMS_LANGUAGE_FALLBACK
-----------------------

Example::

	CMS_LANGUAGE_FALLBACK = True

This will redirect the browser to the same page in another language if the
page is not available in the current language.



CMS_LANGUAGE_CONF
-----------------

Language fallback ordering for each language.

Example::

	CMS_LANGUAGE_CONF = {
		'de': ['en', 'fr'],
		'en': ['de'],
	}

CMS_SITE_LANGUAGES
------------------

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
----------------------

A list of languages Django CMS uses in the frontend. For example, if
you decide you want to add a new language to your page but don't want to
show it to the world yet.

Example::

	CMS_FRONTEND_LANGUAGES = ("de", "en", "pt-BR")

Default is CMS_LANGUAGES


CMS_DBGETTEXT
-------------

Enable gettext-based translation of CMS content rather than use the standard
administration interface. Requires `django-dbgettext
<http://http://bitbucket.org/drmeers/django-dbgettext>`_.

Default: ``False`` (unless ``dbgettext`` is in ``settings.INSTALLED_APPS``)

CMS_DBGETTEXT_SLUGS
-------------------

Enable gettext-based translation of page paths/slugs. Experimental at this
stage, as resulting translations cannot be guaranteed to be unique.

Default: ``False``

For general dbgettext settings, see the `dbgettext documentation
<http://bitbucket.org/drmeers/django-dbgettext/src/tip/docs>`_.


Media Settings
==============


CMS_MEDIA_PATH
--------------

Example::

	CMS_MEDIA_PATH = "cms/"

The path from MEDIA_ROOT to the media files located in ``cms/media/``

default: ``cms/``

CMS_MEDIA_ROOT
--------------

Example::

	CMS_MEDIA_ROOT = "settings.MEDIA_ROOT + "/cms/"

The path to the media root of the cms media files.

Default: ``settings.MEDIA_ROOT + CMS_MEDIA_PATH``

CMS_MEDIA_URL
-------------

Example::

	CMS_MEDIA_URL = "/media/cms/"

The location of the media files that are located in cms/media/cms/

default: ``MEDIA_URL + CMS_MEDIA_PATH``

CMS_PAGE_MEDIA_PATH
-------------------

By default, Django CMS creates a folder called 'cms_page_media' in your static
files folder where all uploaded media files are stored. The media files are
stored in subfolders numbered with the id of the page.

Example::

	CMS_PAGE_MEDIA_PATH = 'cms_page_media/'


URLs
====

CMS_URL_OVERWRITE
-------------------

Example::

	CMS_URL_OVERWRITE = True

This adds a new field "url overwrite" to the "advanced settings" tab of your
page. With this field you can overwrite the whole relative url of the page.


CMS_MENU_TITLE_OVERWRITE
---------------------------

Example::

	CMS_MENU_TITLE_OVERWRITE = True

This adds a new "menu title" field beside the title field.

With this field you can overwrite the title that is displayed in the menu.

To access the menu title in the template, use::

	{{ page.get_menu_title }}

CMS_REDIRECTS
--------------

Example::

	CMS_REDIRECTS = True

This adds a new "redirect" field to the "advanced settings" tab of the page

You can set a url here, which a visitor will be redirected to when the page is accessed.

Note: Don't use this too much. django.contrib.redirect is much more flexible,
handy, and is designed exactly for this purpose.


CMS_FLAT_URLS
---------------

Example::

	CMS_FLAT_URLS = True

If this is enabled the slugs are not nested in the urls.

So a page with a "world" slug will have a "/world" url, even it is a child of
the "hello" page. If disabled the page would have the url: "/hello/world/"


CMS_UNIQUE_SLUGS
------------------

Example::

	CMS_UNIQUE_SLUGS = True

Defines if page slugs should be unique over all sites and languages. This
setting is changed automatically according to other settings.

Do not set it in your settings.py if you don't know what you are doing.

CMS_SOFTROOT
-------------

Example::

	CMS_SOFTROOT = True

This adds a new "softroot" field to the "advanced settings" tab of the page. If
a page is marked as softroot the menu will only display items until it finds
the softroot.

If you have a huge site you can easily partition the menu with this.


Advanced Settings
=================


CMS_PERMISSION
--------------

Example::

	CMS_PERMISSION = True

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
--------------

Example::

	CMS_MODERATOR = True

If set to true, gives you a new "moderation" column in the tree view.

You can select to moderate pages or whole trees. If a page is under moderation
you will receive an email if somebody changes a page and you will be asked to
approve the changes. Only after you approved the changes will they be updated
on the "live" site. If you make changes to a page you moderate yourself, you
will need to approve it anyway. This allows you to change a lot of pages for
a new version of the site, for example, and go live with all the changes at the
same time.


CMS_SHOW_START_DATE & CMS_SHOW_END_DATE
----------------------------------------------

Example::

	CMS_SHOW_END_DATE = True
	CMS_SHOW_START_DATE = True

This adds 2 new date-time fields in the advanced-settings tab of the page.
With this option you can limit the time a page is published.

CMS_SEO_FIELDS
----------------

Example::

	CMS_SEO_FIELDS = True

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
--------------------------

Example::

	CMS_CONTENT_CACHE_DURATION = 60

Defines how long page content should be cached, in seconds, including navigation and admin
menu.

Default is 60

CMS_CACHE_PREFIX
----------------

The CMS will prepend the value associated with this key to every cache access (set and get).
This is useful when you have several Django-CMS installations, and you don't want them
to share cache objects.

Example::

	CMS_CACHE_PREFIX = 'my_awesome_prefix'

Default is None


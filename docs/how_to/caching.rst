#####################
How to manage caching
#####################


******
Set-up
******

To setup caching configure a caching backend in django.

Details for caching can be found here: https://docs.djangoproject.com/en/dev/topics/cache/

In your middleware settings be sure to add ``django.middleware.cache.UpdateCacheMiddleware`` at the first and
``django.middleware.cache.FetchFromCacheMiddleware`` at the last position::

    MIDDLEWARE_CLASSES=[
            'django.middleware.cache.UpdateCacheMiddleware',
            ...
            'cms.middleware.language.LanguageCookieMiddleware',
            'cms.middleware.user.CurrentUserMiddleware',
            'cms.middleware.page.CurrentPageMiddleware',
            'cms.middleware.toolbar.ToolbarMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
        ],


Plugins
=======

.. versionadded:: 3.0

Normally all plugins will be cached. If you have a plugin that is dynamic based on the current user or other
dynamic properties of the request set the ``cache=False`` attribute on the plugin class::

    class MyPlugin(CMSPluginBase):
        name = _("MyPlugin")
        cache = False

.. warning::
    If you disable a plugin cache be sure to restart the server and clear the cache afterwards.

Content Cache Duration
======================

Default: 60

This can be changed in :setting:`CMS_CACHE_DURATIONS`

Settings
========

Caching is set default to true.
Have a look at the following settings to enable/disable various caching behaviours:

- :setting:`CMS_PAGE_CACHE`
- :setting:`CMS_PLACEHOLDER_CACHE`
- :setting:`CMS_PLUGIN_CACHE`






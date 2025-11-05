Multi-Site Installation
=======================

django CMS uses `Django's sites framework <https://docs.djangoproject.com/en/dev/ref/contrib/sites>`_
to manage multi-site installations.

There are three ways to run multiple sites with django CMS:

1. The classic (and most common) approach: separate settings files with distinct ``SITE_ID`` values.
2. Since django CMS 5.1: shared settings without a ``SITE_ID`` setting; the active site is resolved by Django’s Sites framework based on the request’s hostname.
3. Since django CMS 5.1: a custom site middleware; if it sets ``request.site``, django CMS will honor it.

Approach 1: Separate settings with SITE_ID (classic)
----------------------------------------------------

Operate multiple websites in the same virtualenv by using copies of ``manage.py`` and ``wsgi.py``,
plus per-site settings and URL configuration. You can use the same database for all sites
or separate databases for stricter isolation.

A common pattern is to keep shared configuration in a base settings file (e.g. ``my_project/base_settings.py``),
which is imported from each site-specific settings file and overridden as needed. Optionally, import
local, unversioned overrides at the end (e.g. secrets, database credentials).

1. Copy and edit ``wsgi.py`` and ``manage.py`` (e.g. to ``wsgi_second_site.py`` and ``manage_second_site.py``)
   and point ``DJANGO_SETTINGS_MODULE`` to the site’s settings module:

   .. code-block:: python

       os.environ.setdefault(
           "DJANGO_SETTINGS_MODULE",
           "my_project.settings_second_site"
       )

2. In each site-specific settings module, import the shared base and override site-specific values:

   .. code-block:: python

       # my_project/settings_second_site.py
       from .base_settings import *

       SITE_ID: int = 2
       ROOT_URLCONF: str = 'my_project.urls_second_site'
       # other site-specific settings…

       from .settings_local import *  # optional, not under version control

3. Configure your web server so the site uses its dedicated ``wsgi_*.py`` (e.g. ``wsgi_second_site.py``).

Approach 2 (since 5.1): Shared settings without SITE_ID
-------------------------------------------------------

If you omit ``SITE_ID`` from settings, django CMS determines the active site at request time using the
Sites framework and the incoming request’s hostname. This avoids duplicating ``manage.py``, ``wsgi.py``,
and settings modules.

Requirements and notes:

- Create one ``Site`` object per domain in Django’s admin with the correct ``domain``.
- Ensure all domains are listed in ``ALLOWED_HOSTS``.
- ``CMS_LANGUAGES`` can still define per-site language sets (by numeric site ID) and a ``'default'`` block.
  The active site’s language configuration is selected at runtime.

Example (single shared ``settings.py``):

.. code-block:: python

   # Do not set SITE_ID here

   ALLOWED_HOSTS = ['site1.example.com', 'site2.example.com']

   CMS_LANGUAGES = {
       1: [
           {'code': 'en', 'name': 'English', 'public': True},
       ],
       2: [
           {'code': 'de', 'name': 'Deutsch', 'public': True},
       ],
       'default': {
           'public': True,
           'hide_untranslated': False,
       },
   }

.. note::
   Management commands that run without a request (and thus without a hostname) may still need an explicit
   site context. Provide ``--site`` options where available, set ``SITE_ID`` just for the command’s runtime,
   or set ``request.site`` in custom command logic.

Approach 3 (since 5.1): Custom site middleware
----------------------------------------------

You can provide middleware that sets ``request.site``. django CMS will respect this attribute as the
current site for the request, regardless of whether ``SITE_ID`` is configured.

Example middleware:

.. code-block:: python

   # my_project/middleware.py
   from django.contrib.sites.models import Site

   class CurrentSiteFromHostMiddleware:
       def __init__(self, get_response):
           self.get_response = get_response

       def __call__(self, request):
           host = request.get_host().split(':')[0]
           try:
               request.site = Site.objects.get(domain=host)
           except Site.DoesNotExist:
               request.site = None  # optional fallback
           return self.get_response(request)

Register the middleware (early in the stack is recommended):

.. code-block:: python

   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'my_project.middleware.CurrentSiteFromHostMiddleware',
       # …
   ]

Apphooks and per-request site resolution
----------------------------------------

Apphooks are directly linked into Django's URL patterns. Since a common settings file results in common
URL patterns, django CMS adds apphooks of all sites into the same URL pattern **if the settings contain
no** ``SITE_ID``.

To isolate apphooks, the :py:meth:`~cms.utils.decorators.cms_site_filter` decorator is automatically added
to the apphook view functions, which ensures that an apphook is only displayed on its designated site.

However, when multiple sites are configured, this can lead to apphooks shadowing each other if they
share the same URL path. It is important to manage URL patterns carefully to avoid conflicts between
apphooks across different sites.

Language and URL configuration tips
-----------------------------------

- Ensure each domain has a matching ``Site`` with the exact ``domain`` value.
- Configure language sets in ``CMS_LANGUAGES`` per site or via the ``'default'`` block as needed.
- With approaches 2 and 3, the active site is determined per request; for batch tasks without requests,
  pass an explicit site context or temporarily set ``SITE_ID``.
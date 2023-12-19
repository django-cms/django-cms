Multi-Site Installation
=======================

For operating multiple websites using the same virtualenv you can use copies of
``manage.py``, ``wsgi.py`` and different versions of settings and the URL configuration
for each site. You can use the same database for different websites or, if you want a
stricter separation, different databases. You can define settings for all sites in a
file that is imported in the site-specific settings, e. g.
``my_project/base_settings.py``. At the end of these site-specific settings you can
import local settings, which are not under version control, with SECRET_KEY, DATABASES,
ALLOWED_HOSTS etc., which may be site-specific or not.

1. Copy and edit ``wsgi.py`` and ``manage.py`` e. g. to ``wsgi_second_site.py`` and
   ``manage_second_site.py``: Change the reference to the settings like
   ``os.environ.setdefault("DJANGO_SETTINGS_MODULE",
   "my_project.settings_second_site")``, if the settings are in
   ``my_project/settings_second_site.py``. Do this for each site.
2. In the site-specific settings import common base settings in the first line like
   ``from .base_settings import *`` and define ``SITE_ID``, ``ROOT_URLCONF``,
   ``CMS_LANGUAGES`` and other settings that should be different on the sites. This way
   all the items from the imported base settings can be overridden by later definitions:

   ``settings.second_site.py``:

   .. code-block::

       from .base_settings import *

       SITE_ID: int = 2
       ROOT_URLCONF: str = 'my_project.urls_second_site'
       # other site-specific settings…

       from .settings_local import *

3. In the web server settings for a site you refer to the site-specific ``wsgi*.py``
   like ``wsgi_second_site.py``.

#############
Sitemap Guide
#############


*******
Sitemap
*******

Sitemaps are XML files used by Google to index your website by using their
**Webmaster Tools** and telling them the location of your sitemap.

The :class:`CMSSitemap` will create a sitemap with all the published pages of
your CMS.


*************
Configuration
*************

 * add :mod:`django.contrib.sitemaps` to your project's :setting:`django:INSTALLED_APPS`
   setting
 * add ``from cms.sitemaps import CMSSitemap`` to the top of your main ``urls.py``
 * add ``url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'cmspages': CMSSitemap}}),``
   to your ``urlpatterns``


***************************
``django.contrib.sitemaps``
***************************

More information about :mod:`django.contrib.sitemaps` can be found in the official
`Django documentation <http://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/>`_.



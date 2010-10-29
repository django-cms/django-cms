Sitemap Guide
==================

Sitemap
-------

Sitemaps are XML files used by Google to index your website by using their
**Webmaster Tools** and telling them the location of your sitemap.

The CMSSitemap will create a sitemap with all the published pages of your cms

Configuration
-------------

Add ``django.contrib.sitemaps`` to your project's ``INSTALLED_APPS`` setting.
Add ``from cms.sitemaps import CMSSitemap`` to the top of your main `urls.py`.
Add ``url(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'cmspages': CMSSitemap}})``
to your urlpatterns.
	
Django.contrib.sitemaps
-----------------------

More information about ``djangot.contrib.sitemaps`` can be found in the official
`Django documentation <http://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/>`_.

 

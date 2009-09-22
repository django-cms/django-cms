Sitemap Guide
==================

Sitemap
-------

Sitemap are xml files fetched by google to help your site indexation.
You have to tell google were the sitemap is with the **Webmaster Tools**

The CMSSitemap will create a sitemap with all the published pages of your cms

Apps
----

Add the following to your project's ``INSTALLED_APPS`` setting::

	INSTALLED_APPS = (
		...
		'django.contrib.sitemaps',
		...
	)

urls.py
-------

In your main ``urls.py`` add the following import at the top of the file:
   	from cms.sitemaps import CMSSitemap

Then add the following line at the **start** of the ``urlpatterns`` definition::

    urlpatterns = (
		url(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'cmspages': CMSSitemap}}),
		...
	)
	
Django.contrib.sitemaps
-----------------------

More information about ``djangot.contrib.sitemaps`` can be found in the official django documentation `here <http://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/>`_.

 

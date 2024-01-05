.. _multilingual_support_how_to:

###############################
How to serve multiple languages
###############################

If you used `django CMS quickstart <https://github.com/django-cms/django-cms-quickstart>`_ to start your project, you'll find
that it's already set up for serving multilingual content. Our :ref:`installation` guide also does the same.

This guide specifically describes the steps required to enable multilingual support, in case you need to it manually.


.. _multilingual_urls:

*****************
Multilingual URLs
*****************

If you use more than one language, django CMS urls, *including the admin URLS*, need to be
referenced via :func:`~django.conf.urls.i18n.i18n_patterns`. For more information about this see
the official `Django documentation
<https://docs.djangoproject.com/en/dev/topics/i18n/translation/#internationalization-in-url-patterns>`_
on the subject.

Here's a full example of ``urls.py``::

    from django.conf.urls.i18n import i18n_patterns
    from django.contrib import admin
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.urls import include, path
    from django.views.i18n import JavaScriptCatalog


    admin.autodiscover()

    urlpatterns = i18n_patterns(
        re_path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    )
    urlpatterns += staticfiles_urlpatterns()

    # note the django CMS URLs included via i18n_patterns
    urlpatterns += i18n_patterns(
        path('admin/', include(admin.site.urls)),
        path('', include('cms.urls')),
    )


Monolingual URLs
================

Of course, if you want only monolingual URLs, without a language code, simply don't use :func:`~django.conf.urls.i18n.i18n_patterns`::

    urlpatterns += [
        path('admin', admin.site.urls),
        path('', include('cms.urls')),
    ]


************************************
Store the user's language preference
************************************

The user's preferred language is maintained through a browsing session. So that django CMS remembers the user's preference in subsequent sessions, it must be stored in a cookie. To enable this, ``cms.middleware.language.LanguageCookieMiddleware`` must be added to the project's ``MIDDLEWARE`` setting.

See :ref:`determining_language_preference` for more information about how this works.


*********************
Working in templates
*********************

Display a language chooser in the page
======================================

The :ttag:`language_chooser` template tag will display a language chooser for the
current page. You can modify the template in ``menu/language_chooser.html`` or
provide your own template if necessary.

Example:

.. code-block:: html+django

    {% load menu_tags %}
    {% language_chooser "myapp/language_chooser.html" %}


If you are in an apphook and have a detail view of an object you can
set an object to the toolbar in your view. The cms will call ``get_absolute_url`` in
the corresponding language for the language chooser:

Example:

.. code-block:: html+django

    class AnswerView(DetailView):
        def get(self, *args, **kwargs):
            self.object = self.get_object()
            if hasattr(self.request, 'toolbar'):
                self.request.toolbar.set_object(self.object)
            response = super().get(*args, **kwargs)
            return response


With this you can more easily control what url will be returned on the language chooser.

.. note::

    If you have a multilingual objects be sure that you return the right url if you don't have a translation for this language in ``get_absolute_url``


Get the URL of the current page for a different language
========================================================

The ``page_language_url`` returns the URL of the current page in another language.

Example:

.. code-block:: html+django

    {% page_language_url "de" %}


***************************************
Configuring language-handling behaviour
***************************************

:setting:`CMS_LANGUAGES` describes the all options available for determining how django CMS serves content across multiple
languages.


.. _documentation: https://docs.djangoproject.com/en/dev/topics/i18n/translation/#internationalization-in-url-patterns

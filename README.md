Django CMS 2.0
==============

A django app for managing hierarchical pages of content in multiple languages, on different sites.

Django CMS handles the navigation rendering for you in multiple language with i18n slugs 
and the navigation can be extended by your own models.

Pages are rendered with a template that have placeholders that get filled with plugins.

Plugins included at the moment:

* Text
* Picture
* Flash

many more are in the works.

Plugins are very easy to write and you can easily write them on your own and connect them with your own models.

For a feature comparison of all the cms apps available for django see: [CMSComparison](http://code.djangoproject.com/wiki/CMSAppsComparison)

For installation see [INSTALL](INSTALL.md).
For more docs see [docs](cms/docs).

visit [django-cms.org](http://www.django-cms.org/) or #django-cms on freenet for more info

This is a fork of django-page-cms and the main differences are the plugin system and performance improvements.


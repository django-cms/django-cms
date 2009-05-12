Django CMS 2.0
==============

A django app for managing hierarchical pages of content in multiple languages, on different sites.

Django CMS handles the navigation rendering for you in multiple languages with i18n slugs 
and the navigation can be extended by your own models.

Pages are rendered with a template that has placeholders that get filled with plugins.

Plugins included at the moment:

* Text
* Picture
* Flash
* File
* Links

many more are in the works.

Plugins are very easy to write and you can easily write them on your own and connect them with your own models.

![alt text](http://github.com/digi604/django-cms-2.0/raw/master/cms/docs/screen3.png "Tree / List view")

The tree supports full drag&drop and only shows the nodes you have permissions. If search or filters are activated a tradtional list view is shown.

![alt text](http://github.com/digi604/django-cms-2.0/raw/master/cms/docs/screen1.png "Edit view")

The edit page view. Right-Column and Content are placeholders in the default template. If an other template is chosen you see the corresponding placeholders.

![alt text](http://github.com/digi604/django-cms-2.0/raw/master/cms/docs/screen2.png "Plugin Editor with Textplugin")

If you select a plugin you can edit it. The text plugin has the unique capability that you can place plugins directly into the text flow. So links inserted with the link plugin stay up to date even if pages are moved in the tree and the urls change.

For a feature comparison of all the cms apps available for django see: [CMSComparison](http://code.djangoproject.com/wiki/CMSAppsComparison)

Install instructions you can find in the docs [here](http://github.com/digi604/django-cms-2.0/tree/master/cms/docs).

visit [django-cms.org](http://www.django-cms.org/) or #django-cms on freenet for more info

This is a fork of django-page-cms.
Some icons are from http://www.famfamfam.com


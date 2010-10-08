Django CMS 2.0
==============

A Django app for managing hierarchical pages of content in multiple languages, on different sites.

Django CMS handles the navigation rendering for you in multiple languages with internationalization (i18n) slugs,
and the navigation can be extended by your own models.

Pages are rendered with a template that has placeholders which get filled via plugins.
Plugins included at the moment include the following:

* File
* Flash
* Google Map
* Link
* Picture
* HTML Snippet
* Teaser
* Text
* Video
* Twitter


Many more are in the works.  Plugins are very easy to write and integrate with your own models.  
For a list of 3rd party plugins have a look [here](http://www.django-cms.org/en/extensions/).

Tour & Screenshots
------------------

Can be found [here](http://www.django-cms.org/en/tour/).
Some Sites done with django-cms can be found [here](http://www.django-cms.org/en/sites/)



Documentation
-------------

Can be found [here](http://www.django-cms.org/en/documentation/).

Installation instructions can be found [here](http://www.django-cms.org/en/documentation/2.0/installation/).


Sourcecode
----------

Can be found [here](http://github.com/divio/django-cms/) on github.

Running tests
-------------

`virtualenv` is highly recommended to run tests.

Here's a quick drilldown on how this should work on a unix system:
- virtualenv --no-site-packages <this directory>
- source bin/activate
- ./runtests.sh

The first run will bork and complain about PIL (since it's not always available as an egg, it's not in the dependencies).
Running `easy_install pil` should take care of it on linuxes.

Help
----

There is a [google group mailinglist](http://groups.google.com/group/django-cms)
You can also visit the project website at [django-cms.org](http://www.django-cms.org/)
or #django-cms on freenet IRC for more info.

For a feature comparison of all the CMS apps available for django see
[CMSComparison](http://code.djangoproject.com/wiki/CMSAppsComparison).

Kudos
-----

- This is a fork of django-page-cms.
- Some icons are from [http://www.famfamfam.com](http://www.famfamfam.com/)
- Video plugin uses [OSFlashVideoPlayer](http://github.com/FlashJunior/OSFlashVideoPlayer)
- Includes [Wymeditor](http://www.wymeditor.org/)
- Tree Component from [jstree.com](http://www.jstree.com/)


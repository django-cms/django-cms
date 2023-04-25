.. _commonly-used-plugins:

##########################
Some commonly-used plugins
##########################

.. warning::
    In version 3 of the CMS we removed all the plugins from the main repository
    into separate repositories to continue their development there.
    you are upgrading from a previous version. Please refer to
    :ref:`Upgrading from previous versions <upgrade-to-3.0>`


Please note that dozens if not hundreds of different django CMS plugins have been made available
under open-source licences. Some, like the ones on this page, are likely to be of general interest,
while others are highly specialised.

This page only lists those that fall under the responsibility of the django CMS project. Please see
the `Django Packages <https://djangopackages.org/search/?q=django+cms>`_ site for some more, or
just do a web search for the functionality you seek - you'll be surprised at the range of plugins
that has been created.


**********************
django CMS Core Addons
**********************

We maintain a set of *Core Addons* for django CMS. 

You don't need to use them, and for many of them alternatives exist, but they represent a good way
to get started with a reliable project set-up. We recommend them for new users of django CMS in
particular. For example, if you start a project on `Divio Cloud <https://divio.com/>`_ or using the
`django CMS installer <https://github.com/nephila/djangocms-installer>`_, this is the set of addons
you'll have installed by default.

The django CMS Core Addons are:

* `Django Filer <http://github.com/divio/django-filer>`_ - a file management application for
  images and other documents.
* `django CMS Admin Style <https://github.com/django-cms/djangocms-admin-style>`_ - a CSS theme for the
  Django admin
* `django CMS Text CKEditor <https://github.com/django-cms/djangocms-text-ckeditor>`_ - our default rich
  text WYSIYG editor
* `django CMS Link <https://github.com/django-cms/djangocms-link>`_ - add links to content
* `django CMS Picture <https://github.com/django-cms/djangocms-picture>`_ - add images to your site
  (Filer-compatible)
* `django CMS File <https://github.com/django-cms/djangocms-file>`_ - add files or an entire folder to
  your pages (Filer-compatible)
* `django CMS Style <https://github.com/django-cms/djangocms-style>`_ - create HTML containers with
  classes, styles, ids and other attributes
* `django CMS Snippet <https://github.com/django-cms/djangocms-snippet>`_ - insert arbitrary HTML content
* `django CMS Audio <https://github.com/django-cms/djangocms-audio>`_ - publish audio files
  (Filer-compatible)
* `django CMS Video <https://github.com/django-cms/djangocms-video>`_ - embed videos from YouTube, Vimeo
  and other services, or use uploaded videos (Filer-compatible)
* `django CMS GoogleMap <http://github.com/django-cms/djangocms-googlemap>`_ - displays a map of an
  address on your page. Supports addresses and coordinates. Zoom level and route planner options
  can also be set.

We welcome feedback, documentation, patches and any other help to maintain and improve these
valuable components.


**********************
Other addons of note
**********************

These packages are no longer officially guaranteed support by the django CMS project, but they have
good community support.

* `django CMS Inherit <https://github.com/divio/djangocms-inherit>`_ - renders the plugins from a
  specified page (and language) in its place
* `django CMS Column <https://github.com/divio/djangocms-column>`_ - layout page content in columns
* `django CMS Teaser <http://github.com/divio/djangocms-teaser>`_ - displays a teaser box for
  another page or a URL, complete with picture and a description


**********************
Deprecated addons
**********************

Some older plugins that you may have encountered are now deprecated and we advise against
incorporating them into new projects.

These are: 

* `cmsplugin-filer <https://github.com/divio/cmsplugin-filer>`_
* `Aldryn Style <https://github.com/aldryn/aldryn-style>`_
* `Aldryn Locations <https://github.com/aldryn/aldryn-locations>`_
* `Aldryn Snippet <https://github.com/aldryn/aldryn-snippet>`_

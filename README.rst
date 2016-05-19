##########
django CMS
##########
.. image:: https://travis-ci.org/divio/django-cms.svg?branch=develop
    :target: http://travis-ci.org/divio/django-cms
.. image:: https://img.shields.io/pypi/v/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://img.shields.io/pypi/dm/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://img.shields.io/badge/wheel-yes-green.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://img.shields.io/pypi/l/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://codeclimate.com/github/divio/django-cms/badges/gpa.svg
   :target: https://codeclimate.com/github/divio/django-cms
   :alt: Code Climate

Open source enterprise content management system based on the django framework.

.. image:: https://raw.githubusercontent.com/divio/django-cms/develop/docs/images/try-with-aldryn.png
   :target: http://demo.django-cms.org/
   :alt: Try demo with Aldryn Cloud

.. ATTENTION:: To propose features, always open pull requests on the **develop** branch.
   It's the branch for features that will go into the next django CMS feature release.

   For fixes for 3.1.x releases, please work on **support/3.1.x** which contains
   the next patch release for 3.1.x series.

   For fixes for 3.0.x releases, please work on **support/3.0.x** which contains
   the next patch release for 3.0.x series.

   The **master** branch is the current stable release, the one released on PyPI.
   Changes based on **master** will not be accepted.


********
Features
********

* Hierarchical pages
* Extensive support for multilingual websites
* Multi site support
* Draft/Published workflows
* Undo/Redo
* Use the content blocks (placeholders) in your own apps (models)
* Use the content blocks (static placeholders) anywhere in your templates
* Edit content directly in the frontend on your pages
* Hierarchical content plugins (columns, style changes etc)
* Navigation rendering and extending from your apps
* SEO friendly URLs
* Highly integrative into your own apps


You can define editable areas, called placeholders, in your templates which you fill
with many different so called CMS content plugins.
A list of all the plugins can be found here:

`3rd party plugins <http://www.djangopackages.com/grids/g/django-cms/>`_

Should you be unable to find a suitable plugin for you needs, writing your own is very simple.

More information on `our website <http://www.django-cms.org>`_.

************
Requirements
************

django CMS requires Django 1.8, and Python 2.7, 3.3 or 3.4.

*************
Documentation
*************

Please head over to our `documentation <http://docs.django-cms.org/>`_ for all
the details on how to install, extend and use the django CMS.

********
Tutorial
********

http://docs.django-cms.org/en/latest/introduction/index.html

***********
Quick Start
***********

You can use the `django CMS installer <http://djangocms-installer.readthedocs.org>`_::

    $ pip install --upgrade virtualenv
    $ virtualenv env
    $ source env/bin/activate
    (env) $ pip install djangocms-installer
    (env) $ mkdir myproject && cd myproject
    (env) $ djangocms -f -p . my_demo
    (env) $ python manage.py


************
Getting Help
************

Please head over to our IRC channel, #django-cms, on irc.freenode.net or write
to our `mailing list <https://groups.google.com/forum/#!forum/django-cms>`_.

If you don't have an IRC client, you can `join our IRC channel using the KiwiIRC web client
<https://kiwiirc.com/client/irc.freenode.net/django-cms>`_, which works pretty well.

******************
Commercial support
******************

This project is backed by `Divio <https://www.divio.com/en/commercial-support/>`_.
If you need help implementing or hosting django CMS, please contact us:
sales@divio.com.

*******
Credits
*******

* Includes icons from `FamFamFam <http://www.famfamfam.com>`_.
* Python tree engine powered by
  `django-treebeard <https://tabo.pe/projects/django-treebeard/>`_.
* JavaScript tree in admin uses `jsTree <http://www.jstree.com>`_.
* Many thanks to the
  `over 515 contributors <https://github.com/divio/django-cms/blob/master/AUTHORS>`_
  to the django CMS!

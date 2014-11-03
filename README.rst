##########
django CMS
##########
.. image:: https://api.travis-ci.org/divio/django-cms.svg?branch=develop
    :target: http://travis-ci.org/divio/django-cms
.. image:: https://pypip.in/v/django-cms/badge.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://pypip.in/d/django-cms/badge.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://pypip.in/wheel/django-cms/badge.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://pypip.in/license/django-cms/badge.svg
    :target: https://pypi.python.org/pypi/django-cms/


NOTE::

	You are currently on the 'develop' branch, normally, this is a great place
	to get the latest and greatest. However, at this time, this branch is
	being prepared for 3.1 and is currently pre-alpha quality. if you want the
	latest stable release, please switch to the `Support 3.0.x` branch.



Open source enterprise content management system based on the django framework.

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
* SEO friendly urls
* Highly integrative into your own apps


You can define editable areas, called placeholders, in your templates which you fill
with many different so called CMS content plugins.
A list of all the plugins can be found here:

`3rd party plugins <http://www.djangopackages.com/grids/g/django-cms/>`_ 

Should you be unable to find a suitable plugin for you needs, writing your own is very simple.

More information on `our website <http://www.django-cms.org>`_. 

*************
Documentation
*************

Please head over to our `documentation <http://docs.django-cms.org/>`_ for all
the details on how to install, extend and use the django CMS.

********
Tutorial
********

https://github.com/divio/django-cms-tutorial

***********
Quick Start
***********

You can use the `django CMS installer <https://github.com/nephila/djangocms-installer>`_::

    $ pip install --upgrade virtualenv
    $ virtualenv env
    $ source env/bin/activate
    (env) $ pip install djangocms-installer
    (env) $ djangocms -p . my_demo
    (env) $ cd my_demo

************
Getting Help
************

Please head over to our IRC channel, #django-cms, on irc.freenode.net or write
to our `mailing list <https://groups.google.com/forum/#!forum/django-cms>`_.

*******
Credits
*******

* Includes icons from `FamFamFam <http://www.famfamfam.com>`_.
* Python tree engine powered by
  `django-treebeard <https://tabo.pe/projects/django-treebeard/>`_.
* Javascript tree in admin uses `jsTree <http://www.jstree.com>`_.
* Many thanks to the
  `over 250 contributors <https://github.com/divio/django-cms/blob/master/AUTHORS>`_
  to the django CMS!

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

Open source enterprise content management system based on the Django framework.

.. image:: https://raw.githubusercontent.com/divio/django-cms/develop/docs/images/try-with-divio.png
   :target: http://try.django-cms.org/
   :alt: Try demo with Divio Cloud

.. ATTENTION::

    To propose **significant new features**, open pull requests based on and made against the **develop** branch. It's
    the branch for features that will go into the next django CMS feature release.

    To propose **fixes and backwards-compatible improvements**, please work on the latest **release** branch. This is
    the branch that will become the next PyPI release ("the next version of django CMS").

    Security fixes will be backported to older branches by the core team as appropriate.


********
Features
********

* hierarchical pages
* extensive built-in support for multilingual websites
* multi-site support
* draft/publish workflows
* version control
* a sophisticated publishing architecture, that's also usable in your own applications
* frontend content editing
* a hierarchical content structure for nested plugins
* an extensible navigation system that your own applications can hook into
* SEO-friendly URLs
* designed to integrate thoroughly into other applications

Developing applications that integrate with and take advantage of django CMS features is easy and well-documented.

More information on `our website <http://www.django-cms.org>`_.

************
Requirements
************

See the `Python/Django requirements for the current release version
<http://docs.django-cms.org/en/stable/#software-version-requirements-and-release-notes>`_ in our documentation.

See the `installation how-to guide for an overview of some other requirements and dependencies of the current release
<http://docs.django-cms.org/en/stable/how-to/install.html>`_

*************
Documentation
*************

We maintain documentation for several versions of the project. Key versions are:

* `stable <http://docs.django-cms.org>`_ (default), for the **current release** version
* `latest <http://docs.django-cms.org/en/latest/>`_, representing the latest build of the **release-3.4.x branch**
* `develop <http://docs.django-cms.org/en/develop/>`_, representing the latest build of the **develop branch**

For more information about our branch policy, see `Branches
<http://docs.django-cms.org/en/stable/contributing/development-policies.html>`_.

Our documentation is hosted courtesy of `Read the Docs <https://readthedocs.org>`_.


********
Tutorial
********

http://docs.django-cms.org/en/latest/introduction/index.html

***********
Quick Start
***********

You can use the `django CMS installer <https://djangocms-installer.readthedocs.io>`_::

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
  `over 515 contributors <https://github.com/divio/django-cms/blob/develop/AUTHORS>`_
  to the django CMS!

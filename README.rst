##########
django CMS
##########
.. image:: https://travis-ci.org/divio/django-cms.svg?branch=develop
    :target: https://travis-ci.org/divio/django-cms
.. image:: https://img.shields.io/pypi/v/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://img.shields.io/badge/wheel-yes-green.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://img.shields.io/pypi/l/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. image:: https://codeclimate.com/github/divio/django-cms/badges/gpa.svg
   :target: https://codeclimate.com/github/divio/django-cms
   :alt: Code Climate

Open source enterprise content management system based on the Django framework and backed by the non-profit django CMS Association. `Get involved in the dCA! <https://www.django-cms.org/en/contribute/>`_


.. ATTENTION::

    Please use the ``develop`` branch as the target for pull requests for on-going development.

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

More information on `our website <https://www.django-cms.org>`_.

************
Requirements
************

See the `Python/Django requirements for the current release version
<http://docs.django-cms.org/en/latest/#software-version-requirements-and-release-notes>`_ in our documentation.

See the `installation how-to guide for an overview of some other requirements and dependencies of the current release
<http://docs.django-cms.org/en/latest/how_to/install.html>`_

*************
Documentation
*************

We maintain documentation for several versions of the project. Key versions are:

* `stable <http://docs.django-cms.org>`_ (default), for the **current release** version
* `latest <http://docs.django-cms.org/en/latest/>`_, representing the latest build of the **release-3.4.x branch**
* `develop <http://docs.django-cms.org/en/develop/>`_, representing the latest build of the **develop branch**

For more information about our branch policy, see `Branches
<http://docs.django-cms.org/en/latest/contributing/development-policies.html>`_.

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

****
Demo
****

.. image:: https://raw.githubusercontent.com/divio/django-cms/develop/docs/images/try-with-divio.png
   :target: http://try.django-cms.org/
   :alt: Try demo with Divio Cloud

************
Getting Help
************

Please head over to our `Slack channel <https://www.django-cms.org/slack>`_ or our `discourse forum <https://discourse.django-cms.org/>`_ for support. 

******************
Commercial support
******************

This project is backed by the `django CMS Association <https://www.django-cms.org/about-us>`_.
If you need help implementing or hosting django CMS, please contact us:
info@django-cms.org.

**********************
django CMS Association
**********************

The django CMS Association is a non-profit organization that was founded in 2020 with the goal to drive the success of django CMS, by increasing customer happiness, market share and open-source contributions. We provide infrastructure and guidance for the django CMS project. 

The non-profit django CMS Association is dependent on donations to fulfilf its purpose. The best way to donate is to become a member of the association and pay membership fees. The funding will be funneled back into core development and community projects.

`Join the django CMS Association <https://www.django-cms.org/en/contribute/>`_.


*******
Credits
*******

* Includes icons from `FamFamFam <http://www.famfamfam.com>`_.
* Python tree engine powered by
  `django-treebeard <https://tabo.pe/projects/django-treebeard/>`_.
* JavaScript tree in admin uses `jsTree <https://www.jstree.com>`_.
* Many thanks to
  `all the contributors <https://github.com/django-cms/django-cms/graphs/contributors>`_
  to django CMS!

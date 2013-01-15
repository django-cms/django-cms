############
Installation
############

This document assumes you are familiar with Python and Django. It should
outline the steps necessary for you to follow the :doc:`tutorial`.

************
Requirements
************

* `Python`_ 2.5 (or a higher release of 2.x).
* `Django`_ 1.3.1 or 1.4.
* `South`_ 0.7.2 or higher
* `PIL`_ 1.1.6 or higher
* `django-classy-tags`_ 0.3.4.1 or higher
* `django-mptt`_ 0.5.2 (strict due to API compatibility issues)
* `django-sekizai`_ 0.6.1 or higher
* `html5lib`_ 0.90 or higher
* `django-i18nurls`_ (if using django 1.3.X)
* An installed and working instance of one of the databases listed in the
  `Databases`_ section.

.. note:: When installing the django CMS using pip, Django, django-mptt
          django-classy-tags, django-sekizai, south and html5lib will be
          installed automatically.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags
.. _django-mptt: https://github.com/django-mptt/django-mptt
.. _django-sekizai: https://github.com/ojii/django-sekizai
.. _html5lib: http://code.google.com/p/html5lib/
.. _django-i18nurls: https://github.com/brocaar/django-i18nurls

Recommended
===========

* `django-filer`_ with its `django CMS plugins`_, file and image management
  application to use instead of some core plugins
* `django-reversion`_ 1.6, to support versions of your content

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugins: https://github.com/stefanfoulis/cmsplugin-filer
.. _django-reversion: https://github.com/etianen/django-reversion

On Ubuntu
=========

.. warning::

    The instructions here install certain packages, such as PIL, Django, South
    and django CMS globally, which is not recommended. We recommend you use
    `virtualenv`_ instead. If you choose to do so, install Django,
    django CMS and South inside a virtualenv.

If you're using Ubuntu (tested with 10.10), the following should get you
started:

.. code-block:: bash

    sudo aptitude install python2.6 python-setuptools python-imaging
    sudo easy_install pip
    sudo pip install Django==1.4 django-cms south

Additionally, you need the Python driver for your selected database:

.. code-block:: bash

    sudo aptitude python-psycopg2

or

.. code-block:: bash

    sudo aptitude install python-mysql

This will install PIL and your database's driver globally.

You have now everything that is needed for you to follow the :doc:`tutorial`.


On Mac OSX
==========

**TODO** (Should setup everything up to but not including
"pip install django-cms" like the above)

On Microsoft Windows
====================

**TODO**.

*********
Databases
*********

We recommend using `PostgreSQL`_ or `MySQL`_ with django CMS. Installing and
maintaining database systems is outside the scope of this documentation, but is
very well documented on the systems' respective websites.

To use django CMS efficiently, we recommend:

* Creating a separate set of credentials for django CMS.
* Creating a separate database for django CMS to use.

.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.com
.. _virtualenv: http://www.virtualenv.org/

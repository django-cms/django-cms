############
Installation
############

This document assumes you are familiar with Python and Django, and should
outline the steps necessary for you to follow the :doc:`tutorial`.

************
Requirements
************

* `Python`_ 2.5 (or a higher release of 2.x).
* `Django`_ 1.2.3 (or a higher release of 1.2).
* `South`_ 0.7.2 or higher
* `PIL`_ 1.1.6 or higher
* `django-classy-tags`_ 0.2.2 or higher
* An installed and working instance of one of the databases listed in the
  `Databases`_ section.
  
.. note:: When installing the django CMS using pip, both Django and
          django-classy-tags will be installed automatically.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags

On Ubuntu
=========

If you're using Ubuntu (tested with 10.10), the following should get you
started:

``sudo aptitude install python2.6 python-setuptools python-imaging``

``sudo easy_install pip``

``sudo pip install django-cms south django-appmedia``

Additionally, you need the python driver for your selected database:

``sudo aptitude python-psycopg2``
or
``sudo aptitude install python-mysql``

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

We recommend using `PostgreSQL`_ or `MySQL`_ with Django CMS. Installing and
maintaining database systems is outside the scope of this documentation, but is
very well documented on the system's respective websites.

To use Django CMS efficiently, we recommend:

* Create a separate set of credentials for django CMS.
* Create a separate database for django CMS to use.

.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.com
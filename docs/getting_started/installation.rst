############
Installation
############

This document assumes you are familiar with Python and Django. It should
outline the steps necessary for you to follow the :doc:`tutorial`.

************
Requirements
************

* `Python`_ 2.5 (or a higher release of 2.x).
* `Django`_ 1.4.5, 1.5 or higher
* `South`_ 0.7.2 or higher
* `django-classy-tags`_ 0.3.4.1 or higher
* `django-mptt`_ 0.5.2 (strict due to API compatibility issues)
* `django-sekizai`_ 0.7 or higher
* `html5lib`_ 0.90 or higher
* `django-i18nurls`_ (if using django 1.3.X)
* An installed and working instance of one of the databases listed in the
  `Databases`_ section.

.. note:: When installing the django CMS using pip, Django, django-mptt
          django-classy-tags, django-sekizai, south and html5lib will be
          installed automatically.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags
.. _django-mptt: https://github.com/django-mptt/django-mptt
.. _django-sekizai: https://github.com/ojii/django-sekizai
.. _html5lib: http://code.google.com/p/html5lib/
.. _django-i18nurls: https://github.com/brocaar/django-i18nurls

Recommended
===========

These packages are not *required*, but they provide useful functionality with
minimal additional configuration and are well-proven.

File and image handling
-----------------------

* `Django Filer`_ for file and image management
* `django-filer plugins for django-cms`_, required to use Django Filer with django-cms
* `Pillow`_ (fork of PIL) for image manipulation

.. _Django Filer: https://github.com/stefanfoulis/django-filer
.. _django-filer plugins for django-cms: https://github.com/stefanfoulis/cmsplugin-filer
.. _Pillow: https://github.com/python-imaging/Pillow

Revision management
-------------------

* `django-reversion`_ 1.6.6 (with Django 1.4.5), 1.7 (with Django 1.5)
  to support versions of your content (If using a different Django version
  it is a good idea to check the page `Compatible-Django-Versions`_ in the
  django-reversion wiki in order to make sure that the package versions are
  compatible.)

  .. note::

    As of django CMS 2.4, only the most recent 25 published revisions are
    saved. You can change this behaviour if required with
    :setting:`CMS_MAX_PAGE_PUBLISH_REVERSIONS`. Be aware that saved revisions
    will cause your database size to increase.

.. _django-reversion: https://github.com/etianen/django-reversion
.. _Compatible-Django-Versions: https://github.com/etianen/django-reversion/wiki/Compatible-Django-Versions

************************************
Installing in a virtualenv using pip
************************************

Installing inside a `virtualenv`_ is the preferred way to install any Django installation. This should work on
any platform where python in installed. The first step is to create the virtualenv:

.. code-block:: bash

  #!/bin/sh
  sudo pip install --upgrade virtualenv
  virtualenv --distribute --no-site-packages env

You can switch to your virtualenv at the command line by typing:

.. code-block:: bash

  source env/bin/activate
  
Next, you can install packages one at a time using `pip`_, but we recommend using a `requirements.txt`_ file. The
following is an example requirements.txt file that can be used with pip to install django-cms and its dependencies:

::

    # Bare minimum
    django-cms==2.4.1
    
    #These dependencies are brought in by django-cms, but if you want to lock-in their version, specify them
    Django==1.5.1
    django-classy-tags==0.4
    South==0.8.1
    html5lib==1.0b1
    django-mptt==0.5.2
    django-sekizai==0.7
    six==1.3.0
    
    #Optional, recommended packages                
    Pillow==2.0.0
    django-filer==0.9.4      
    cmsplugin-filer==0.9.5   
    django-reversion==1.7
    
for Postgresql you would also add:

::

    psycopg2==2.5
    
and install libpq-dev (on Debian-based distro)

for MySQL you would also add:

::

    mysql-python==1.2.4

and install libmysqlclient-dev (on Debian-based distro)

One example of a script to create a virtualenv Python environment is as follows:

.. code-block:: bash

  #!/bin/sh
  env/bin/pip install --download-cache=~/.pip-cache -r requirements.txt

.. _virtualenv: http://www.virtualenv.org
.. _pip: http://www.pip-installer.org
.. _requirements.txt: http://www.pip-installer.org/en/latest/cookbook.html#requirements-files

*****************************
Installing globally on Ubuntu
*****************************

.. warning::

    The instructions here install certain packages, such as Django, South, Pillow
    and django CMS globally, which is not recommended. We recommend you use
    `virtualenv`_ instead (see above).

If you're using Ubuntu (tested with 10.10), the following should get you
started:

.. code-block:: bash

    sudo aptitude install python2.6 python-setuptools
    sudo easy_install pip
    sudo pip install Django==1.5 django-cms south Pillow

Additionally, you need the Python driver for your selected database:

.. code-block:: bash

    sudo aptitude python-psycopg2

or

.. code-block:: bash

    sudo aptitude install python-mysql

This will install Django, django CMS, South, Pillow, and your database's driver globally.

You have now everything that is needed for you to follow the :doc:`tutorial`.


*********
Databases
*********

We recommend using `PostgreSQL`_ or `MySQL`_ with django CMS. Installing and
maintaining database systems is outside the scope of this documentation, but
is very well documented on the systems' respective websites.

To use django CMS efficiently, we recommend:

* Creating a separate set of credentials for django CMS.
* Creating a separate database for django CMS to use.

.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.com

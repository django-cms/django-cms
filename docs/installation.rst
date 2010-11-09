Installation
============

This document assumes that you are familiar with python and django.

A more beginner friendly tutorial can be found `here <tutorial>`_.

Requirements
------------

* Python 2.5 (or a higher release of the 2.x). 2.4 might work, but is not
  supported.
* Django 1.2.3 (or a higher release of the 1.2). 1.3 might work, but is not
  supported yet.
* South 0.7 or higher

Apps
----

Required
~~~~~~~~

* ``django.contrib.auth``
* ``django.contrib.contenttypes``
* ``django.contrib.sessions``
* ``django.contrib.admin``
* ``django.contrib.sites``
* ``cms``
* ``mptt``
* ``menus``

.. warning:: mptt is shipped with django-cms and at the moment it is not possible
             to use a different version of django-mptt. If your project has
             other applications requiring mptt, they have to use the one from
             the cms which is version 0.3-pre.

Optional
~~~~~~~~

* ``cms.plugins.text``
* ``cms.plugins.picture``
* ``cms.plugins.link``
* ``cms.plugins.file``
* ``cms.plugins.snippet``
* ``cms.plugins.googlemap``
* ``publisher``


Middlewares
-----------

Note that the order is important:

#. ``django.contrib.sessions.middleware.SessionMiddleware``
#. ``cms.middleware.multilingual.MultilingualURLMiddleware``
#. ``django.contrib.auth.middleware.AuthenticationMiddleware`` 
#. ``django.middleware.common.CommonMiddleware``
#. ``cms.middleware.page.CurrentPageMiddleware``
#. ``cms.middleware.user.CurrentUserMiddleware``
#. ``cms.middleware.toolbar.ToolbarMiddleware``
#. ``cms.middleware.media.PlaceholderMediaMiddleware``

.. note:: For non-multilingual sites you may remove the 
          `cms.middleware.multilingual.MultilingualURLMiddleware` middleware.

Template Context Processors
---------------------------

* ``django.core.context_processors.auth``
* ``django.core.context_processors.i18n``
* ``django.core.context_processors.request``
* ``django.core.context_processors.media``
* ``cms.context_processors.media``

Templates
---------

You have to define at least one template in ``CMS_TEMPLATES`` which should
contain at least one ``{% placeholder '<name>' %}`` tag.

urls.py
-------

Include ``cms.urls`` **at the very end** of your urlpatterns. It **must** be the
last pattern in the list!

Media Files
-----------

Make sure your Django installation finds the cms media files, for this task we
recommend using django-appmedia which will create a symbolic link for you. If
for whatever reason you are unable to use it, copy the folder ``cms/media/cms``
into your main media folder.

South
-----

To avoid issues with migrations during the installation process it is currently
recommended to use ``python manage.py syncdb --all`` and
``python manage.py migrate --fake`` for **new** projects. Note that the cms
migrations can not be supported on sqlite3.


Troubleshooting
---------------

If you create a page and you don't see a page in the list view:

- Be sure you copied all the media files. Check with firebug and its "net" panel
  if you have any 404s

If you edit a Page but don't see a "Add Plugin" button and a dropdown-list
with plugins:

- Be sure your ``CMS_TEMPLATES`` setting is correct and that the templates
  specified actually exist and have at least one ``{% placeholder %}``
  templatetag in them template.

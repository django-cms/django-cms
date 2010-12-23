Installation
============

This document assumes you are familiar with Python and Django.

A more beginner-friendly tutorial can be found :doc:`here <tutorial>`.

Requirements
============

* `Python`_ 2.5 (or a higher release of 2.x). 2.4 might work, but is not
  supported.
* `Django`_ 1.2.3 (or a higher release of 1.2). 1.3 might work, but is not yet
  supported.
* `South`_ 0.7 or higher
* `PIL`_ 1.1.6 or higher
* `django-classy-tags`_ 0.2.2 or higher

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags

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

.. warning:: Django CMS ships with an older version of mptt (0.3-pre). Django
    CMS is not yet compatible with the latest version of django-mptt. If your
    project has other applications requiring mptt, they must use the mptt
    included with Django CMS.

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

You must define at least one template in ``CMS_TEMPLATES``, which should
contain at least one ``{% placeholder '<name>' %}`` tag.

urls.py
-------

Include ``cms.urls`` **at the very end** of your urlpatterns. It **must** be the
last pattern in the list!

Media Files
-----------

Make sure your Django installation finds the cms media files. We recommend
using django-appmedia, which will create a symbolic link for you. If
for whatever reason you are unable to use it, copy the folder ``cms/media/cms``
into your main media folder.

South
-----

To avoid issues with migrations during the installation process it is currently
recommended to use ``python manage.py syncdb --all`` and
``python manage.py migrate --fake`` for **new** projects. Note that cms
migrations are not supported with sqlite3.


Troubleshooting
---------------

If you've created a page & you don't see it in the cms list of the Django admin:

- Be sure you copied all the media files. Check with firebug and its "net" panel
  to see if you have any 404s.

If you're editing a Page in the Django admin, but don't see an "Add Plugin"
button with a dropdown-list of plugins:

- Be sure your ``CMS_TEMPLATES`` setting is correct, the templates specified
  exist, and they contain at least one ``{% placeholder %}`` templatetag.

Template errors
~~~~~~~~~~~~~~~
If your placeholder content isn't displayed when you view a CMS page: change the
CMS_MODERATOR variable in settings.py to False. This bug has been recently
fixed, so upgrade to the latest version of Django CMS. See:
https://github.com/divio/django-cms/issues/issue/430

Javascript errors
~~~~~~~~~~~~~~~~~
If plugins don't work (e.g.: you add a text plugin, but don't see the Javascript
text editor in the plugin window), you should use a Javascript inspector in your
browser to investigate the issue (e.g.: Firebug for Firefox, Web Inspector for
Safari or Chrome). The Javascript inspector may report the following errors:

- **TypeError: Result of expression 'jQuery' [undefined] is not a function.**

If you see this, check the ``MEDIA_URL`` variable in your settings.py file. Your
webserver (e.g.: Apache) should be configured to serve static media files from
this URL.

- **Unsafe JavaScript attempt to access frame with URL
  http://localhost/media/cms/wymeditor/iframe/default/wymiframe.html from frame
  with URL http://127.0.0.1:8000/admin/cms/page/1/edit-plugin/2/. Domains,
  protocols and ports must match.**

This error is due to the Django test server running on a different port and URL
than the main webserver. In your test environment, you can overcome this issue
by adding a CMS_MEDIA_URL variable to your settings.py file, and adding a url
rule in urls.py to make the Django development serve the Django CMS files from
this location.



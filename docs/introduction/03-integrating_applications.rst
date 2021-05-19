:sequential_nav: both

.. _integrating_applications:

########################
Integrating applications
########################

All the following sections of this tutorial are concerned with different ways of integrating other
applications into django CMS. The ease with which other applications can be built into django CMS
sites is an important feature of the system.

Integrating applications doesn't merely mean installing them alongside django CMS, so that they peacefully co-exist. It
means using django CMS's features to build them into a single coherent web project that speeds up the work of managing
the site, and makes possible richer and more automated publishing.

It's key to the way that django CMS integration works that **it doesn't require you to modify your other applications**
unless you want to. This is particularly important when you're using third-party applications and don't want to have to
maintain your own forked versions of them. (The only exception to this is if you decide to build django CMS features
directly into the applications themselves, for example when using :ref:`placeholders in other applications
<placeholders_outside_cms>`.)

For this tutorial, we're going to take a basic Django `opinion poll application
<https://github.com/divio/django-polls>`_ and integrate it into the CMS.

So we will:

* incorporate the Polls application into the project
* create a second, independent, *Polls/CMS Integration* application to manage the integration

This way we can integrate the Polls application without having to change anything in it.


*************************************
Incorporate the ``polls`` application
*************************************

Install ``polls``
=================

Install the application from its GitHub repository using ``pip``::

    pip install git+http://git@github.com/divio/django-polls.git#egg=polls

Let's add this application to our project. Add ``'polls'`` to the end of ``INSTALLED_APPS`` in
your project's `settings.py` (see the note on :ref:`installed_apps` about ordering ).

Add the ``poll`` URL configuration to ``urlpatterns`` in the project's ``urls.py``:

..  code-block:: python
    :emphasize-lines: 3

    urlpatterns += i18n_patterns(
        re_path(r'^admin/', include(admin.site.urls)),
        re_path(r'^polls/', include('polls.urls')),
        re_path(r'^', include('cms.urls')),
    )

Note that it must be included **before** the line for the django CMS URLs. django CMS's URL pattern
needs to be last, because it "swallows up" anything that hasn't already been matched by a previous
pattern.

Now run the application's migrations:

.. code-block:: bash

    python manage.py migrate polls

At this point you should be able to log in to the Django
admin - ``http://localhost:8000/admin/`` - and find the Polls application.

.. image:: /introduction/images/polls-admin.png
   :alt: the polls application admin
   :width: 400
   :align: center

Create a new **Poll**, for example:

* **Question**: *Which browser do you prefer?*

  **Choices**:

    * *Safari*
    * *Firefox*
    * *Chrome*

Now if you visit ``http://localhost:8000/en/polls/``, you should be able to see the published poll
and submit a response.

.. image:: /introduction/images/polls-unintegrated.png
   :alt: the polls application
   :width: 400
   :align: center


Improve the templates for Polls
===============================

You'll have noticed that in the Polls application we only have minimal templates, and no navigation or styling.

Our django CMS pages on the other hand have access to a number of default templates in the project, all of which
extend one called ``base.html``. So, let's improve this by overriding the polls application's base template.

We'll do this in the *project* directory.

In ``mysite/templates``, add ``polls/base.html``, containing:

.. code-block:: html+django

    {% extends 'base.html' %}

    {% block content %}
        {% block polls_content %}
        {% endblock %}
    {% endblock %}

Refresh the ``/polls/`` page again, which should now be properly integrated into the site.

.. image:: /introduction/images/polls-integrated.png
   :alt: the polls application, integrated
   :width: 400
   :align: center



**************************************************
Set up a new ``polls_cms_integration`` application
**************************************************

So far, however, the Polls application has been integrated into the project, but not into django CMS itself. The two
applications are completely independent. They cannot make use of each other's data or functionality.

Let's create the new *Polls/CMS Integration* application where we will bring them together.


Create the application
======================

Create a new package at the project root called ``polls_cms_integration``::

    python manage.py startapp polls_cms_integration

Our workspace now looks like this::

    tutorial-project/
        media/
        mysite/
        polls_cms_integration/  # the newly-created application
            __init__.py
            admin.py
            models.py
            migrations.py
            tests.py
            views.py
        static/
        manage.py
        project.db
        requirements.txt


Add it to ``INSTALLED_APPS``
============================

Next is to integrate the ``polls_cms_integration`` application into the project.

Add ``polls_cms_integration`` to ``INSTALLED_APPS`` in ``settings.py``  - and now we're ready to use it to begin
integrating Polls with django CMS. We'll start by :ref:`developing a Polls plugin <plugins_tutorial>`.

.. note::

    **Adding templates to the project or to the application?**

    Earlier, we added new templates to the project. We could equally well have have added ``templates/polls/base.html``
    inside ``polls_cms_integration``. After all, that's where we're going to be doing all the other integration work.

    However, we'd now have an application that makes assumptions about the name of the template it should extend (see
    the first line of the ``base.html`` template we created) which might not be correct for a different project.

    Also, we'd have to make sure that ``polls_cms_integration`` came *before* ``polls`` in ``INSTALLED_APPS``,
    otherwise the templates in ``polls_cms_integration`` would not in fact override the ones in ``polls``. Putting
    them in the project guarantees that they will override those in all applications.

    Either way of doing it is reasonable, as long as you understand their implications.

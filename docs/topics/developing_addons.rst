.. _best_practices_addons:

#############################################
Developing addon applications: best practices
#############################################

The django CMS ecosystem is part of its success - the third-party applications, plugins and
extensions that work well with it and add functionality.

A good addon application can become a popular open source project in its own right,

This document will describe some of the practices you can adopt to help ensure that yours can more
easily be used and improved by other developers, and will play nicely with other django CMS addons.

Some of these should be already familiar to anyone who has developed resusable Django applications,
because the same general principles apply.


======
Models
======

Field names
===========

Date and time
-------------

Use the ``_at`` suffix for ``datetime`` and the ``_on`` suffix for ``dates``.

Timestamps (which are usually automatically created) should be of the form ``created_at``,
``created_on``, ``modified_at``, ``modified_on`` and so on.

When time/date field controls something, use ``publish_at``, ``publish_until``, etc.

For quantities, use ``item_count``.

Reverse relations
-----------------

Use the default ``<modelname>_set`` for ForeignKeys. This avoids a lot of ambiguity and
complexity with irregular plural forms.

Database Fields
---------------

If a ForeignKey can be blank, it should also have ``on_delete=models.SET_NULL``, to avoid cascade
deletes of related objects. Be warned that many fields, such as Filer fields, are ForeignKeys even
if that's not immediately apparent.

Never allow settings or configuration to affect the names or structure of tables or fields.

=========
Templates
=========


Template readability counts. Don't worry about excess whitespace in templates as a result of
indentation.


Page templates
==============

Your addon application needs to be able to integrate well into django CMS projects that have their
own expectations of structure: internally within templates, across the hierarchy of template
directories and across the hierarchy of template inheritance.

An addon that publishes its own pages (i.e. does not merely insert plugins into existing pages)
will need access to a site-wide HTML template, so that its pages have the same look and feel as
others on the site.

This means that projects should provide a set of templates that can readily be used by different
applications - not, for example, designed around the expectations of just one application to the
exclusion of others. The :doc:`/topics/developing_projects` documentation offers some useful
guidance on this, and recommends that all projects should offer a ``base.html`` template that is in
turn inherited by the templates listed in :setting:`CMS_TEMPLATES`.

In turn, your addon should have a ``base.html`` that extends whichever template the CMS is using
for that part of the site. As in the case of the project's ``base.html``, this provides a basis for
all common page templates used by your addon; if you need other page templates in the addon, they
can extend ``base.html``.

 A minimal example::

    {% extends CMS_TEMPLATE %}

    {% block content %}
    {% endblock content %}

Having a ``{% block content %}`` in your site's templates is a good convention that makes it easy
for addons to target a known block for their content. Suppose your addon is called
``third_party_application``; in that case, use a structure like::

.. code-block:: text

    third_party_application
        templates/
            third_party_application/
                 base.html



Plugin templates
================


For plugins' templates, create a separate ``plugins`` folder within your application. The name of
the added html file should represent the functionality of the plugin. Here's an example with our
previous structure:

.. code-block:: text

    third_party_application
        templates/
            third_party_application/
                plugins/
                    excuse_generator.html
                base.html


In some cases plugins themselves need templates that provide different themes or variants based on
a common starting point. A recommended structure then might be something like:

.. code-block:: text

    third_party_application
        templates/
            third_party_application/
                plugins/
                    base.html
                    excuse_generator.html
                    complaint_generator.html
                base.html


Compatibility with Aldryn Boilerplates
======================================

Aldryn Boilerplates are complete django CMS site setups, built around rich frontend frameworks. You
don't need to use the `Aldryn <http://aldryn.com>`_ platform to use them; they are free and open
source. See `Aldryn Boilerplate Bootstrap 3
<http://aldryn-boilerplate-bootstrap3.readthedocs.org>`_ for an example.

It's fairly straightforward to build support for Boilerplates into your addons, for example, by
applying CSS classes to the elements in the HTML to take advantage of the Boilerplate's CSS and
JavaScript provisions.

In this case, for each Boilerplate you'd like to support in your application, also add a set of
templates at::

    boilerplates/boilerplate_name/templates/

For example::

    third_party_application
        templates/
            third_party_application/
                 base.html
        boilerplates/
            aldryn_boilerplate_bootstrap3/
                templates/
                    third_party_application/
                         base.html
            boilerplate_name/
                templates/
                    third_party_application/
                         base.html

and do this for as many Boilerplates as you wish to support.

This does of course mean more work for you as a project maintainer. The payoff is enhanced
compatibility with multiple Boilerplates.

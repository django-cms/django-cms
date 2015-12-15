###########################################################
Exploring applications
###########################################################

In this section you will learn about:

* applications in the **Aldryn Essentials collection**
* **Aldryn Forms** and **Aldryn Categories**
* the **Aldryn Marketplace** and **django CMS addons**
* finding other addons

We've already explored a number of applications, including of course django CMS itself, and also:

* Aldryn News & Blog
* Aldryn People
* Aldryn Bootstrap 3
* Django Filer

Much of the power and functionality in a django CMS site comes not just from django CMS or other
applications, but the way in which they integrate seamlessly.

Many other applications have been created for django CMS, for all kinds of purposes. This site
includes just a few of them.


***************************
Aldryn Essential Collection
***************************

Aldryn News & Blog and Aldryn People are part of the *Essential Collection*, a suite of applications
designed to work in similar ways and provide common patterns and interfaces.

The others are:

* Aldryn Jobs
* Aldryn Events
* Aldryn FAQ

Typically, you'll use them in the same way you used News & Blog and People:

#.  Create a landing page for the application.

#.  In the page's *Advanced settings*, create an apphook to hook the application into the page.

#.  Create the items (jobs, events, FAQs) that the application is designed to manage; these will be
    published on its landing page.

#.  If you wish, use plugins to re-use the content from these applications in other contexts.


******************
Other applications
******************

Other applications of note available in this site include:


Aldryn Forms
============

Place forms on your pages, and collect responses.

Aldryn Forms, unlike the applications in the Essentials collection, requires some knowledge of
HTML to use well, but the basic operation is:

#.  Add a *Form* plugin to a placeholder.

#.  Configure the *Form's* options.

#.  Into the *Form*, insert *Fieldset*, field, and *Submit* plugins as appropriate. You *will* need
    to assemble a form with correct structure and components, but if you know a little about forms
    in HTML, this will be fairly straightforward.

Responses will be emailed to any recipients specified, and also stored in the database (and
available in the *Aldryn Forms* application in the Django admin.


Aldryn Categories
=================

Aldryn Categories is a utility Addon that provides your other applications with hierarchical categories.

The categories you define in Aldryn Categories can be re-used by any Categories-aware application,
including News & Blog, Events, People, Jobs and FAQ.

This means that the same hierarchies of categories can be available across your site's applications.


****************************************
Aldryn Marketplace and django CMS Addons
****************************************

The `Aldryn Marketplace <http://www.aldryn.com/en/marketplace/aldryn-categories/>`_ and `django CMS
Addons <http://www.django-cms.org/en/addons/>`_ pages are curated lists of applications that have
been tested and are known to work well with django CMS (and if you find any that don't, please tell
us!).

Applications on the Aldryn Marketplace are available to Aldryn sites (like the tutorial site)
through a one-click installer on the `Aldryn Control Panel <https://control.aldryn.com>`_.

Applications listed on the django CMS Addons page might not all be on Aldryn, in which case you,
or whoever is responsible for deploying your site, will have to install and configure them
manually.


******************
Other applications
******************

There is also a vast range of applications that have been designed to integrate and inter-operate
with django CMS. Most of them are also free open source packages.

You can find them on `PyPI <http://pypi.python.org>`_, `Django Packages
<https://www.djangopackages.com/grids/g/django-cms/>`_ and on services like GitHub, as well as
tucked away into the obscurer corners of the web.

Some of them are more complete and polished than others; some will be of general interest, and some
will be of very specialised (legal, scientific, management, etc) interest.

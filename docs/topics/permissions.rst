###########
Permissions
###########

The django CMS permissions system is flexible, granular and multi-layered - it can however also sometimes seem a little
confusing!

It's important to understand its parts and how they interact in order to use it effectively.

In django CMS permissions can be granted:

* that determine **what actions a user may perform**
* that determine **on which parts of the site they may perform them**

These two dimensions of permissions are independent of each other. See :ref:`permission-strategies` below.


***********************
``CMS_PERMISSION`` mode
***********************

The first thing to understand is that as far as permissions are concerned django CMS operates in one of two modes, depending
on the :setting:`CMS_PERMISSION` setting:

* ``False`` (the default): only the standard Django Users and Groups permissions will apply
* ``True``: as well as standard Django permissions, django CMS applies a layer of permissions control
  affecting *pages*


``CMS_PERMISSION`` mode *off*
=============================

When django CMS's own permission system is disabled, you have no control over permissions over particular pages. In other
words, *row-level controls on pages* do not exist.

You still have control over **what functionality** particular users and groups have in the CMS, but not over **which
content** they can exercise it on.


Key user permissions
--------------------

You can find the permissions you can set for a user or groups in the Django admin, in the *Authentication and Authorization*
section.

Filtering by ``cms`` will show the ones that belong to the CMS application. Permissions that a CMS editor will need are
likely to include:

* ``cms | cms plugin``
* ``cms | page``
* ``cms | placeholder``
* ``cms | placeholder reference``
* ``cms | static placeholder``
* ``cms | placeholder reference``
* ``cms | title``

Most of these offer the usual add/change/delete options, though there are some exceptions, such as ``cms | placeholder |
Can use Structure mode``.

Users with permission to do something to a CMS model will be able to do it to *all* instances of that model when
``CMS_PERMISSION`` mode is *off*


``CMS_PERMISSION`` mode *on*
============================

When django CMS's permission system is enabled, a new layer of permissions is **added**, and permissions over CMS page-related
models will need to be provided **in addition** to those granted in Django's *Authentication and Authorization* models.

In other words, **both** Django's and django CMS's permissions will need to be granted over pages if an editor is to have
access to them.

By default, when ``CMS_PERMISSION`` mode is enabled, users will not be able to edit CMS pages unless they are Django
superusers. This is rarely desirable, so you will probably wish to configure the CMS permissions to provide more nuanced
control.

See :ref:`page-permissions` below for more.

New admin models
----------------

When ``CMS_PERMISSION`` is enabled, you'll find three new models available in the admin:

* :ref:`Pages global permissions <pages-global-permissions>`
* *User groups (page)*
* *Users (page)*

You will find that the latter two simply reflect the Django Groups and User permissions that already exist in the system. They are a simpler representation of the available permissions, specific to page editing. You'll often find it more useful
to use the Django Groups and User permissions.

:ref:`Pages global permissions <pages-global-permissions>` are described below.

.. _page-permissions:

Page permissions
================

When ``CMS_PERMISSION`` is enabled, unless you simply make your users superusers, you'll need to give each one either global
permission, or permission over specific pages (:ref:`preferably via their membership of a group <use-permissions-on-groups>`
in either case).

Both global and specific permission granting are described below.


.. _pages-global-permissions:

Global page permissions
-----------------------

*Pages global permissions* are available in the admin, in the *django CMS* section.

The first two options for a global permission concern **whom** they apply to.

Then there is list of **what actions** the editor can perform. The editors will need at least *some* of these if they are to
manage pages.

Finally, there's a list of the **sites** they can perform the actions on.


.. _pages-specific-permissions:

Page-specific permissions
-------------------------

The CMS permissions system also provides permisions control for particular pages or hierarchies of pages in the site -
row-level permissions, in other words.

These are controlled by selecting *Permissions* from the *Page* menu in the toolbar when on the page (this options is only
available when ``CMS_PERMISSION`` mode is on).

*Login required* determines whether anonymous visitors will be able to see the page at all.

*Menu visibility* determines who'll be able to see the page in navigation menus - everyone, or logged in or anonymous users
only.

*View restrictions* determine which groups and users will be able to see the page. Adding a view restriction will allow you
to set this. Note that this doesn't apply new restrictions to users who are also editors with appropriate permissions.

*Page permissions* determine what editors can do to a page (or hierarchy of pages). They work just like the *Pages global
permissions* described above, but don't apply globally. They are **added to** global permissions - they don't override them.

The *Can change permission* refers to whether the user can change the permissions of a "subordinate" users Bob is the
subordinate of Alice if one of:

* Bob was created by Alice
* Bob has at least one page permission set on one of the pages on which Alice has the *Can change permissions* right

.. _important:

    Even though a user may have permissions to change a page, that doesn't give them permissions to add or change plugins
    *within* that page. In order to be able to add/change/delete plugins on any page, you will need to go through the
    standard Django permissions to provide users with the actions they can perform.

    Even if a *page permission* allows a user to edit pages in general (global) or a particular page (specific), they will
    still need ``cms | page | Can publish page`` permission to publish it, ``cms | cms plugins | Can edit cms plugin`` to
    edit plugins on the page, and so on.

    This is because the page permissions system is an additional layer over the Django permissions system.


.. _permission-strategies:

*********************
Permission strategies
*********************

For a simple site with only a few users you may not need to be concerned about this, but with thousands of pages belonging to
different departments and users with greatly differing levels of authority and expertise, it is important to understand who
is able to do what on your site.


Two dimensions of permissions
=============================

As noted earlier, it's useful to think of your users' permissions across two dimensions:

* what sort of things this user or group of user should be allowed to do (e.g. publish pages, add new plugins, create new
  users, etc)
* which sections of the site the user should be allowed to do them on (the home page, a limited set of departmental pages,
  etc)


.. _use-permissions-on-groups:

Use permissions on Groups, not on Users
=======================================

Avoid applying permissions to individual users unless strictly necessary. It's far better to apply them to Groups, and add
Users to Groups. Otherwise, you risk ending up with large numbers of Users with unknown or inappropriate permissions.


Use Groups to build up permissions
==================================

Different users may require different subsets of permissions. For example, you could define a *Basic content editor* group,
who can edit and publish pages and content, but who don't have permission to create new ones; that permission would be
granted to a *Lead content editor* Group. Another Group could have permissions to use the weblog.

Some users should be allowed to edit some pages but not others. So, you could create a *Pharmacy department* and a *Neurology
department* group, which don't actually have any permissions of their own, but give each one
:ref:`pages-specific-permissions` on the appropriate landing page of the website.

Then, when managing a user, place the user into the appropriate groups.


Global or specific page permissions?
====================================

In a simple site, if you have ``CMS_PERMISSION`` enabled, add a global permission so that all editors can edit all pages.

If you need more control, only allow select users access to the global permission, but add specific page permissions to
pages as appropriate for the other editors.

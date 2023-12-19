###########
Permissions
###########

The django CMS permissions system is flexible, granular and multi-layered.


****************
Permission modes
****************

Permissions operate in two different modes, depending on the :setting:`CMS_PERMISSION` setting.

* Simple permissions mode (``CMS_PERMISSION = False``): only the standard Django Users and Groups
  permissions will apply. This is the default.
* Page permissions mode (``CMS_PERMISSION = True``): as well as standard Django permissions, django
  CMS provides row-level permissions on pages, allowing you to control the access of users to
  different sections of a site, and sites within a multi-site project.

.. _key-user-permissions:

********************
Key user permissions
********************

You can find the permissions you can set for a user or groups in the Django admin, in the
*Authentication and Authorization* section. These apply equally in Simple permissions mode and
Page permissions mode.

Filtering by ``cms`` will show the ones that belong to the CMS application. Permissions that a CMS
editor will need are likely to include:

* ``cms | cms plugin``
* ``cms | page``
* ``cms | placeholder``
* ``cms | placeholder reference``
* ``cms | static placeholder``
* ``cms | placeholder reference``
* ``cms | title``

Most of these offer the usual add/change/delete options, though there are some exceptions, such as
``cms | placeholder | Can use Structure mode``.

See :ref:`use-permissions-on-groups` below on applying permissions to groups rather than users.


************************************
Permissions in Page permissions mode
************************************

In Page permissions mode, you also need to give users permission to the right pages and sub-sites.


.. _global-and-per-page-permissions:

Global and per-page permissions
===============================

This can be done in two ways, *globally* or *per-page*.

.. _pages-global-permissions:

**Global page permissions** apply to all pages (or all pages on a sub-site in a multi-site
project). Global page permissions are managed in the admin at *django CMS* > *Pages global
permissions*.

**Per-page permissions** apply to a specific page and/or its children and/or its descendants.
Per-page permissions are managed via the toolbar (*Page* > *Permissions*) when on the page in
question, in edit mode.

Your users (unless they are Django superusers) will need at least one of global page permissions or
per-page permissions granted to them in order to be able to edit any pages at all.

They will **also** need appropriate :ref:`user permissions <key-user-permissions>`, otherwise they
will have no edit rights to pages.

.. _page-permission-options:

Page permission options
=======================

Both global page permissions and per-page permissions can be assigned to users or groups of users.
They include:

* *Can add*
* *Can edit*
* *Can delete*
* *Can publish*
* *Can change advanced settings*
* *Can change permissions*
* *Can move*

.. _important:

    Even though a user may have *Can edit* permissions on a page, that doesn't give them
    permissions to add or change plugins *within* that page. In order to be able to
    add/change/delete plugins on any page, you will need to go through :ref:`the standard Django
    permissions <key-user-permissions>` to provide users with the actions they can perform, for
    example:

    * ``cms | page | Can publish page`` to publish it
    * ``cms | cms plugins | Can edit cms plugin`` to edit plugins on the page


.. _pages-specific-permissions:

Per-page permissions
====================

Per-page permissions are controlled by selecting *Permissions* from the *Page* menu in the toolbar
when on the page (this options is only available when ``CMS_PERMISSION`` mode is on).

*Login required* determines whether anonymous visitors will be able to see the page at all.

*Menu visibility* determines who'll be able to see the page in navigation menus - everyone, or logged in or anonymous users
only.

.. _view-restrictions:

*View restrictions* determine which groups and users will be able to see the page when it is
published. Adding a view restriction will allow you to set this. Note that this doesn't apply any
restrictions to users who are also editors with appropriate permissions.

*Page permissions* determine what editors can do to a page (or hierarchy of pages). They are
described above in :ref:`page-permission-options`.


New admin models
----------------

When ``CMS_PERMISSION`` is enabled, as well as :ref:`Pages global permissions
<pages-global-permissions>` you will find two new models available in the CMS admin:

* *User groups (page)*
* *Users (page)*

You will find that the latter two simply reflect the Django Groups and User permissions that
already exist in the system, and can be ignored.


.. _permission-strategies:

*********************
Permission strategies
*********************

For a simple site with only a few users you may not need to be concerned about this, but with
thousands of pages belonging to different departments and users with greatly differing levels of
authority and expertise, it is important to understand who is able to do what on your site.


.. _use-permissions-on-groups:

Use permissions on Groups, not on Users
=======================================

Avoid applying permissions to individual users unless strictly necessary. It's far better to apply
them to Groups, and add Users to Groups. Otherwise, you risk ending up with large numbers of Users
with unknown or inappropriate permissions.


Use Groups to build up permissions
==================================

Different users may require different subsets of permissions. For example, you could define a
*Basic content editor* group, who can edit and publish pages and content, but who don't have
permission to create new ones; that permission would be granted to a *Lead content editor* Group.
Another Group could have permissions to use the weblog.

Then, when managing a user, place the user into the appropriate groups.


Two dimensions of permissions
-----------------------------

You can divide your users' permissions across two dimensions:

* what sort of things this user or group of user should be allowed to do (e.g. publish pages, add
  new plugins, create new users, etc)
* which sections of the site the user should be allowed to do them on (the home page, a limited set
  of departmental pages, etc)

Groups are very useful for managing this. For example, you can create a *Europe* group for editors
who are allowed to edit the Europe page hierarchy or sub-site. The group can then be added to a
:ref:`global or per-page permission <global-and-per-page-permissions>`.

###########
Permissions
###########

In django CMS you can set three types of permissions:

#. View restrictions for restricting front-end view access to users
#. Page permissions for allowing staff users to only have rights on certain sections of certain sites
#. Mode permission which when left unset, restricts staff users to only editing, not adding new content

To enable features 1. and 2., ``settings.py`` requires::

    CMS_PERMISSION = True

The third one is controlled by the "**Can use Structure mode**" Django permission.

*****************
View restrictions
*****************

View restrictions can be set-up from the *View restrictions* formset on any cms page.
Once a page has at least one view restriction installed, only users with granted access will be able to see that page.
Mind that this restriction is for viewing the page as an end-user (front-end view), not viewing the page in the admin interface!

View restrictions are also controlled by the ``CMS_PUBLIC_FOR`` setting. Possible values are ``all`` and ``staff``.
This setting decides if pages without any view restrictions are:

* viewable by everyone -- including anonymous users (*all*)
* viewable by staff users only (*staff*)

****************
Page permissions
****************

After setting ``CMS_PERMISSION = True`` you will have three new models in the admin index:

1. Users (page)
2. User groups (page)
3. Pages global permissions

.. _users-page-permissions:

Users (page) / User groups (page)
=================================

Using *Users (page)* you can easily add users with permissions over CMS pages.

You would be able to create a user with the same set of permissions using the usual *Auth.User* model, but using *Users (page)* is more convenient.

A new user created using *Users (page)* with given page add/edit/delete rights will not be able to make any changes to pages straight away.
The user must first be assigned to a set of pages over which he may exercise these rights.
This is done using the :ref:`page-permissions`. formset on any page or by using :ref:`pages-global-permissions`.

*User groups (page)* manages the same feature on the group level.

.. _page-permissions:

Page permissions
================

The *Page permission* formset has multiple checkboxes defining different permissions: can edit, can add, can delete, can change advanced settings, can publish, can move and can change permission.
These define what kind of actions the user/group can do on the pages on which the permissions are being granted through the *Grant on* drop-down.

*Can change permission* refers to whether the user can change the permissions of his subordinate users. Bob is the subordinate of Alice if one of:

* Bob was created by Alice
* Bob has at least one page permission set on one of the pages on which Alice has the *Can change permissions* right


**Note:** Mind that even though a new user has permissions to change a page, that doesn't give him permissions to add a plugin within that page.
In order to be able to add/change/delete plugins on any page, you will need to go through the usual *Auth.User* model and give the new user permissions to each plugin you want him to have access to.
Example: if you want the new user to be able to use the text plugin, you will need to give him the following rights: ``text | text | Can add text``, ``text | text | Can change text``, ``text | text | Can delete text``.

.. _pages-global-permissions:

Pages global permissions
========================

Using the *Pages global permissions* model you can give a set of permissions to all pages in a set of sites.

.. note:: You always **must** set the sites managed py the global permissions, even if you only have one site.

.. _structure_mode_permissions:

********************
Edit mode permission
********************

.. versionchanged:: 3.1

django CMS uses **Structure** and **Content** modes for different type of content editing;
while the former allows full control over the plugins layout, positioning and to add new
plugins to the page, the latter only allow editing existing plugins.

From version 3.1 the specific permission "**Can use Structure mode**" exists to permit access
to Structure Mode. This allows defining a different level of permissions on the same content.

This permission also applies to ``PlaceholderField`` defined on models.

****************
File Permissions
****************

django CMS does not take care of and no responsibility for controlling access to files. Please make sure to use either
a pre-built solution (like `django-filer <https://github.com/divio/django-filer>`_) or to roll your own.

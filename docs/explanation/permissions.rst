###########
Permissions
###########

The django CMS permissions system is flexible, granular and multi-layered.

For step-by-step setup of users and groups, see the Django admin and
your project's permission how-to (under construction). This page is
about *why* the system looks the way it does.

*********************
Roles, not just users
*********************

A team using a CMS usually has more than one kind of user. django CMS
is shaped around four loose roles, even though Django itself only
knows about users and groups:

**Author**
    Creates and edits draft content. Cannot publish. Often the
    largest group on a content-heavy site.

**Editor**
    Reviews, edits, and publishes. The role that needs publish
    permission; otherwise looks like an author with more rights.

**Designer**
    Owns templates, styles, and the layout vocabulary. Works in
    code, not in the toolbar. Permission-wise this is usually a
    developer with deployment access — not a CMS user role at all.

**Site administrator**
    Manages users, groups, permissions, deployment, and project
    configuration. Often a Django superuser.

The permission system below is the mechanism that lets you map these
roles onto users and groups. The system does not care what you call
your groups; it only enforces what each group is allowed to do.


*********************
Two layers, two modes
*********************

There are two layers of permissions in any django CMS project:

1. **Django auth permissions** (always on). The standard
   per-model add / change / delete permissions Django gives to every
   model. CMS models — ``Page``, ``PageContent``, ``Placeholder``,
   ``CMSPlugin``, and so on — participate in this system like any
   other Django model. Configured in the Django admin under
   *Authentication and Authorization*.
2. **CMS per-page permissions** (off by default). Row-level
   permissions on individual pages or page subtrees: "this group can
   edit pages under ``/legal/``, but not under ``/marketing/``".
   Configured per project by the :setting:`CMS_PERMISSION` setting.

The setting controls which model the second layer follows:

* ``CMS_PERMISSION = False`` — only Django auth applies. Whoever can
  edit pages can edit *all* pages. Simple, predictable, sufficient
  for small teams and single-domain sites.
* ``CMS_PERMISSION = True`` — Django auth still applies, *and* on top
  of it the CMS checks per-page permissions for each request. Needed
  when different groups should own different parts of the page tree,
  or when a multi-site project needs editors scoped to one site.

Turning ``CMS_PERMISSION`` on is not free: every page operation now
involves additional database lookups, and the admin grows several new
forms that a small team may find more confusing than helpful. Switch
it on when you need it, not by default.

****************************
Two dimensions of permission
****************************

Whichever mode is on, permissions divide along **two independent
dimensions**:

* **What** the user is allowed to do — add, change, delete, publish,
  change advanced settings, move pages in the tree.
* **Where** they are allowed to do it — globally (all pages on a
  site), or only on a specific page subtree.

A *Basic editor* group might have "can change" on the *what* axis
and "all pages on site X" on the *where* axis. A *Legal team*
group might have the same *what* permissions but be restricted to
the ``/legal/`` subtree on the *where* axis.

The *where* dimension only exists when ``CMS_PERMISSION = True``. In
the simpler mode, every CMS permission applies to every page.

The two models that implement the *where* dimension are:

* :class:`~cms.models.permissionmodels.GlobalPagePermission` — applies
  to all pages of one or more sites.
* :class:`~cms.models.permissionmodels.PagePermission` — applies to a
  specific page, optionally cascading to its descendants.


***************************************
Permissions for plugins, not just pages
***************************************

A common surprise: granting a user "can change" on a page does *not*
let them add or edit the plugins inside that page. Plugins are their
own model with their own permissions.

The split is intentional. Plugins are reusable components defined by
add-on packages; their permissions are managed alongside the package
that defines them, not alongside the page. To grant an editor the
right to add and edit plugins on a page they can already edit, give
their group the standard Django auth permissions on the relevant
plugin models (``djangocms_text.text``, ``djangocms_frontend.uiitem``,
your custom plugin model, and so on).

If this feels like permission sprawl, you are not alone. The
:doc:`/how_to/20-cms-config` mechanism and convenience admin actions
exist partly to reduce the per-package plumbing.

*************************************
Publishing and the versioning package
*************************************

"Can publish" is the most-asked-about CMS permission. It is also the
one most affected by which versioning package is installed.

Without a versioning package, **there is no publish action** to
permit. Saving a ``PageContent`` row is what makes it visible. See
:ref:`publishing`.

With ``djangocms-versioning`` installed, **publish becomes a distinct
step** with its own permission, separate from "change". A common
group design is:

* *Authors* — can add and change page content; cannot publish.
* *Editors* — same as authors, plus can publish.

The "Can publish" permission is granted on the relevant content
version models exposed by ``djangocms-versioning`` (e.g.
``django CMS Versioning | page content version``). Different
versioning packages may model this differently; check the package's
own documentation for the exact permission names.

If your project uses :doc:`/how_to/20-cms-config` to register custom
content models, those models participate in the same versioning
contract and inherit the same publish permission model.

*************************************
View restrictions vs edit permissions
*************************************

A separate concern, often confused with edit permissions: who is
allowed to *see* a published page.

* **Login-required pages.** Available without ``CMS_PERMISSION``. A
  page can be marked as requiring login; anonymous visitors are
  redirected to log in.
* **View restrictions per group.** Available only with
  ``CMS_PERMISSION = True``. A page can be restricted so that only
  members of specific groups can see it. Useful for intranet
  sections, customer portals, or pre-launch staging pages.
* **Menu visibility.** Independent of view restrictions: a page can
  be hidden from menus while remaining reachable by URL, or shown
  only to anonymous (logged-out) visitors, or only to authenticated
  ones.

These three controls are layered. A page can be in the menu for
logged-in users (menu visibility), require login to view at all
(login-required), and be further restricted to one group (view
restriction).

**These are front-end controls only.** View restrictions,
login-required, and menu visibility all govern who can *see a
published page on the public site*. They do **not** hide a page inside
the admin. The page tree in the admin — and the page-link
autocomplete used by the smart-link field, which mirrors it — list
*every* page on a site to any staff user who can edit at least one
page on that site. Such a user can therefore see the titles, paths,
and URLs of restricted, login-required, and draft pages, even ones
they cannot view on the front end or edit. Per-page edit permissions
gate the *actions* offered on each node (edit, move, delete), not
whether the node is listed.

In other words, a page title or path is not a secret from your staff
editors. If a page's *existence* must be hidden from some staff users,
the page tree is the wrong tool: keep that content on a separate site
(see :setting:`CMS_PERMISSION` and multi-site setups) or outside the
CMS, rather than relying on a view restriction to conceal it in the
admin.


*************************
Delegated user management
*************************

With ``CMS_PERMISSION = True`` a non-superuser can be given the right
to manage *other* users — the "Users" and "User groups" entries in the
admin become available to anyone who has the ``change`` permission on
the CMS user/group models and a page-permission level of their own.
These users are **page-user managers**. They are not superusers, yet
inside their own corner of the system they act with superuser-like
authority.

The mental model is deliberate: **a page-user manager is a superuser
for their subordinate users only.** A user is "subordinate" when the
manager created them, or when they sit at the same or a lower level in
the page tree the manager controls. Within that subordinate set, the
manager can do almost everything a superuser could do to those
accounts:

* create new staff users (new page-users are made staff automatically);
* grant and revoke any permission or group the manager *themselves*
  holds — they cannot hand out rights they do not have;
* edit account status fields, including ``is_staff`` (admin-login
  capability) and ``is_active`` (whether the account may log in at
  all).

The single boundary a manager cannot cross is **superuser status**:
``is_superuser`` is read-only for non-superusers, so a manager can
never promote a subordinate (or themselves) to full superuser.

**A manager can reverse a setting a superuser made.** This follows
directly from the model and is worth stating plainly. If a superuser
disables a subordinate account (``is_active = False``) or removes its
staff flag (``is_staff = False``), a page-user manager with that user
in their subordinate set can switch it back on. The manager's authority
over a subordinate is not subordinate to the superuser's earlier edit;
it is the *same* authority over that account, minus the ability to
grant superuser. If you need a deactivation or a demotion to be
permanent against a manager, the user must be moved out of that
manager's subordinate set — for example by deleting the account, or by
re-parenting it above the manager's page-tree level — rather than
relying on the status flag alone.

This is intentional delegation, not a gap: the whole point of a
page-user manager is to off-load routine account administration from
the superuser. Hand the role only to people you would trust with the
accounts it covers.


********
Strategy
********

A few guidelines that hold regardless of which mode you are in:

**Apply permissions to Groups, not Users.** Per-user permissions
drift quickly. After a year, no one will remember why a specific
user has a specific permission. Group-based grants survive staff
changes and are auditable.

**Compose Groups by responsibility, not by person.** A *Basic
editor* group, a *Lead editor* group, a *Blog editor* group, a
*Legal* group. Users land in one or more of these based on what
they do. Avoid groups named after individuals or departments
("Marketing") unless the departmental boundary is also the
permission boundary.

**Start in simple mode.** Leave ``CMS_PERMISSION = False`` until you
have a concrete reason to switch. Most teams that turn it on at
the start later wish they had not — the additional admin surface is
real, and re-engineering away from it is harder than adopting it
later.

**Permissions are not a substitute for trust.** Anyone with the
"change permissions" right can grant themselves more rights. The
boundary that matters most in practice is who gets superuser; tighten
that first.

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
editor will need are likely to include the following core package permissions:

* ``django CMS | cms plugin``
* ``django CMS | page``
* ``django CMS | placeholder``
* ``django CMS | placeholder reference``

Most of these offer the usual add/change/delete options, though there are some exceptions, such as
``django CMS | placeholder | Can use Structure mode``.

In addition to the core package permissions, an editor will likely need the following permissions
from 3rd-party packages:

* `djangocms-alias <https://pypi.org/project/djangocms-alias/>`_

  * ``django CMS Alias | alias``
  * ``django CMS Alias | alias content``
  * ``django CMS Alias | category``

* `djangocms-frontend <https://pypi.org/project/djangocms-frontend/>`_

  * ``django CMS Frontend | UI item``
  * After adding these permissions, save and use the ``python manage.py frontend sync_permissions``
    command as documented in `djangocms-frontend's documentation
    <https://djangocms-frontend.readthedocs.io/en/stable/tutorial/builtin_components.html#assigning-permissions>`_

* `djangocms-text <https://pypi.org/project/djangocms-text/>`_

  * ``django CMS Rich Text | text``

* `djangocms-versioning <https://pypi.org/project/djangocms-versioning/>`_

  * ``django CMS Versioning | alias content version``
  * ``django CMS Versioning | page content version``
  * ``django CMS Versioning | version``

Typically when adding other 3rd party packages or custom plugins you may need to add additional
permissions to enable their features. Sometimes documentation for such needed permissions may be
missing, in that case you can compare the list of available permissions with the package enabled
and disabled on your site.

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

###########
Permissions
###########

django CMS sits on top of Django's standard auth system and adds a
second, optional layer of **per-page permissions** for projects that
need finer control. This page explains how those two layers fit
together, the roles they are designed to support, and the trade-offs
that come with each.


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
Where to go next
****************

* :ref:`content_objects` — pages, page content, and the grouper /
  content split that the permission system protects.
* :ref:`publishing` — how publishing depends on the versioning
  package, and what that means for the "Can publish" permission.
* :doc:`/reference/permissions` — the authoritative list of CMS
  permission models and fields.
* :doc:`/reference/configuration` — the :setting:`CMS_PERMISSION`
  setting and related options.

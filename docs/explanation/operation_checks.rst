.. _operation_checks:

################
Operation checks
################

Before django CMS changes content (moving a page, adding a plugin), it asks one
question: *may this operation happen?* This page explains where that question is
answered, how packages add their own answers to it, and how anything, from the
page tree to an API or an assistant, can ask it without changing anything.
The functions and signals are listed in :ref:`operations_reference`.

.. note::

    Operation checks are unrelated to Django's system check framework
    (``manage.py check``). They are about what a user may do to content, not
    about how a project is configured.


*************
Why one place
*************

The answer to "may this happen?" used to be spread across several places:

* **Forms.** The admin form behind the page tree validated a move. Code that
  moved a page without that form, a management command or an API view, skipped
  the validation and could create two pages with the same URL.
* **Admin views.** Packages that needed to prevent an operation, for example a
  versioning package protecting a published page, overrode the admin view and
  copied its code.
* **Package-specific mechanisms.** ``PlaceholderRelationField.default_checks``
  answers true or false for placeholders. ``djangocms-versioning`` has its own
  ``Conditions`` for versions, which other packages extend by changing class
  attributes at import time.

Each place only covered the callers that happened to go through it, and none of
them could explain *why* an operation was refused before the user tried it.

Operation checks replace this with one registry. Every service runs the checks
registered for its operation, whoever calls it, and the same checks can be run
as a dry run.


**************
How it is used
**************

Operations
==========

Every operation that changes content is declared once, in the **operation
registry** ``cms.operations``. A declaration names:

* an **operationId**, stable and unique, for example ``move_plugin``. The
  constants in ``cms.operations`` (``operations.MOVE_PLUGIN``) are these ids,
  and they are the names the ``pre_*_operation`` and ``post_*_operation``
  signals carry;
* a **summary**, one line: "Move a plugin within or between placeholders";
* a **description**, plain text: what changes, what is required, and what may
  refuse it;
* the **service** performing it.

Checks, signals, log entries and dry runs refer to an operation by its id.
Everything that describes an operation to a person or a program reads the
summary and description from the registry instead of writing its own: the
admin's log entries, a REST API's schema (an OpenAPI ``operationId``,
``summary`` and ``description``), tool definitions for an assistant, and this
documentation. Packages declare their own operations the same way, in their
:doc:`cms_config </how_to/20-cms-config>`.

Summaries and descriptions are declared in the registry, not taken from the
service's docstring, because they serve different readers:

* The **summary** is shown to people: in log entries and in the admin. It is
  translatable, declared with ``gettext_lazy``, and translated when it is shown.
* The **description** is read by programs and developers: API schemas, tool
  definitions for assistants and this documentation. It is plain English and not
  translated, so that its wording stays stable for the programs that rely on
  it. If a declaration has no description, the registry falls back to the
  service's docstring (``inspect.getdoc()``).
* **Docstrings** stay developer documentation, with markup, parameter names and
  the exceptions raised. They are never translated, and are never used for text
  shown to editors.

Docstrings cannot be translated anyway. Wrapping one in ``_()`` turns it into an
ordinary expression and leaves ``__doc__`` empty, ``makemessages`` does not
extract docstrings, and a translation keyed on a whole docstring would be lost
with every edit to it.

Each service states which operation it performs, and runs that operation's
checks before it sends the pre-operation signal:

.. code-block:: python

    from cms.pages import services as page_services
    from cms.shared.operations import OperationContext

    page_services.move_page(
        page, target_page, "first-child",
        context=OperationContext(user=request.user),
    )
    # raises PermissionDenied or ValidationError if a check fails

One frame for every service
===========================

Every service does the same four things in the same order: run the checks,
announce the operation with the pre-operation signal, do the work, and announce
the result with the post-operation signal. ``cms.shared.operations.operation()``
is that frame, so a service only contains its own work:

.. code-block:: python

    from cms.shared.operations import operation
    from cms.signals import PAGE_OPERATION_SIGNALS

    def move_page(page, target_page, position, *, context, permissions=None):
        with operation(
            operations.MOVE_PAGE,
            context,
            checks={"page": page, "target_page": target_page,
                    "position": position, "permissions": permissions},
            signals=PAGE_OPERATION_SIGNALS,
            sender=Page,
            obj=page,
        ):
            page.move_page(target_page, position, user=context.user)
        return page

``checks`` holds the service's arguments, the same ones a dry run passes to
``can()``. A failing check raises before anything is announced, so signal
receivers never hear of an operation that was refused. If the work itself fails,
no post-operation signal is sent. The frame yields the signal kwargs; a service
that wants receivers to see the object as it is after the operation updates them
inside the ``with`` block.

The frame runs in a database transaction, or a savepoint if the caller already
holds one. The checks see the state the work changes, and the operation commits
or rolls back together with whatever signal receivers write about it, such as a
log entry or a version's modified date. A receiver that raises undoes the
operation. Cache invalidation is not rolled back; clearing a cache too often is
harmless.

The checks
==========

A check is a plain function. It receives the
:class:`~cms.shared.operations.OperationContext` (the acting user, the language,
where the operation came from) and the arguments of the service as keywords. It
raises an exception if the operation must not happen, and returns nothing
otherwise.

.. code-block:: python

    from cms.shared.checks import OperationBlocked

    def page_is_unlocked(context, *, page, **kwargs):
        if is_locked(page, context.user):
            raise OperationBlocked(_("This page is locked for editing."))

Checks accept ``**kwargs``, so that a service can pass more arguments in a later
release without breaking them.

Every check has a unique name, such as ``"cms.pages.url_unique"``. The name
identifies the check in a dry run's result and makes it replaceable.

Three kinds of check
====================

Every check has one of three *kinds*. The kind says what the check asks, which
exception it raises, and who it applies to:

.. list-table::
    :header-rows: 1
    :widths: 14 40 22 12

    * - Kind
      - Asks
      - Raises
      - Admin answers
    * - **permission**
      - May *this user* do it? For example ``cms.pages.move_permission``.
      - ``PermissionDenied``
      - 403
    * - **policy**
      - Does the object's state allow it right now, whoever acts? For example:
        published content is read-only, a draft is locked by another user,
        content is under moderation.
      - ``OperationBlocked``
      - 409
    * - **validation**
      - Would the result be valid? For example ``cms.pages.url_unique``: no two
        pages with the same URL.
      - ``ValidationError``
      - 400

``OperationBlocked`` lives in ``cms.shared.checks``. It is a subclass of
``PermissionDenied``, so code that already handles ``PermissionDenied`` keeps
refusing blocked operations; code that wants to tell the two apart catches
``OperationBlocked`` first.

The distinction between permission and policy matters to whoever is refused. A
permission failure means "ask someone with more rights"; a policy failure means
"nobody may do this to the object as it is now: create a draft, wait for the
lock, or finish moderation first". Versioning, locking and moderation packages
register policy checks.

Acting on the system's behalf
=============================

Some code acts on the system's own behalf rather than a user's: management
commands, imports, data migrations. It passes a *system context*:

.. code-block:: python

    context = OperationContext.system("myapp.import_pages", user=author)

``reason`` names the caller; ``user``, if given, is recorded as the author.
A system context

* **skips the permission checks**, because nobody asks whether the system may do
  something;
* **runs the policy checks**: by default, an import writing into published
  content is refused just as an editor's change would be. A caller that has to
  write regardless, such as a data migration, opts out explicitly when it
  creates the context: ``OperationContext.system("myapp.migration",
  policy=False)``. Only a system context can opt out;
* **always runs every validation check**: pages created by an import get unique
  URLs just like pages created in the admin.

The functions of :mod:`cms.api` stay unchecked by default, as in previous
versions, so that fixtures and tests building content keep working. Passing
``context=`` makes them run as their operation: ``create_page`` and
``create_page_content`` as ``ADD_PAGE`` and ``ADD_PAGE_TRANSLATION``,
``add_plugin`` through the ``add_plugin`` service (cleaning the data with the
plugin's form), ``assign_user_to_page`` and ``create_page_user`` through the
grant services:

.. code-block:: python

    from cms.api import add_plugin, create_page

    page = create_page("News", "page.html", "en", parent=home, context=context)
    add_plugin(placeholder, "LinkPlugin", "en", name="django CMS",
               external_link="https://www.django-cms.org", context=context)

Forms never use a system context. A form processes input a user sent, so its
``save()`` passes the acting user's context, and the service checks that user's
permissions, even though the form has already validated its fields.

Order
=====

Checks run by kind: **permission checks first, then policy checks, then
validation checks**. Within a kind, the core checks run first, in the order
django CMS registers them, followed by checks registered by packages, in
``INSTALLED_APPS`` order.

The order matters for what a user learns. A user who may not move a page should
hear "you may not", not "a page with this URL already exists at the target",
which would tell them about pages they may not see. Policy comes before
validation because there is no point in reporting an invalid result for an
object that may not be changed at all.


*********
Dry runs
*********

``cms.shared.checks.can()`` runs the same checks as the service and changes
nothing:

.. code-block:: python

    from cms import operations
    from cms.shared.checks import can

    verdict = can(
        operations.MOVE_PAGE, context,
        page=page, target_page=target_page, position="first-child",
    )
    if not verdict:
        for reason in verdict.reasons:
            print(reason.name, reason.kind, reason.message)

The result, a ``Verdict``, is truthy if the operation may proceed. It lists a
``Reason`` (check name, kind, message) for each failure. A real run stops at the
first failure. A dry run collects all policy and validation failures, so that a
user can see everything that stands in the way at once, and reports them
separately by their kind: "published content is read-only" asks for a different
next step than "a page with this URL already exists". It still stops at the
first permission failure, so a dry run never reveals anything about content the
user may not touch.

This is what the admin UI needs to grey out an action and say why, and what an
API or an assistant needs to answer "can I move this page there?".

Asking before the details are known
===================================

A dry run may leave out arguments. "Can I move this page at all?" has no target
yet. Checks declare the arguments they cannot do without (``requires``); a dry
run that lacks one of them **skips** that check instead of guessing, and lists
it in ``verdict.skipped``. ``verdict.complete`` is ``False`` then: the answer
means "nothing speaks against it so far", not "yes".

A service always passes every argument. A real run with a missing argument is a
programming error and raises ``TypeError``.

A dry run is advice
===================

Content can change between the dry run and the operation. The service always
runs the checks again, so a dry run that said yes can still be followed by a
refused operation.


******************************
Adding and replacing checks
******************************

A package registers checks in its :doc:`cms_config </how_to/20-cms-config>`,
under ``cms_checks``. It maps an operation to a list of ``(name, check)``,
``(name, check, requires)`` or ``(name, check, requires, kind)`` tuples.
``kind`` is ``"validation"`` unless the tuple says ``"permission"`` or
``"policy"``, so a system context runs a package's checks unless the package
marks them as permission checks:

.. code-block:: python

    from cms import operations
    from cms.app_base import CMSAppConfig

    class MyAppConfig(CMSAppConfig):
        cms_checks = {
            operations.MOVE_PAGE: [
                ("myapp.page_unlocked", page_is_unlocked, ["page"], "policy"),
            ],
        }

* **Adding** a check: register it under a new name. It runs after the core
  checks.
* **Replacing** a check: register it under the name of an existing one. It takes
  that check's place in the order. Replace core checks with care: they protect
  the consistency of the page tree and its URLs.

Registering in ``cms_config`` means several packages can contribute checks to
the same operation without knowing about each other, and without changing
attributes of another package's classes at import time.

Permissions
===========

The core permission checks ask the page permission backend
(``cms.pages.permissions``). Its policy can still be changed the way it could
before: for a single call, by passing ``permissions=`` to the service (the admin
does this, so that its overridable ``has_*_permission`` methods keep deciding
admin requests), or for every caller with a ``page_permissions`` contract. A
permission-related check from a package should raise ``PermissionDenied``.

Operations on one translation of a page (changing its template, toggling its
navigation status, copying plugins into it) ask the backend's
``can_change_content(page_content)``. By default it answers the same as
``can_change_page(page)``, but a backend can decide per translation: a
versioning package, for example, only lets drafts be changed. In the admin,
``can_change_content`` asks ``PageContentAdmin.has_change_permission(request,
page_content)``, so a package overriding that method decides for these
operations, too.

Adding a page is the one case where the admin's method cannot decide on its
own. ``PageContentAdmin.has_add_permission(request)`` only knows the parent
named in the query string, while the page is created under the parent the form
posts. So in the admin, adding a page needs both: the admin's
``has_add_permission`` and the backend's ``can_add_page``/``can_add_subpage``
for the parent the page actually gets. An admin subclass can refuse adds this
way, but not allow an add the backend refuses.

The plugin permission backend (``cms.core.permissions``) works the same
way for plugins and placeholders. It asks the object owning the placeholder
(``has_placeholder_change_permission()``) and the placeholder's own
``has_*_plugin_permission()`` methods; the admin adapter routes these through
the placeholder admin's ``has_*_permission`` hooks.


****************************
Who owns which operations
****************************

Each part of django CMS owns the operations on its own content, with its own
services, checks and permission backend, so that each can be replaced on its
own::

    cms.shared  ←  cms.core (placeholders, plugins)  ←  cms.pages, other placeholder owners
                                                     ←  cms.permissions

* **cms.core** owns the placeholder and plugin operations. They work for any
  placeholder owner: a page content, an alias, or any model with a
  ``PlaceholderRelationField``. Core never imports pages. It asks the owning
  object for permission (``has_placeholder_change_permission()``) and for
  policy (``check_source()``, where versioning plugs in).
* **cms.pages** owns adding, changing, moving, copying and deleting pages, the
  home page, the template, copying a language and the navigation status.
  Operations that touch plugins, such as copying a language or a page, call the
  core services for that part.
* **cms.permissions** owns granting and revoking page permissions, global
  permissions, user and group permissions, and page users and groups. These
  change *who may act*, not content.
* **cms.extensions** owns saving and deleting page and translation extensions.

A REST API or an assistant that edits plugins therefore depends on
``cms.core`` only, not on ``cms.pages``.

``cms.api``, management commands, wizards, toolbar endpoints, the admin and
packages such as djangocms-rest are *callers* of these services, not providers.
The admin is an HTTP adapter: it turns a request into an ``OperationContext``,
calls the service, and turns ``PermissionDenied`` into 403, ``OperationBlocked``
into 409 and ``ValidationError`` into 400, each answered with the plain-text
message the frontend editor shows.


******************************
Placeholder and plugin checks
******************************

The plugin services run the same three kinds of check:

* **permission**: the user may add, change, delete, move, clear or copy, and may
  read the placeholder a paste comes from;
* **policy**: the object owning the placeholder is editable (``check_source()``,
  and with it the checks that packages such as djangocms-versioning register on
  ``PlaceholderRelationField``);
* **validation**: the plugin and its children are allowed in the slot, the
  plugin limit is not exceeded, ``parent_classes`` and ``child_classes`` are
  respected, the parent is in the target placeholder and language, a plugin is
  not moved into itself, and the language belongs to the site.

Whether a plugin may go under a parent is decided by the same plugin class
methods the editor asks for what it offers: the parent's
``get_child_classes()``, which includes the children's ``parent_classes`` and the
placeholder configuration, and ``requires_parent_plugin()`` for the top level.
A move is only checked if the plugin gets a new parent or placeholder, so a
tree created before these rules were checked can still be reordered. The
language is checked against the languages of the site the placeholder's page
belongs to, or the current site for other placeholders.

Plugin limits (``CMS_PLACEHOLDER_CONF``) are looked up with the template of
the placeholder's page, for adding, moving and pasting alike.

Editability checks
==================

Some packages decide whether an object's content may be changed right now,
whoever acts: a versioning package only lets drafts be changed, a locking
package only the user holding the lock. Such a rule applies to every operation
that changes the object's content -- adding, moving or deleting plugins in its
placeholders, changing a page translation's template or navigation status,
deleting the translation, copying plugins into it, saving a page content
extension.

Instead of registering a check for each of these operations, a package registers
one **editability check**:

.. code-block:: python

    from cms.shared.checks import OperationBlocked

    def draft_only(context, obj):
        if is_versioned(obj) and not is_draft(obj):
            raise OperationBlocked(_("Only drafts can be changed."))

    class MyAppConfig(CMSAppConfig):
        cms_editability_checks = [("myapp.draft_only", draft_only)]

``obj`` is the object whose content changes: the page content, an alias
content, any object placeholders belong to. The check must accept objects it
does not manage. django CMS registers it as a policy check, under its name, for
every operation that changes content, so a refusal reaches the caller as
``OperationBlocked`` with the check's message, and a dry run reports it by name.
Parts and packages add operations with
:func:`cms.core.checks.register_editable_operation`.

``Placeholder.check_source(user)``, which the frontend editor uses to decide
whether a placeholder is shown as editable, asks the editability checks, too.

The older hook still works: checks added to
``PlaceholderRelationField.default_checks`` or passed to the field as
``checks=`` answer ``True`` or ``False`` for a placeholder and still guard the
plugin operations, through the core policy check ``cms.core.source_editable``.
They give no reason, and they do not guard the page translation operations.

Plugin data
===========

Adding or changing a plugin takes the plugin's data, not a form:

.. code-block:: python

    from cms.core.services import add_plugin, change_plugin

    link = add_plugin(placeholder, "LinkPlugin", "en",
                      {"name": "django CMS", "external_link": "https://www.django-cms.org"},
                      context=context)
    change_plugin(link, {"name": "The django CMS project"}, context=context)

Before saving, the service hands the data to
``CMSPluginBase.clean_plugin_data(obj, data, *, instance=None)``, a classmethod
that cleans it. By default it binds the plugin's ``form``, the plugin's own or
the ``ModelForm`` django CMS generates, with the fields the plugin's admin form
shows, so the form's and the model's validation apply. It needs no request. For a
change, ``data`` only needs the fields that change. The fields that place a
plugin in the tree (placeholder, parent, position, language, plugin type) are
never taken from the data; the operation sets them.

The service calls the hook for every caller, so sanitising, for example the
HTML sanitising a text plugin does in its form field, cannot be skipped by
calling the service directly. A plugin whose form depends on the request
overrides the classmethod. The admin passes the form it has already validated as
``form=``, so that the data is not cleaned twice.

``CMSPluginBase.save_model()`` calls the service as well; it no longer looks up
the placeholder admin to announce the operation.


********************
What checks are not
********************

* **Not a replacement for forms.** Forms still read and clean what a user
  submitted, and attach errors to fields. The page tree's ``MovePageForm`` now
  only turns a drop into a target page and a position; whether the move is
  allowed is left to the checks.
* **Not in the models.** ``Page.move_page()`` and the other model methods keep
  doing the mechanics without checking. Internal code, such as tree repair,
  relies on that. Anything acting on behalf of a user should call the service.


**************
Current status
**************

In django CMS 6.0, the page operations run through operation checks. The
services in ``cms.pages.services`` perform them; the arguments in the second
column are what a check receives and what a dry run passes to ``can()``.

.. list-table::
    :header-rows: 1
    :widths: 30 25 45

    * - Operation and service
      - Arguments
      - Checks, in order
    * - ``MOVE_PAGE``

        ``move_page``
      - ``page``, ``target_page``, ``position``
      - ``cms.pages.move_permission``: the user may move the page.

        ``cms.pages.move_target_permission``: the user may add pages below the
        new parent and move every page of the subtree there.

        ``cms.pages.home_stays_root``: the home page does not end up below
        another page.

        ``cms.pages.slug_unique``: no new sibling has the same slug in any
        language.

        ``cms.pages.url_unique``: none of the page's URLs collides with the URL
        of another page.
    * - ``ADD_PAGE``

        ``add_page``
      - ``site``, ``parent_page``, ``source``, ``allow_view_only_page_type``
      - ``cms.pages.add_permission``: the user may add a page at the root or
        below the parent the page gets (for page types, the page-types root).

        ``cms.pages.add_source_permission``: for a page created from a source,
        the user may copy the source.

        Announced to signal receivers as ``ADD_PAGE_TRANSLATION``.
    * - ``ADD_PAGE_TRANSLATION``

        ``add_translation``
      - ``page``
      - ``cms.pages.add_translation_permission``: the user may change the page.
    * - ``CHANGE_PAGE_TRANSLATION``

        ``change_page_content``
      - ``page_content``
      - ``cms.pages.change_translation_permission``: the user may change this
        translation's content.
    * - ``CHANGE_PAGE_ADVANCED_SETTINGS``

        ``change_advanced_settings``
      - ``page``
      - ``cms.pages.advanced_settings_permission``: the user may change the
        page's advanced settings.
    * - ``CHANGE_PAGE_PERMISSIONS``

        ``save_page_permissions``
      - ``page``, ``save``, ``delete``
      - ``cms.permissions.change_page_permissions``: the user may change the
        page's permissions.

        ``cms.permissions.grants_belong_to_page`` (validation): every grant
        belongs to this page.

        ``cms.permissions.grantable_page_permissions``: the user holds every
        flag set on a saved grant.

        ``cms.permissions.grant_recipients``: editing rights go only to users and
        groups the user manages; view restrictions may name anyone.
    * - ``CHANGE_USER_PERMISSIONS``

        ``set_user_permissions``
      - ``obj``, ``data``
      - ``cms.permissions.manage_user_or_group``: the user manages this user or
        group.

        ``cms.permissions.grantable_user_permissions``: the user holds every
        permission set or cleared.
    * - ``CHANGE_GLOBAL_PAGE_PERMISSION``

        ``save_global_page_permission``
      - ``grant``, ``sites``
      - ``cms.permissions.global_grant_manageable``: the user could have
        granted the stored grant.

        ``cms.permissions.global_grant_grantable``: the user holds every flag
        of the new grant on its sites.
    * - ``DELETE_GLOBAL_PAGE_PERMISSION``

        ``delete_global_page_permission``
      - ``grant``
      - ``cms.permissions.global_grant_deletable``: the user could have granted
        the grant.
    * - ``COPY_PAGE_FROM_SOURCE``

        ``copy_page_from_source``; also called by ``add_page`` when copying
      - ``source``, ``target_site``, ``parent_page``,
        ``allow_view_only_page_type``
      - ``cms.pages.source_copy_permission``: the user may change the source,
        or view a page type from the target site when that exception applies.

        ``cms.pages.source_copy_target_permission``: the user may add a page
        below the target parent or at the root.
    * - ``COPY_PAGE``

        ``copy_page_tree``
      - ``page``, ``target_page``, ``position``, ``target_site``,
        ``copy_permissions``
      - ``cms.pages.copy_permission``: the user may view the page.

        ``cms.pages.copy_target_permission``: the user may add pages below the
        new parent (or at the root) and copy every page of the subtree there.

        ``cms.pages.copy_languages``: the page has a language the target site
        offers.
    * - ``SET_HOME``

        ``set_home``
      - ``page``
      - ``cms.pages.set_home_permission``: the user may change the page and the
        current home page.

        ``cms.pages.home_candidate``: the page is a root page and not the home
        page yet.
    * - ``DELETE_PAGE``

        ``delete_page``
      - ``page``
      - ``cms.pages.delete_permission``: the user may delete the page.
    * - ``DELETE_PAGE_TRANSLATION``

        ``delete_translation``
      - ``page_content``
      - ``cms.pages.delete_translation_permission``: the user may delete the
        translation.

        ``cms.pages.not_last_translation``: the page has another translation.
    * - ``CHANGE_PAGE_TEMPLATE``

        ``change_template``
      - ``page_content``, ``template``
      - ``cms.pages.change_template_permission``: the user may change the page.

        ``cms.pages.template_valid``: the project offers the template.
    * - ``COPY_PAGE_LANGUAGE``

        ``copy_language``
      - ``source_page_content``, ``target_language``
      - ``cms.pages.copy_language_permission``: the user may change the page.

        ``cms.pages.target_language``: the site offers the language and the
        page has content in it.

        ``cms.pages.copy_language_plugin_permission``: the user may add the
        plugins to every target placeholder. Checked before anything is copied.
    * - ``TOGGLE_PAGE_IN_NAVIGATION``

        ``toggle_in_navigation``
      - ``page_content``
      - ``cms.pages.navigation_permission``: the user may change the page.
    * - ``SAVE_EXTENSION``, ``DELETE_EXTENSION``

        ``cms.extensions.services.save_extension``, ``delete_extension``
      - ``extension``
      - ``cms.extensions.change_permission``: the user may change the page, or
        the translation a page content extension belongs to.

        ``cms.extensions.one_per_object`` (validation, saving only): the object
        has no extension of this kind yet.

Every check also receives ``permissions``, the permission backend a caller
passed to the service.

Code that customised move validation by overriding ``MovePageForm.clean()``
should register a check instead, see
:ref:`upgrade-6.0-backward-incompatible`.

The placeholder and plugin operations run through operation checks, too. The
services in ``cms.core.services`` perform them; the arguments are listed in
:ref:`operations_reference`. ``permissions`` is the plugin permission backend,
and ``plugins``, if a service passes it, the plugins it copies.

.. list-table::
    :header-rows: 1
    :widths: 30 70

    * - Operation
      - Checks, in order
    * - ``ADD_PLUGIN``
      - ``cms.core.add_permission``: the user may add this plugin type to the
        placeholder.

        ``cms.core.target_editable`` (policy): the placeholder's content may be
        edited.

        ``cms.core.plugin_type_valid``: the plugin type is registered.

        ``cms.core.allowed_in_slot``: the plugin type is allowed in the slot.

        ``cms.core.parent_valid``: the target (parent or sibling) is in the
        placeholder and language.

        ``cms.core.plugin_limit``: the placeholder has not reached its limit for
        the plugin type, or overall.

        ``cms.core.language_valid``: the site offers the language.

        ``cms.core.parent_allowed``: the plugin type may go under the parent, or
        at the top level.
    * - ``CHANGE_PLUGIN``
      - ``cms.core.change_permission``: the user may change the plugin.

        ``cms.core.source_editable`` (policy): its placeholder's content may be
        edited.

        The data is validated by the plugin's ``clean_plugin_data()`` after the
        checks.
    * - ``MOVE_PLUGIN``
      - ``cms.core.move_permission``: the user may move the plugin out of its
        placeholder and into the target placeholder.

        ``cms.core.source_editable`` (policy): both placeholders' content may be
        edited.

        ``cms.core.parent_valid``: the new parent is in the target placeholder
        and language, and is neither the plugin nor one of its descendants.

        ``cms.core.allowed_in_slot``: the plugin and its descendants are allowed
        in the target slot (not checked within a placeholder or into the
        clipboard).

        ``cms.core.parent_allowed``: the plugin may go under its new parent, or
        at the top level (only checked if the parent or placeholder changes).

        ``cms.core.plugin_limit``: the target placeholder has room for the plugin
        (only checked when it enters another placeholder).
    * - ``CUT_PLUGIN``
      - ``cms.core.cut_permission``: the user may move the plugin.

        ``cms.core.source_editable`` (policy): its placeholder's content may be
        edited.
    * - ``PASTE_PLUGIN``
      - ``cms.core.paste_permission``: the user may read the source placeholder
        and add the plugins to the target.

        ``cms.core.target_editable`` (policy): the target's content may be
        edited.

        ``cms.core.parent_valid``: the parent is in the target placeholder and
        language.

        ``cms.core.allowed_in_slot``: the plugins are allowed in the target slot.

        ``cms.core.language_valid``: the site offers the target language.

        ``cms.core.parent_allowed``: the plugin may go under the parent, or at
        the top level.

        ``cms.core.plugin_limit``: the target placeholder has room for the
        plugin.
    * - ``PASTE_PLACEHOLDER``
      - ``cms.core.paste_permission``, ``cms.core.target_editable``,
        ``cms.core.allowed_in_slot`` for the plugins of the copied placeholder,
        and ``cms.core.language_valid``.
    * - ``COPY_PLUGIN_TO_CLIPBOARD``,

        ``COPY_PLACEHOLDER_TO_CLIPBOARD``
      - ``cms.core.copy_permission``: the user may copy the plugins and read
        their placeholder.

        ``cms.core.target_editable`` (policy): the clipboard may be edited.
    * - ``ADD_PLUGINS_FROM_PLACEHOLDER``
      - ``cms.core.copy_permission``, ``cms.core.target_editable``,
        ``cms.core.allowed_in_slot`` and ``cms.core.language_valid``.
    * - ``DELETE_PLUGIN``
      - ``cms.core.delete_permission`` and ``cms.core.source_editable``.
    * - ``CLEAR_PLACEHOLDER``
      - ``cms.core.clear_permission`` and ``cms.core.source_editable``.

.. TODO: the following is not implemented yet and must be updated as it lands:

   * the page checks above are all permission or validation checks so far;
     those about an object's state become policy checks;

The version conditions of ``djangocms-versioning`` and
``PlaceholderRelationField`` checks become policy checks on the same registry,
so that one mechanism answers "may this happen?" for every operation.

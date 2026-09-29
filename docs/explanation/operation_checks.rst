.. _operation_checks:

################
Operation checks
################

Before django CMS changes content (moving a page, adding a plugin), it asks one
question: *may this operation happen?* This page explains where that question is
answered, how packages add their own answers to it, and how anything, from the
page tree to an API or an assistant, can ask it without changing anything.

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

Operations are named by the constants in ``cms.operations``, the same names the
``pre_obj_operation`` and ``post_obj_operation`` signals carry, for example
``operations.MOVE_PAGE``. Each service states which operation it performs, and
runs that operation's checks before it sends the pre-operation signal:

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

The checks
==========

A check is a plain function. It receives the
:class:`~cms.shared.operations.OperationContext` (the acting user, the language,
where the operation came from) and the arguments of the service as keywords. It
raises Django's own exceptions if the operation must not happen, and returns
nothing otherwise:

* ``PermissionDenied``: the user may not do this. The admin answers with 403.
* ``ValidationError``: nobody may do this right now, because the result would
  be invalid, for example two pages with the same URL. The admin answers with 400.

.. code-block:: python

    from django.core.exceptions import ValidationError

    def page_is_unlocked(context, *, page, **kwargs):
        if is_locked(page, context.user):
            raise ValidationError(_("This page is locked for editing."))

Checks accept ``**kwargs``, so that a service can pass more arguments in a later
release without breaking them.

Every check has a unique name, such as ``"cms.pages.url_unique"``. The name
identifies the check in a dry run's result and makes it replaceable.

Order
=====

The core checks run first, in the order django CMS registers them, **starting
with the permission checks**. Checks registered by packages follow, in
``INSTALLED_APPS`` order.

The order matters for what a user learns. A user who may not move a page should
hear "you may not", not "a page with this URL already exists at the target",
which would tell them about pages they may not see.


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
``Reason`` (check name, ``"permission"`` or ``"validation"``, message) for each
failure. A real run stops at the first failure. A dry run collects all
validation failures, so that a user can see everything that stands in the way at
once, but it still stops at the first permission failure.

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
under ``cms_checks``. It maps an operation to a list of ``(name, check)`` or
``(name, check, requires)`` tuples:

.. code-block:: python

    from cms import operations
    from cms.app_base import CMSAppConfig

    class MyAppConfig(CMSAppConfig):
        cms_checks = {
            operations.MOVE_PAGE: [
                ("myapp.page_unlocked", page_is_unlocked, ["page"]),
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

In django CMS 6.0, moving a page (``operations.MOVE_PAGE``) runs through
operation checks:

.. list-table::
    :header-rows: 1
    :widths: 35 65

    * - Check
      - Refuses the move if
    * - ``cms.pages.move_permission``
      - the user may not move the page.
    * - ``cms.pages.move_target_permission``
      - the user may not add pages at the target, or may not move every page of
        the subtree there.
    * - ``cms.pages.home_stays_root``
      - the home page would end up below another page.
    * - ``cms.pages.slug_unique``
      - a new sibling has the same slug in any language.
    * - ``cms.pages.url_unique``
      - any of the page's URLs would collide with the URL of another page.

Code that customised move validation by overriding ``MovePageForm.clean()``
should register a check instead, see
:ref:`upgrade-6.0-backward-incompatible`.

The other page and plugin operations follow. The plan is to move
``PlaceholderRelationField.default_checks`` and the version conditions of
``djangocms-versioning`` onto the same registry, so that one mechanism answers
"may this happen?" for every operation.

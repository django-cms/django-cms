.. _operations_reference:

##########################
Operations and services
##########################

The functions and objects that change content outside the admin, check whether
a change is allowed, and announce it. See :ref:`operation_checks` for the
concepts and :ref:`service_layer_how_to` for how to use them.

.. versionadded:: 6.0


*****************
Operation context
*****************

.. autoclass:: cms.shared.operations.OperationContext
    :members: from_request, system, is_system

.. autofunction:: cms.shared.operations.operation


**********
Operations
**********

.. py:module:: cms.operations

Operations are declared in the operation registry ``cms.operations``. Each
declaration has an operationId (the constant, for example
``operations.MOVE_PAGE == "move_page"``), a one-line summary, a plain-text
description, the service performing it and the arguments a caller supplies.

``summary``
    Shown to people, in log entries and the admin. Translatable: declare it
    with ``gettext_lazy``.
``description``
    Read by API schemas, tool definitions and the documentation. Plain English,
    not translated. Defaults to the service's docstring
    (``inspect.getdoc()``) if not declared.
``arguments``
    What a caller outside Python -- a REST endpoint, an MCP tool -- supplies,
    as :class:`Argument` declarations. :meth:`Operation.json_schema` turns them
    into the JSON Schema both use for a request body or an ``inputSchema``.
    ``None`` if not declared; adapters leave such operations out.
``returns``
    What the service returns, as a :class:`Result`.
    :meth:`Operation.output_schema` describes it as JSON Schema, for a REST
    response or an MCP ``outputSchema``. A model object is marked with its
    label as ``x-cms-model``: serializing it is the adapter's job.

.. autoclass:: cms.operations.Operation
    :members: id, summary, description, service, arguments, returns, json_schema, output_schema

.. autoclass:: cms.operations.Result
    :members: json_schema, models, is_empty

.. autoclass:: cms.operations.Argument
    :members: json_schema, models

Arguments are checked against the service when the operation is declared:

* every argument is a keyword argument of the service -- adapters call the
  service, and :func:`~cms.shared.checks.can`, with keywords;
* every parameter the service requires is declared, and an argument the
  service requires is not declared optional;
* ``context``, ``permissions`` and ``sender`` are never arguments.

A service parameter with a default that is not declared stays available to
Python callers only (for example the ``form`` the admin passes to
``add_plugin``).

A model argument names a stored object by primary key; the adapter resolves
it, scoped to what the acting user may see, before it calls the service. Its
schema is ``{"type": ["integer", "string"], "x-cms-model": "cms.page"}``. With
``instance=True`` the caller builds the object instead -- a new grant, or a
page with changed advanced settings -- and the schema is an object marked
``"x-cms-instance": true``.

.. autofunction:: cms.operations.register_operation

.. autofunction:: cms.operations.get_operation

.. autofunction:: cms.operations.get_operations

``operation()`` raises ``LookupError`` for an operation that is not declared.

Declaring operations from an app
================================

.. code-block:: python

    from django.utils.translation import gettext_lazy as _

    from cms.app_base import CMSAppConfig
    from cms.operations import Argument, Operation

    class MyAppConfig(CMSAppConfig):
        cms_operations = [
            Operation(
                "myapp.publish_article",
                summary=_("Publish an article"),
                description="Make the article's draft its public version. "
                            "Requires permission to publish articles.",
                service=publish_article,
                arguments=[
                    Argument("article", model="myapp.Article", description="The article to publish."),
                ],
            ),
        ]

``cms_operations`` is a list of :class:`~cms.operations.Operation`; reads go
into ``cms_queries``, a list of :class:`~cms.operations.Query`. Prefix the
ids with the app's label, so that they cannot collide with the ids of django CMS
or other apps; declaring an id twice raises ``ImproperlyConfigured``.

The table lists the service performing each operation and the arguments its
checks receive; every check also receives ``permissions``.

.. list-table::
    :header-rows: 1
    :widths: 32 28 40

    * - Operation
      - Service
      - Check arguments
    * - ``MOVE_PAGE``
      - :func:`cms.pages.services.move_page`
      - ``page``, ``target_page``, ``position``
    * - ``ADD_PAGE``
      - :func:`cms.pages.services.add_page`
      - ``site``, ``parent_page``, ``source``, ``allow_view_only_page_type``
    * - ``ADD_PAGE_TRANSLATION``
      - :func:`cms.pages.services.add_translation`
      - ``page``
    * - ``CHANGE_PAGE_TRANSLATION``
      - :func:`cms.pages.services.change_page_content`
      - ``page_content``
    * - ``CHANGE_PAGE_ADVANCED_SETTINGS``
      - :func:`cms.pages.services.change_advanced_settings`
      - ``page``
    * - ``CHANGE_PAGE_PERMISSIONS``
      - :func:`cms.permissions.services.save_page_permissions`
      - ``page``, ``save``, ``delete``
    * - ``CHANGE_USER_PERMISSIONS``
      - :func:`cms.permissions.services.set_user_permissions`
      - ``obj``, ``data``
    * - ``CHANGE_GLOBAL_PAGE_PERMISSION``
      - :func:`cms.permissions.services.save_global_page_permission`
      - ``grant``, ``sites``
    * - ``DELETE_GLOBAL_PAGE_PERMISSION``
      - :func:`cms.permissions.services.delete_global_page_permission`
      - ``grant``
    * - ``SAVE_EXTENSION``
      - :func:`cms.extensions.services.save_extension`
      - ``extension``
    * - ``DELETE_EXTENSION``
      - :func:`cms.extensions.services.delete_extension`
      - ``extension``
    * - ``COPY_PAGE``
      - :func:`cms.pages.services.copy_page_tree`
      - ``page``, ``target_page``, ``position``, ``target_site``,
        ``copy_permissions``
    * - ``COPY_PAGE_FROM_SOURCE``
      - :func:`cms.pages.services.copy_page_from_source`
      - ``source``, ``target_site``, ``parent_page``,
        ``allow_view_only_page_type``
    * - ``SET_HOME``
      - :func:`cms.pages.services.set_home`
      - ``page``
    * - ``DELETE_PAGE``
      - :func:`cms.pages.services.delete_page`
      - ``page``
    * - ``DELETE_PAGE_TRANSLATION``
      - :func:`cms.pages.services.delete_translation`
      - ``page_content``
    * - ``CHANGE_PAGE_TEMPLATE``
      - :func:`cms.pages.services.change_template`
      - ``page_content``, ``template``
    * - ``COPY_PAGE_LANGUAGE``
      - :func:`cms.pages.services.copy_language`
      - ``source_page_content``, ``target_language``
    * - ``TOGGLE_PAGE_IN_NAVIGATION``
      - :func:`cms.pages.services.toggle_in_navigation`
      - ``page_content``

The placeholder and plugin operations are performed by the services in
``cms.core.services``:

.. list-table::
    :header-rows: 1
    :widths: 32 28 40

    * - Operation
      - Service
      - Arguments
    * - ``ADD_PLUGIN``
      - :func:`cms.core.services.add_plugin`
      - ``placeholder``, ``plugin_type``, ``language``, ``data``,
        ``position``, ``target``
    * - ``CHANGE_PLUGIN``
      - :func:`cms.core.services.change_plugin`
      - ``plugin``, ``data``
    * - ``MOVE_PLUGIN``
      - :func:`cms.core.services.move_plugin`
      - ``plugin``, ``target_position``, ``target_placeholder``,
        ``target_parent``
    * - ``CUT_PLUGIN``
      - :func:`cms.core.services.cut_plugin`
      - ``plugin``, ``target_language``, ``target_placeholder``
    * - ``PASTE_PLUGIN``
      - :func:`cms.core.services.paste_plugin`
      - ``plugin``, ``target_language``, ``target_placeholder``,
        ``target_position``, ``target_parent``
    * - ``PASTE_PLACEHOLDER``
      - :func:`cms.core.services.paste_placeholder`
      - ``plugin``, ``target_language``, ``target_placeholder``,
        ``target_position``
    * - ``COPY_PLUGIN_TO_CLIPBOARD``
      - :func:`cms.core.services.copy_plugin_to_clipboard`
      - ``source_plugin``, ``target_placeholder``, ``target_language``
    * - ``COPY_PLACEHOLDER_TO_CLIPBOARD``
      - :func:`cms.core.services.copy_placeholder_to_clipboard`
      - ``source_placeholder``, ``target_placeholder``, ``source_language``,
        ``target_language``
    * - ``ADD_PLUGINS_FROM_PLACEHOLDER``
      - :func:`cms.core.services.add_plugins_from_placeholder`
      - ``source_placeholder``, ``target_placeholder``, ``source_language``,
        ``target_language``
    * - ``DELETE_PLUGIN``
      - :func:`cms.core.services.delete_plugin`
      - ``plugin``
    * - ``CLEAR_PLACEHOLDER``
      - :func:`cms.core.services.clear_placeholder`
      - ``placeholder``, ``language``

The services run the checks registered for their operation, with the
arguments in the third column, before they announce or change anything.

Adding and changing a plugin also validate ``data`` with the plugin's
:meth:`~cms.core.plugin_base.CMSPluginBase.clean_plugin_data`, after the
checks.


****************
Operation checks
****************

.. py:module:: cms.shared.checks

.. autofunction:: cms.shared.checks.can

.. autofunction:: cms.shared.checks.run_checks

.. autofunction:: cms.shared.checks.register_check

.. autofunction:: cms.shared.checks.get_checks

.. autodata:: cms.shared.checks.PERMISSION

.. autodata:: cms.shared.checks.VALIDATION

.. autodata:: cms.shared.checks.POLICY

.. autoexception:: cms.shared.checks.OperationBlocked

.. autoclass:: cms.shared.checks.Verdict
    :members: complete

.. autoclass:: cms.shared.checks.Reason

Registering checks from an app
==============================

.. code-block:: python

    class MyAppConfig(CMSAppConfig):
        cms_checks = {
            operations.MOVE_PAGE: [
                ("myapp.page_unlocked", page_is_unlocked, ["page"]),
            ],
        }

``cms_checks`` maps an operation name to a list of ``(name, check)``,
``(name, check, requires)`` or ``(name, check, requires, kind)`` tuples.
``kind`` is ``"validation"`` (the default), ``"policy"`` or
``"permission"``; a system context skips permission checks. Checks run
permission first, then policy, then validation. A check is a callable
``check(context, **target)`` raising ``PermissionDenied`` (permission),
``OperationBlocked`` (policy) or ``ValidationError`` (validation). Registering a check under the name of an existing one
replaces it.

``requires`` may only name arguments the operation declares: a dry run with
the declared arguments skips a check that requires any other name, and would
approve what the service refuses. ``manage.py cms check`` reports such checks.

.. autofunction:: cms.shared.checks.argument_problems

Editability checks
==================

.. autofunction:: cms.core.checks.register_editability_check

.. autofunction:: cms.core.checks.register_editable_operation

.. autofunction:: cms.core.checks.is_editable

Apps register editability checks in their ``cms_config`` as
``cms_editability_checks``, a list of ``(name, check)`` tuples.

Core checks
===========

.. py:module:: cms.pages.checks

.. py:module:: cms.permissions.checks

.. py:module:: cms.core.checks

.. py:module:: cms.extensions.checks

The checks django CMS registers for the page operations live in
``cms.pages.checks``, the ones for permission grants in
``cms.permissions.checks``, the ones for extensions in ``cms.extensions.checks``
and the ones for placeholder and plugin operations in ``cms.core.checks``. :ref:`operation_checks` lists them by operation, with
their names.


*************
Page services
*************

.. automodule:: cms.pages.services
    :members: add_page, add_translation, change_page_content,
        change_advanced_settings, move_page, copy_page_tree,
        copy_page_from_source, set_home, delete_page, delete_translation,
        change_template, copy_language, toggle_in_navigation, rebuild_urls

Page lookup uses the normal queryset or admin ``get_object()`` path. A caller
that exposes page data checks the appropriate view permission before returning
it. Each mutating service checks permission for its own operation, even when
the caller has already fetched the page.


*******************
Permission services
*******************

.. automodule:: cms.permissions.services
    :members: set_user_permissions, save_page_permissions,
        save_global_page_permission, delete_global_page_permission,
        delete_global_page_permissions

******************
Extension services
******************

.. automodule:: cms.extensions.services
    :members: save_extension, delete_extension


***************
Plugin services
***************

.. automodule:: cms.core.services
    :members: add_plugin, change_plugin, move_plugin, cut_plugin, paste_plugin, paste_placeholder,
        copy_plugin_to_clipboard, copy_placeholder_to_clipboard,
        add_plugins_from_placeholder, delete_plugin, clear_placeholder


*******************
Permission backends
*******************

.. py:module:: cms.pages.permissions

.. autoclass:: cms.pages.permissions.PagePermissions
    :members:

.. autoclass:: cms.pages.permissions.AdminPagePermissions

.. autoclass:: cms.pages.permissions.AdminPageContentPermissions

.. autofunction:: cms.pages.permissions.get_page_permissions

.. py:module:: cms.core.permissions

.. autoclass:: cms.core.permissions.PluginPermissions
    :members:

.. autoclass:: cms.core.permissions.AdminPluginPermissions

.. autofunction:: cms.core.permissions.get_permissions


*************
Read services
*************

Read services give an adapter -- a REST endpoint, an MCP resource -- the content a
user is about to change, decided by the same rules as the services. They take an
:class:`~cms.shared.operations.OperationContext` and return model objects.

Every read takes an ``admin`` flag:

``admin=False`` (default)
    What the site shows: the source model's ``objects`` manager -- with
    djangocms-versioning, the published version -- for whoever the source's
    ``has_placeholder_view_permission`` lets view it, anonymous visitors
    included. A model without that hook never has its placeholders read this
    way; ``PageContent`` defines it (page view permission and
    ``login_required``).
``admin=True``
    What an editor sees: the ``admin_manager``, drafts included, for active
    staff users who may view the source. Use it to resolve the arguments of a
    write.

Content a user may not read raises its model's ``DoesNotExist``, exactly as
content that does not exist.

.. automodule:: cms.core.queries
    :members: get_source, get_placeholders, get_placeholder, get_plugin, get_plugin_tree, placeholder_token,
        PlaceholderContent

Page reads
==========

.. automodule:: cms.pages.queries
    :members: get_page, get_page_by_path, get_page_content, get_page_contents, get_page_tree, search_pages,
        PageNode

The lists filter view permissions for all pages at once with
:func:`cms.permissions.page_permissions.filter_viewable_page_contents`, the
function the menu uses.

Content tokens
==============

:func:`~cms.core.queries.get_plugin_tree` returns a token for the placeholder's
content in that language. The plugin operations that change a placeholder --
``add_plugin``, ``change_plugin``, ``move_plugin``, ``cut_plugin``,
``delete_plugin``, ``clear_placeholder``, ``paste_plugin``,
``paste_placeholder`` and ``add_plugins_from_placeholder`` -- take it back as
``expected_token``. The policy check ``cms.core.content_unchanged`` refuses the
operation with :class:`~cms.shared.checks.OperationBlocked` if the content has
changed since, and :func:`~cms.shared.checks.can` reports it. Without
``expected_token`` the check does nothing.

The token covers the placeholder the operation changes: the plugin's own
placeholder for ``move_plugin``, not the target.

Declared reads
==============

Reads are declared like operations, as a :class:`~cms.operations.Query`, so
that a REST interface can offer them in its OpenAPI schema and an MCP server as
resource templates. Ids are unique across operations and queries.

.. autoclass:: cms.operations.Query
    :members: id, summary, description, service, arguments, returns, modes, json_schema, output_schema

.. autofunction:: cms.operations.register_query

.. autofunction:: cms.operations.get_query

.. autofunction:: cms.operations.get_queries

``modes`` lists ``"published"``, ``"editing"`` or both. A read offering
``"editing"`` takes ``admin``; the adapter sets it from the mode it reads in,
so ``admin`` -- like ``context`` -- is never a declared argument.

django CMS declares ``get_object_placeholders``, ``get_placeholder``,
``get_plugin``, ``get_plugin_tree``, ``get_page``, ``get_page_by_path``,
``get_page_content``, ``get_page_contents``, ``get_page_tree`` and
``search_pages``.

Scoped lookups
==============

.. automodule:: cms.shared.lookups
    :members: register_lookup, get_lookup, lookup, lookup_many

django CMS registers lookups for ``cms.placeholder``, ``cms.cmsplugin``,
``cms.page``, ``cms.pagecontent`` and ``sites.site``.


*****************
Operation signals
*****************

Every operation is announced by a pair of signals in ``cms.signals``, sent
before and after it. ``cms.signals.PAGE_OPERATION_SIGNALS`` and
``cms.signals.PLACEHOLDER_OPERATION_SIGNALS`` name the pairs.

.. data:: cms.signals.pre_obj_operation
.. data:: cms.signals.post_obj_operation

    Sent for page operations, with the ``Page`` or ``PageContent`` class as
    ``sender``.

.. data:: cms.signals.pre_placeholder_operation
.. data:: cms.signals.post_placeholder_operation

    Sent for plugin and placeholder operations.

All four send these arguments:

``operation``
    The operation name from ``cms.operations``.
``token``
    The same value in the pre and the post signal of one operation, so that a
    receiver can pair them.
``user``
    The acting user.
``request``
    The originating request, or ``None`` if a service was called outside a
    request.
``language``, ``origin``
    From the :class:`~cms.shared.operations.OperationContext`; ``origin`` is the
    path the operation was started from, if any. The page operations the admin
    sends itself (``ADD_PAGE_TRANSLATION``, ``CHANGE_PAGE_TRANSLATION``) send
    ``language`` but no ``origin``.

Page operations also send:

``obj``
    The page. For ``ADD_PAGE_TRANSLATION`` and ``CHANGE_PAGE_TRANSLATION`` it is
    only sent with the post signal.
``translation``
    The ``PageContent`` for operations on one translation
    (``DELETE_PAGE_TRANSLATION``, ``CHANGE_PAGE_TEMPLATE``,
    ``COPY_PAGE_LANGUAGE``, ``TOGGLE_PAGE_IN_NAVIGATION``).
``target_language``
    ``COPY_PAGE_LANGUAGE`` only.
``new_page``
    The copy; post signal of ``COPY_PAGE`` only.

Placeholder operations send, depending on the operation:

.. list-table::
    :header-rows: 1
    :widths: 32 68

    * - Operation
      - Arguments
    * - ``ADD_PLUGIN``
      - ``plugin``, ``placeholder``, ``tree_order``
    * - ``CHANGE_PLUGIN``
      - ``old_plugin``, ``new_plugin``, ``placeholder``
    * - ``MOVE_PLUGIN``
      - ``plugin``, ``source_language``, ``source_placeholder``,
        ``source_parent_id``, ``target_language``, ``target_placeholder``,
        ``target_parent_id``
    * - ``CUT_PLUGIN``
      - ``plugin``, ``clipboard``, ``clipboard_language``, ``source_language``,
        ``source_placeholder``, ``source_parent_id``, ``source_order``
    * - ``PASTE_PLUGIN``
      - ``plugin``, ``target_language``, ``target_placeholder``,
        ``target_parent_id``
    * - ``PASTE_PLACEHOLDER``
      - ``plugins``, ``target_language``, ``target_placeholder``
    * - ``ADD_PLUGINS_FROM_PLACEHOLDER``
      - ``plugins``, ``source_language``, ``source_placeholder``,
        ``target_language``, ``target_placeholder``, ``target_order``
    * - ``DELETE_PLUGIN``
      - ``plugin``, ``placeholder``, ``tree_order``
    * - ``CLEAR_PLACEHOLDER``
      - ``plugins``, ``placeholder``

Receivers must accept ``**kwargs``: new arguments can be added in any release.

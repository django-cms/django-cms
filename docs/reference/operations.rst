.. _operations_reference:

##########################
Operations and services
##########################

The functions and objects that change content outside the admin, check whether
a change is allowed, and announce it. See :ref:`operation_checks` for the
concepts.

.. versionadded:: 6.0


*****************
Operation context
*****************

.. autoclass:: cms.shared.operations.OperationContext
    :members: from_request, from_placeholder_request

.. autofunction:: cms.shared.operations.operation


**********
Operations
**********

Operations are named by the constants in ``cms.operations``. The table lists the
service performing each operation and the arguments its checks receive; every
check also receives ``permissions``.

.. list-table::
    :header-rows: 1
    :widths: 32 28 40

    * - Operation
      - Service
      - Check arguments
    * - ``MOVE_PAGE``
      - :func:`cms.pages.services.move_page`
      - ``page``, ``target_page``, ``position``
    * - ``COPY_PAGE``
      - :func:`cms.pages.services.copy_page_tree`
      - ``page``, ``target_page``, ``position``, ``target_site``,
        ``copy_permissions``
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
      - ``page_content``, ``target_language``
    * - ``TOGGLE_PAGE_IN_NAVIGATION``
      - :func:`cms.pages.services.toggle_in_navigation`
      - ``page_content``

The plugin services in :mod:`cms.core.services` (``MOVE_PLUGIN``,
``CUT_PLUGIN``, ``PASTE_PLUGIN``, ``PASTE_PLACEHOLDER``,
``ADD_PLUGINS_FROM_PLACEHOLDER``, ``DELETE_PLUGIN``, ``CLEAR_PLACEHOLDER``)
check permissions through their backend and do not run operation checks yet.
``ADD_PLUGIN``, ``CHANGE_PLUGIN``, ``ADD_PAGE_TRANSLATION`` and
``CHANGE_PAGE_TRANSLATION`` are performed by the admin only.


****************
Operation checks
****************

.. autofunction:: cms.shared.checks.can

.. autofunction:: cms.shared.checks.run_checks

.. autofunction:: cms.shared.checks.register_check

.. autofunction:: cms.shared.checks.get_checks

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

``cms_checks`` maps an operation name to a list of ``(name, check)`` or
``(name, check, requires)`` tuples. A check is a callable
``check(context, **target)`` raising ``PermissionDenied`` or
``ValidationError``. Registering a check under the name of an existing one
replaces it.


*************
Page services
*************

.. automodule:: cms.pages.services
    :members: move_page, copy_page_tree, set_home, delete_page, delete_translation,
        change_template, copy_language, toggle_in_navigation, rebuild_urls


***************
Plugin services
***************

.. automodule:: cms.core.services.plugins
    :members: move_plugin, cut_plugin, paste_plugin, paste_placeholder,
        copy_plugin_to_clipboard, copy_placeholder_to_clipboard,
        add_plugins_from_placeholder, delete_plugin, clear_placeholder


*******************
Permission backends
*******************

.. autoclass:: cms.pages.permissions.PagePermissions
    :members:

.. autoclass:: cms.pages.permissions.AdminPagePermissions

.. autoclass:: cms.pages.permissions.AdminPageContentPermissions

.. autofunction:: cms.pages.permissions.get_page_permissions

.. autoclass:: cms.core.services.permissions.PluginPermissions
    :members:

.. autoclass:: cms.core.services.permissions.AdminPluginPermissions

.. autofunction:: cms.core.services.permissions.get_permissions


*****************
Operation signals
*****************

Every operation is announced by a pair of signals in :mod:`cms.signals`, sent
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

.. _service_layer_how_to:

##########################################
 How to change content through services
##########################################

.. versionadded:: 6.0

Code outside the admin -- a view, a management command, a REST endpoint, an MCP
tool, a data import -- changes content by calling the same **services** the admin
calls. A service runs the operation's permission, policy and validation checks,
announces the operation to signal receivers (versioning, history, log entries),
invalidates caches, and does all of it in one transaction. Writing to the models
directly skips every one of these steps.

This guide shows how to call the services, handle their refusals, ask before
acting, and discover operations and their arguments programmatically. For the
concepts, see :ref:`operation_checks`; for the full list of operations, see
:ref:`operations_reference`.


****************************
Say who is acting: a context
****************************

Every service takes a keyword-only ``context``, an
:class:`~cms.shared.operations.OperationContext`. It names the acting user, whose
permissions the checks ask about, and the language the operation applies to.

.. code-block:: python

    from cms.shared.operations import OperationContext

    # In a view or an API endpoint: the request's user.
    context = OperationContext.from_request(request, language="en")

    # Anywhere else, for a known user.
    context = OperationContext(user=user, language="en")

``from_request()`` also keeps the request for signal receivers that still read
it. Receivers should prefer the ``user`` the signals carry: a context built
without a request sends ``request=None``.

Code acting on the system's own behalf -- a data import, a management command --
uses a **system context**. It skips the permission checks, but still runs the
policy checks (published content stays protected) and every validation check:

.. code-block:: python

    context = OperationContext.system("myapp.import", user=author)

The reason names your code; ``user``, if given, is recorded as the author.
``OperationContext.system(..., policy=False)`` skips the policy checks as well.
Reserve it for data migrations that must write regardless of the content's
state.

.. warning::

    Never use a system context for actions a user or an assistant asked for.
    Build the context from that user, so that their permissions apply and log
    entries show who did it.


**************
Call a service
**************

The services are plain functions in each part of django CMS:

* ``cms.core.services`` -- placeholders and plugins
* ``cms.pages.services`` -- pages, translations and the page tree
* ``cms.permissions.services`` -- permission grants
* ``cms.extensions.services`` -- page and page content extensions

They take model objects and return model objects:

.. code-block:: python

    from cms.core import services as plugin_services
    from cms.pages import services as page_services

    placeholder = page.get_placeholders("en").get(slot="content")

    # Add a text plugin. The data is validated by the plugin's form, as in the
    # editor; the result is the plugin's own model instance.
    plugin = plugin_services.add_plugin(
        placeholder, "TextPlugin", "en", {"body": "<p>Hello</p>"}, context=context
    )

    # Move it to the top of its placeholder (tree positions start at 1).
    plugin_services.move_plugin(plugin, target_position=1, context=context)

    # Move a page below another one.
    page_services.move_page(page, target_page, "last-child", context=context)

The functions in :mod:`cms.api` keep working as before and do not run checks.
To run one as its operation -- checks, signals, transaction -- pass a context:

.. code-block:: python

    from cms.api import create_page

    page = create_page("About", "page.html", "en", context=context)


****************
Handle a refusal
****************

A service that refuses raises before it changes anything. The exception says
which kind of check refused:

.. list-table::
    :header-rows: 1
    :widths: 30 40 30

    * - Exception
      - Means
      - HTTP status the admin uses
    * - ``PermissionDenied``
      - The acting user may not do this.
      - 403
    * - :class:`~cms.shared.checks.OperationBlocked`
      - The content's state does not allow it right now, whoever acts: a
        published version, a lock, a moderation step.
      - 409
    * - ``ValidationError``
      - The result would not be valid: an unknown plugin type, a plugin not
        allowed in the slot, a slug that is taken.
      - 400

``OperationBlocked`` is a subclass of ``PermissionDenied``, so catch it first:

.. code-block:: python

    from django.core.exceptions import PermissionDenied, ValidationError
    from django.http import HttpResponse

    from cms.shared.checks import OperationBlocked

    try:
        plugin_services.move_plugin(plugin, target_position=1, context=context)
    except OperationBlocked as error:
        return HttpResponse(str(error), status=409)
    except PermissionDenied as error:
        return HttpResponse(str(error), status=403)
    except ValidationError as error:
        return HttpResponse(" ".join(error.messages), status=400)

The messages are translated and meant for people.


*****************
Ask before acting
*****************

:func:`~cms.shared.checks.can` runs an operation's checks without changing
anything. Use it to disable a button, to explain to a user why something is
not possible, or to let an assistant check a plan before it acts:

.. code-block:: python

    from cms import operations
    from cms.shared.checks import can

    verdict = can(operations.MOVE_PLUGIN, context, plugin=plugin, target_position=1)
    if not verdict:
        for reason in verdict.reasons:
            print(reason.name, reason.kind, reason.message)
            # cms.core.move_permission permission You have no permission to move this plugin

Pass the same keyword arguments the service takes. The
:class:`~cms.shared.checks.Verdict` is truthy if the operation may proceed, and
lists a :class:`~cms.shared.checks.Reason` for each failed check: its ``name``,
a stable identifier you can match on, its ``kind`` (``"permission"``,
``"policy"`` or ``"validation"``) and its ``message``.

A dry run stops at the first permission failure, so that it never tells a
user more about content they may not touch. It collects every policy and
validation failure otherwise.

A check that needs an argument you did not pass is skipped and listed in
``verdict.skipped``. A verdict with skipped checks is not a promise: check
``verdict.complete`` before you rely on it.


*********************
Read before you write
*********************

An adapter receives primary keys and shows users content before they change it.
Read both through the read services, which apply the same rules as the
services -- not through the models:

.. code-block:: python

    from cms.core import queries
    from cms.shared.lookups import lookup

    # Objects by primary key, only if the acting user may see them. The label is
    # the one an operation's arguments declare (``argument.models``).
    content = lookup("cms.pagecontent", content_id, context, admin=True)
    placeholder = queries.get_placeholders(content, context, admin=True).get(slot="content")

    # The plugins in tree order, and a token for what was read.
    tree = queries.get_plugin_tree(placeholder, "en", context, admin=True)
    for plugin in tree.plugins:
        print(plugin.pk, plugin.plugin_type, plugin.parent_id, plugin.position)

``admin=True`` reads as an editor: drafts included (the model's
``admin_manager``), for active staff users. Writes act on that content, so
resolve their arguments this way. Without it, the reads return what the site
shows (``objects``; with djangocms-versioning, the published version) to whoever
may view it, anonymous visitors included -- what a public API serves.

Content that does not exist and content the user may not see both raise
``DoesNotExist``, so that a lookup never confirms that hidden content exists.

Pass the token back when you write. If someone changed the placeholder in the
meantime, the write is refused with ``OperationBlocked``; read again and decide
again:

.. code-block:: python

    plugin_services.move_plugin(
        lookup("cms.cmsplugin", plugin_id, context, admin=True),
        target_position=1,
        expected_token=tree.token,
        context=context,
    )


************************
Group several operations
************************

Each service runs in its own transaction; a signal receiver that raises rolls
the operation back. To make several operations succeed or fail together, wrap
them in your own transaction:

.. code-block:: python

    from django.db import transaction

    with transaction.atomic():
        page_services.move_page(page, target_page, "first-child", context=context)
        plugin_services.clear_placeholder(placeholder, "en", context=context)

If the second call raises, the page move is rolled back too. Cache invalidation
is not rolled back; it only causes the next request to rebuild the cache.


***************************************
Discover operations and their arguments
***************************************

Adapters that expose operations to other programs -- a REST API, an MCP server
-- do not need code per operation. The operation registry describes every
operation, including those that installed apps declare:

.. code-block:: python

    from cms import operations
    from cms.operations import get_operation, get_operations

    for op in get_operations():
        if op.service is None or op.arguments is None:
            continue  # not callable with declared arguments
        print(op.id, op.summary, op.description)
        for argument in op.arguments:
            print("   ", argument.name, argument.models or argument.type, argument.required)

    move = get_operation(operations.MOVE_PLUGIN)
    move.json_schema()
    # {"type": "object",
    #  "properties": {
    #      "plugin": {"type": ["integer", "string"], "x-cms-model": "cms.cmsplugin",
    #                 "description": "The plugin."},
    #      "target_position": {"type": "integer", ...},
    #      ...},
    #  "required": ["plugin", "target_position"],
    #  "additionalProperties": false}

* ``id`` is stable: use it as the OpenAPI ``operationId`` or the tool name.
* ``summary`` is translatable and meant for people. ``description`` is plain
  English, not translated, and meant for programs, for example an assistant
  reading a tool definition.
* ``json_schema()`` describes the arguments as JSON Schema, ready for a request
  body or an MCP ``inputSchema``. A model argument is the object's primary key,
  marked with its model's label as ``x-cms-model``.
* ``output_schema()`` describes the result, from ``op.returns``. A model object
  in it is marked ``x-cms-model``; your serializer for that model fills in its
  fields.

Reads are declared the same way, as queries: ``get_queries()`` and
``get_query()`` return them with ``arguments``, ``returns`` and the ``modes``
they support -- ``"published"`` and ``"editing"``. Call a query's service with
``admin=True`` for the editing mode; ``admin`` is never one of the declared
arguments.

To call an operation with decoded JSON, turn primary keys into objects -- only
objects the acting user may see -- and call the service with keywords:

.. code-block:: python

    def call(op, payload, context):
        kwargs = {}
        for argument in op.arguments:
            if argument.name not in payload:
                continue
            value = payload[argument.name]
            if argument.models and not argument.instance and value is not None:
                value = lookup(argument.models[0], value, context, admin=True)  # cms.shared.lookups
            kwargs[argument.name] = value
        return op.service(**kwargs, context=context)

The declared arguments are exactly what :func:`~cms.shared.checks.can` needs:
every check requires only declared arguments (``manage.py cms check`` reports
any that do not), so a dry run with the same ``kwargs`` skips no check.

The ``context``, ``permissions`` and ``sender`` parameters are never arguments.
Service parameters that are not declared, such as the ``form`` the admin passes
to ``add_plugin``, are meant for Python callers only.


************************
Make your own operations
************************

Your app's own content operations can work the same way: declare them in your
``cms_config`` with ``cms_operations``, including their ``arguments``, and
register their checks with ``cms_checks``. See :ref:`operations_reference`.

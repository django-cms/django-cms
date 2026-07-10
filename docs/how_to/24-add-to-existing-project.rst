.. _add_to_existing_project:

Add django CMS to an existing project
=====================================

You can add django CMS to an existing Django project with a single command::

    pip install django-cms
    djangocms .

Run it from the project root (the directory containing ``manage.py``), with
your project's virtual environment activated.

.. warning::

    The command makes automated, best-effort edits to your settings and urls
    files. Make sure your project is under version control (or backed up) so
    you can review every change afterwards. The command asks for confirmation
    before changing anything.

.. tip::

    Run it with ``--dry-run`` first to preview every change as a unified diff,
    without writing any files or installing packages::

        djangocms . --dry-run

What the command does
---------------------

The command reads the settings module from ``manage.py`` and updates your
project files:

* adds the django CMS apps (and those of the selected add-ons) to
  ``INSTALLED_APPS``,
* adds the django CMS middleware and template context processors,
* appends required settings such as ``SITE_ID``, ``LANGUAGES`` (derived from
  your ``LANGUAGE_CODE``) and ``CMS_TEMPLATES`` if they are missing,
* adds the django CMS url patterns to your ``ROOT_URLCONF``,
* creates a ``templates`` directory with a minimal base template if your
  project has none yet.

Existing entries are never duplicated, so the command is safe to run again.

It then lists the required packages and asks whether to install them. If you
agree, it installs them, runs the database migrations and validates the
installation with ``cms check``.

Choosing options
----------------

The same options as for creating a new project are available, for example::

    djangocms . --mode headless --no-versioning

selects the headless mode (content is served through a REST API instead of
HTML pages) and skips content versioning. See the
:ref:`djangocms command reference <djangocms-command>` for all options and
their defaults.

Using custom project rules
--------------------------

The ``--template`` option can point to a local template directory, a local ZIP
or tar archive, or a remote template archive. If that template contains
``djangocms_install_rules.json``, the command uses its options, packages, and
project-editing rules instead of those from the official ``cms-template``::

    djangocms . --template https://example.com/agency-template.tar.gz --dry-run

Place the rules file at the template root. A single enclosing archive directory
is also supported. This lets an organization keep project generation and
existing-project integration in the same versioned template.

If the custom template does not contain a rules file, the command reports that
fact and falls back to the official rules. Use
``--use-bundled-install-rules`` to explicitly ignore template and remote rules
and use the rules bundled with django CMS.

Review the changes
------------------

The edits are best-effort: projects with heavily customized settings (for
example, split settings modules or settings computed at runtime) may need
manual adjustments. After running the command:

* review the diff of your settings and urls files,
* start the development server with ``python -m manage runserver``,
* log in with an existing superuser account and check that the toolbar
  appears.

No superuser is created when installing into an existing project; create one
with ``python -m manage createsuperuser`` if needed.

Prefer full control?
--------------------

If you would rather apply every change yourself, follow
:ref:`the manual configuration steps <minimal-required-configuration>`, which
walk through each setting the command writes for you.

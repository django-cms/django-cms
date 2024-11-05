.. _management_commands:

######################
Command Line Interface
######################

..  module:: cms.management

.. highlight:: bash

You can invoke the django CMS command line interface using the ``cms`` Django
command::

    python manage.py cms


**********************
Informational commands
**********************

.. _cms-list-command:

``cms list``
============

The ``list`` command is used to display information about your installation.

It has two sub-commands:

* ``cms list plugins`` lists all plugins that are used in your project.
* ``cms list apphooks`` lists all apphooks that are used in your project.

``cms list plugins`` will issue warnings when it finds orphaned plugins (see
``cms delete-orphaned-plugins`` below).


.. _cms-check-command:

``cms check``
=============

Checks your configuration and environment.


**************************************
Plugin and apphook management commands
**************************************

.. _cms-delete-orphaned-plugins-command:

``cms delete-orphaned-plugins``
===============================

.. warning::

    The ``delete-orphaned-plugins`` command **permanently deletes** data from
    your database. You should make a backup of your database before using it!

Identifies and deletes orphaned plugins.

Orphaned plugins are ones that exist in the CMSPlugins table, but:

* have a ``plugin_type`` that is no longer even installed
* have no corresponding saved instance in that particular plugin type's table

Such plugins will cause problems when trying to use operations that need to copy
pages (and therefore plugins), which includes ``cms moderator on`` as well as page
copy operations in the admin.

It is recommended to run ``cms list plugins`` periodically, and ``cms
delete-orphaned-plugins`` when required.


``cms uninstall``
=================

The ``uninstall`` subcommand can be used to make uninstalling a CMS
plugin or an apphook easier.

It has two sub-commands:

* ``cms uninstall plugins <plugin name> [<plugin name 2> [...]]`` uninstalls
  one or several plugins by **removing** them from all pages where they are
  used. Note that the plugin name should be the name of the class that is
  registered in the django CMS. If you are unsure about the plugin name, use
  the :ref:`cms-list-command` to see a list of installed plugins.
* ``cms uninstall apphooks <apphook name> [<apphook name 2> [...]]`` uninstalls
  one or several apphooks by **removing** them from all pages where they are
  used. Note that the apphook name should be the name of the class that is
  registered in the django CMS. If you are unsure about the apphook name, use
  the :ref:`cms-list-command` to see a list of installed apphooks.

.. warning::

    The uninstall commands **permanently delete** data from your database.
    You should make a backup of your database before using them!


.. _cms-copy-command:

``cms copy``
============

The ``copy`` command is used to copy content from one language or site to another.

It has two sub-commands:

* ``cms copy lang`` copy content to a given language.
* ``cms copy site`` copy pages and content to a given site.

.. _cms-copy-lang-command:

``cms copy lang``
=================

The ``copy lang`` subcommand can be used to copy content (titles and plugins)
from one language to another.
By default the subcommand copy content from the current site
(e.g. the value of ``SITE_ID``) and only if the target
placeholder has no content for the specified language; using the defined
options you can change this.

You must provide two arguments:

* ``--from-lang``: the language to copy the content from;
* ``--to-lang``: the language to copy the content to.

It accepts the following options

* ``--force``: set to copy content even if a placeholder already has content;
  if set, copied content will be appended to the original one;
* ``--site``: specify a SITE_ID to operate on sites different from the current one;
* ``--verbosity``: set for more verbose output.
* ``--skip-content``: if set, content is not copied, and the command will only
  create titles in the given language.

Example::

    cms copy lang --from-lang=en --to-lang=de --force --site=2 --verbosity=2

.. _cms-copy-site-command:

``cms copy site``
=================

The ``copy site`` subcommand can be used to copy content (pages and plugins)
from one site to another.
The subcommand copy content from the ``from-site`` to ``to-site``; please note
that static placeholders are copied as they are shared across sites.
The whole source tree is copied, in the root of the target website.
Existing pages on the target website are not modified.

You must provide two arguments:

* ``--from-site``: the site to copy the content from;
* ``--to-site``: the site to copy the content to.

Example::

    cms copy site --from-site=1 --to-site=2


**********************
Maintenance and repair
**********************

.. _fix-tree:

``fix-tree``
============

Occasionally, the page tree can become corrupted. Typical symptoms include problems 
when trying to copy or delete pages.

This command will fix small corruptions by rebuilding the tree.

.. versionadded:: 4.0

    Since django CMS Version 4 this command does not affect the plugin tree.
    
######################
Command Line Interface
######################

.. highlight:: bash

You can invoke the django CMS command line interface using the ``cms`` Django
command::

    python manage.py cms

**********************
Informational commands
**********************

``cms list``
============

The ``list`` command is used to display information about your installation.

It has two subcommands:

* ``cms list plugins`` lists all plugins that are used in your project.
* ``cms list apphooks`` lists all apphooks that are used in your project.


**************************************
Plugin and apphook management commands
**************************************

The ``uninstall`` subcommand can be used to make an uninstallation of a CMS
Plugin or an apphook easier.

It has two subcommands:

* ``cms uninstall plugins <plugin name> [<plugin name 2> [...]]`` uninstalls
  one or several plugins by **removing** them from all pages where they are
  used.
* ``cms uninstall apphooks <apphook name> [<apphook name 2> [...]]`` uninstalls
  one or several apphooks by **removing** them from all pages where they are
  used.

.. warning::

    The uninstall command **permanently deletes** data from your database.
    You should make a backup of your database before using them!


******************
Moderator commands
******************

If you turn :setting:`CMS_MODERATOR` to ``True`` on an existing project, you
should use the ``cms moderator on`` command to make the required changes in the
database, otherwise you will have problems with invisible pages.

.. warning::

    This command **alters data** in your database. You should make a backup of
    your database before using it!
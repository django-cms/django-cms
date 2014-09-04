###########################
Using South with django CMS
###########################

South is an incredible piece of software that lets you handle database
migrations. This document is by no means meant to replace the
excellent `documentation`_ available online, but rather to give a quick primer
on why you should use South and how to get started quickly.


************
Installation
************

As always using Django and Python is a joy. Installing South is
as simple as typing::

    pip install South

Then, simply add ``south`` to the list of :setting:`django:INSTALLED_APPS` in your
``settings.py`` file.


***********
Basic usage
***********

For a very short crash course:

#. Instead of the initial ``manage.py syncdb`` command, simply run
   ``manage.py schemamigration --initial <app name>``. This will create a new
   migrations package, along with a new migration file (in the form of a python
   script).
#. Run the migration using ``manage.py migrate``. Your tables will be created
   in the database and Django will work as usual.
#. Whenever you make changes to your models.py file, run
   ``manage.py schemamigration --auto <app name>`` to create a new migration
   file. Next run ``manage.py migrate`` to apply the newly created migration.


****************************
More information about South
****************************

Obviously, South is a very powerful tool and this simple crash course is only
the very tip of the iceberg. Readers are highly encouraged to have a quick
glance at the excellent official South `documentation`_.

.. _documentation: http://south.aeracode.org/docs/index.html

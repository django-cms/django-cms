Contribution Guide
==================

Being an open source project we very much appreciate contributions from the
community. You don't have to know how to code to be able to contribute,
translations and documentation improvements are at least as welcome as code.

Community
---------

People interested in developing for the django-cms should join the
`django-cms-developers`_ mailing list as well as heading over to #django-cms on
freenode　for help and to discuss the development.

You may also be interested in following @djangocmsstatus on twitter to get the
github commits as well as the hudson build reports.


Translate the CMS
-----------------

For translators we have a `transifex account
<http://www.transifex.net/projects/p/django-cms/>`_ where you can translate
the .po files and don't need to install git or mercurial to be able to
contribute. All changes there will be automatically sent to the project.


Review or write documentation
-----------------------------

People interested in writing documentation and/or reviewing the documentation
already existing are more than welcome to do so. The best way to do so is to
`fork`_ the cms on github, change the relevant files and send us a pull request.

If you think you're not familiar enough with the project to write documentation
you can still read over the existing one and suggest on how to improve it or
point out mistakes in it.

For our documentation we use `sphinx`_, which is based off Restructured Text.


Contributing code
-----------------

To contribute code you should be familiar with git and have an account on
github.com (although we'd also accept plain old patches of course).

The usual process to contribute code is:

- `fork`_ the cms on github.
- Make your changes.
- Send us a pull request.

Please note that each pull request should fix exactly one issue or add exactly
one new feature, don't send pull requests which have several things mixed in,
since that lowers their chances of getting pulled in.

New Features
~~~~~~~~~~~~

If you're interested in developing a new feature for the cms, it is recommended
that you first discuss it on the `django-cms-developers`_  mailing list so as
not to do any work that will not get merged in anyway.

Coding Guidelines
~~~~~~~~~~~~~~~~~

* Follow the `PEP8`_ coding style guidelines whenever possible.
* All code **must** be unittest covered. Tests are not optional!
* If you change a public API you must also change their documentation.
3 Please comment your code. 


.. _fork: http://github.com/divio/django-cms
.. _sphinx: http://sphinx.pocoo.org/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _django-cms-developers: http://groups.google.com/group/django-cms-developers
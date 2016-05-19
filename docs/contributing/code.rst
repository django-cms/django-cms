..  _contributing-code:

#################
Contributing code
#################

Like every open-source project, django CMS is always looking for motivated
individuals to contribute to its source code.


*************
In a nutshell
*************

Here's what the contribution process looks like in brief:

#. django CMS is hosted on `GitHub`_, at https://github.com/divio/django-cms
#. The best method to contribute back is to create an account there, then fork
   the project. You can use this fork as if it was your own project, and should
   push your changes to it.
#. When you feel your code is good enough for inclusion, "send us a `pull
   request`_", by using the nice GitHub web interface.

See the :ref:`contributing_patch` how-to document for a walk-through of this process.


********************************
Basic requirements and standards
********************************

If you're interested in developing a new feature for the CMS, it is recommended
that you first discuss it on the `django-cms-developers`_  mailing list so as
not to do any work that will not get merged in anyway.

- Code will be reviewed and tested by at least one core developer, preferably
  by several. Other community members are welcome to give feedback.
- Code *must* be tested. Your pull request should include unit-tests (that cover
  the piece of code you're submitting, obviously)
- Documentation should reflect your changes if relevant. There is nothing worse
  than invalid documentation.
- Usually, if unit tests are written, pass, and your change is relevant, then
  it'll be merged.

Since we're hosted on GitHub, django CMS uses `git`_ as a version control system.

The `GitHub help`_ is very well written and will get you started on using git
and GitHub in a jiffy. It is an invaluable resource for newbies and old timers
alike.


Syntax and conventions
======================

Python
------

We try to conform to `PEP8`_ as much as possible. A few highlights:

- Indentation should be exactly 4 spaces. Not 2, not 6, not 8. **4**. Also, tabs
  are evil.
- We try (loosely) to keep the line length at 79 characters. Generally the rule
  is "it should look good in a terminal-base editor" (eg vim), but we try not be
  too inflexible about it.


HTML, CSS and JavaScript
------------------------

As of django CMS 3.2, we are using the same guidelines as described in `Aldryn
Boilerplate`_

Frontend code should be formatted for readability. If in doubt, follow existing
examples, or ask.


.. _js_linting:

JS Linting
----------

JavaScript is linted using `ESLint <http://eslint.org>`_. In order to run the
linter you need to do this:

.. code-block:: sh

    gulp lint

Or you can also run the watcher by just running ``gulp``.


Process
=======

This is how you fix a bug or add a feature:

#. `fork`_ us on GitHub.
#. Checkout your fork.
#. *Hack hack hack*, *test test test*, *commit commit commit*, test again.
#. Push to your fork.
#. Open a pull request.

And at any point in that process, you can add: *discuss discuss discuss*,
because it's always useful for everyone to pass ideas around and look at things
together.

:ref:`testing` is really important: a pull request that lowers our testing
coverage will only be accepted with a very good reason; bug-fixing patches
**must** demonstrate the bug with a test to avoid regressions and to check
that the fix works.

We have an IRC channel, our `django-cms-developers`_ email list,
and of course the code reviews mechanism on GitHub - do use them.

If you don't have an IRC client, you can `join our IRC channel using the KiwiIRC web client
<https://kiwiirc.com/client/irc.freenode.net/django-cms>`_, which works pretty well.

.. _contributing_frontend:

********
Frontend
********

In order to be able to work with the frontend tooling contributing to the
django CMS you need to have the following dependencies installed:

    1. `Node <https://nodejs.org/>`_ version 0.12.7 (will install npm as well).
       We recommend using `NVM <https://github.com/creationix/nvm>`_ to get
       the correct version of Node.
    2. `Globally installed gulp <https://github.com/gulpjs/gulp/blob/master/docs/getting-started.md#1-install-gulp-globally>`_
    3. Local dependencies ``npm install``

Styles
======

We are using `Sass <http://sass-lang.com/>`_ for our styles. The files
are located within ``cms/static/cms/sass`` and can be compiled using the
`libsass <http://libsass.org/>`_ implementation of Sass compiler through
`Gulp <http://gulpjs.com/>`_.

In order to compile the stylesheets you need to run this command from the repo
root::

    gulp sass

While developing it is also possible to run a watcher that compiles Sass files
on change::

    gulp

By default, source maps are not included in the compiled files. In order to turn
them on while developing just add the ``--debug`` option::

    gulp --debug

Icons
=====

We are using `gulp-iconfont <https://github.com/backflip/gulp-iconfont>`_ to
generate icon web fonts into ``cms/static/cms/fonts/``. This also creates
``_iconography.scss`` within ``cms/static/cms/sass/components`` which adds all
the icon classes and ultimately compiles to CSS.

In order to compile the web font you need to run::

    gulp icons

This simply takes all SVGs within ``cms/static/cms/fonts/src`` and embeds them
into the web font. All classes will be automatically added to
``_iconography.scss`` as previously mentioned.

Additionally we created an SVG template within
``cms/static/cms/font/src/_template.svgz`` that you should use when converting
or creating additional icons. It is named *svgz* so it doesn't get compiled
into the font. When using *Adobe Illustrator* please mind the
`following settings <images/svg_settings.png>`_.


JS Bundling
===========

JavaScript files are split up for easier development, but in the end they are
bundled together and minified to decrease amount of requests made and improve
performance. In order to do that we use ``gulp`` task runner, where ``bundle``
command is available. Configuration and list of dependencies for each bundle are
stored inside the ``gulpfile.js``.


.. _fork: http://github.com/divio/django-cms
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _Aldryn Boilerplate: http://aldryn-boilerplate-bootstrap3.readthedocs.org/en/latest/guidelines/index.html
.. _django-cms-developers: http://groups.google.com/group/django-cms-developers
.. _GitHub: http://www.github.com
.. _GitHub help: http://help.github.com
.. _freenode: http://freenode.net/
.. _pull request: http://help.github.com/send-pull-requests/
.. _git: http://git-scm.com/

..  _contributing:

##########################
Contributing to django CMS
##########################

Like every open-source project, django CMS is always looking for motivated
individuals to contribute to its source code.


Key points:

.. ATTENTION::

    If you think you have discovered a security issue in our code, please report
    it **privately**, by emailing us at `security@django-cms.org`_.

        Please **do not** raise it on:

        * IRC
        * GitHub
        * either of our email lists

        or in any other public forum until we have had a chance to deal with it.

..  _community-resources:

*********
Community
*********

People interested in developing for the django CMS should join the
`django-cms-developers`_ mailing list as well as heading over to #django-cms on
the `freenode`_ IRC network for help and to discuss the development.

You may also be interested in following `@djangocmsstatus`_ on twitter to get
the GitHub commits as well as the hudson build reports. There is also a
`@djangocms`_ account for less technical announcements.


*************
In a nutshell
*************

Here's what the contribution process looks like, in a bullet-points fashion, and
only for the stuff we host on GitHub:

#. django CMS is hosted on `GitHub`_, at https://github.com/divio/django-cms
#. The best method to contribute back is to create an account there, then fork
   the project. You can use this fork as if it was your own project, and should
   push your changes to it.
#. When you feel your code is good enough for inclusion, "send us a `pull
   request`_", by using the nice GitHub web interface.

.. _contributing-code:

*****************
Contributing Code
*****************

Getting the source code
=======================

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
  [Godwin's law] about it.

HTML, CSS and JavaScript
------------------------

As of django CMS 3.2, we are using the same guidelines as described in `Aldryn
Boilerplate`_

Frontend code should be formatted for readability. If in doubt, follow existing
examples, or ask.

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

.. _contributing-documentation:

**************************
Contributing Documentation
**************************

Perhaps considered "boring" by hard-core coders, documentation is sometimes even
more important than code! This is what brings fresh blood to a project, and
serves as a reference for old timers. On top of this, documentation is the one
area where less technical people can help most - you just need to write
simple, unfussy English. Elegance of style is a secondary consideration, and
your prose can be improved later if necessary.

Documentation should be:

- written using valid `Sphinx`_/`restructuredText`_ syntax (see below for
  specifics) and the file extension should be ``.rst``
- written in English (we have standardised on British spellings)
- accessible - you should assume the reader to be moderately familiar with
  Python and Django, but not anything else. Link to documentation of libraries
  you use, for example, even if they are "obvious" to you
- wrapped at 100 characters per line

Merging documentation is pretty fast and painless.

Also, contributing to the documentation will earn you great respect from the
core developers. You get good karma just like a test contributor, but you get
double cookie points. Seriously. You rock.

Except for the tiniest of change, we recommend that you test them before
submitting. Follow the same steps above to fork and clone the project locally.
Next, create a virtualenv so you can install the documentation tools::

    virtualenv djcms-docs-env
    source djcms-docs-env/bin/activate
    pip install sphinx sphinx_rtd_theme

Now you can ``cd`` into the ``django-cms/docs`` directory and build the documentation::

    make html
    open build/html/index.html

This allows you to review your changes in your local browser. After each
change, be sure to rebuild the docs using ``make html``. If everything looks
good, then it's time to push your changes to Github and open a pull request.

Documentation structure
=======================

Our documentation is divided into the following main sections:

* :doc:`/introduction/index` (``introduction``): step-by-step tutorials to get
  you up and running
* :doc:`/how_to/index` (``how_to``): guides covering more advanced development
* :doc:`/topics/index` (``topics``): explanations of key parts of the system
* :doc:`/reference/index` (``reference``): technical reference for APIs, key
  models
  and so on
* :doc:`/contributing/index` (``contributing``)
* :doc:`/upgrade/index` (``upgrade``)
* (in progress Using django CMS (``user``): guides for *using* rather than
  setting up or developing for the CMS


Documentation markup
====================

Sections
--------

We use Python documentation conventions for section marking:

* ``#`` with overline, for parts
* ``*`` with overline, for chapters
* ``=`` for sections
* ``-`` for subsections
* ``^`` for subsubsections
* ``"`` for paragraphs

Inline markup
-------------

* use backticks - `````` - for:
    * literals - ````cms.models.pagemodel````
    * filenames - ``edit ``settings.py````
    * names of fields and other specific items in the Admin interface - ``edit ``Redirect````
* use emphasis - ``*Home*`` - around:
    * the names of available options in or parts of the Admin - ``the *Toolbar*``
    * the names of important modes or states - ``switch to *Edit mode*``
    * values in or of fields - ``enter *Home*``
* use strong emphasis - ``**`` - around:
    * buttons that perform an action - ``hit **Save as draft**``

Rules for using technical words
-------------------------------

There should be one consistent way of rendering any technical word, depending on its context.
Please follow these rules:

* in general use, simply use the word as if it were any ordinary word, with no capitalisation or
  highlighting: "Your placeholder can now be used."
* at the start of sentences or titles, capitalise in the usual way: "Placeholder management guide"
* when introducing the term for the the first time, or for the first time in a document, you may
  highlight it to draw attention to it: "**Placeholders** are special model fields".
* when the word refers specifically to an object in the code, highlight it as a literal:
  "``Placeholder`` methods can be overwritten as required" - when appropriate, link the term to
  further reference documentation as well as simply highlighting it.

References
----------

Use absolute links to other documentation pages - ``:doc:`/how_to/toolbar``` -
rather than relative links - ``:doc:`/../toolbar```. This makes it easier to
run search-and-replaces when items are moved in the structure.

.. _contributing-translations:

************
Translations
************

For translators we have a `Transifex account
<https://www.transifex.com/projects/p/django-cms/>`_ where you can translate
the .po files and don't need to install git or mercurial to be able to
contribute. All changes there will be automatically sent to the project.

    .. raw:: html

        Top translations django-cms core:<br/>

        <img border="0" src="https://www.transifex.com/projects/p/django-cms/resource/core/chart/image_png"/>


********
Frontend
********

In order to be able to work with the frontend tooling contributing to the
django CMS you need to have the following dependencies installed:

    1. `Node <https://nodejs.org/>`_ (will install npm as well).
    2. `Globally installed gulp <https://github.com/gulpjs/gulp/blob/master/docs/getting-started.md#1-install-gulp-globally>`_
    3. Local dependencies ``cd cms/static/cms && npm install``

Styles
------

We are using `Sass <http://sass-lang.com/>`_ for our styles. The files
are located within ``cms/static/cms/sass`` and can be compiled using the
`libsass <http://libsass.org/>`_ implementation of Sass compiler through
`Gulp <http://gulpjs.com/>`_.

In order to compile the stylesheets you need to run this command from the repo
root::

    cd cms/static/cms && gulp sass

While developing it is also possible to run a watcher that compiles Sass files
on change::

    cd cms/static/cms && gulp



Icons
-----

We are using `gulp-iconfont <https://github.com/backflip/gulp-iconfont>`_ to
generate icon webfonts into ``cms/static/cms/fonts/``. This also creates
``_iconography.scss`` within ``cms/static/cms/sass/components`` which adds all
the icon classes and ultimately compiles to css.

In order to compile the webfont you need to run::

    cd cms/static/cms && gulp icons

This simply takes all SVGs within ``cms/static/cms/fonts/src`` and embeds them
into the webfont. All classes will be automatically added to
``_iconography.scss`` as previously mentioned.



.. _security@django-cms.org: mailto:security@django-cms.org
.. _fork: http://github.com/divio/django-cms
.. _Sphinx: http://sphinx.pocoo.org/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _Aldryn Boilerplate : http://aldryn-boilerplate-bootstrap3.readthedocs.org/en/latest/guidelines/index.html
.. _django-cms-developers: http://groups.google.com/group/django-cms-developers
.. _GitHub : http://www.github.com
.. _GitHub help : http://help.github.com
.. _freenode : http://freenode.net/
.. _@djangocmsstatus : https://twitter.com/djangocmsstatus
.. _@djangocms : https://twitter.com/djangocms
.. _pull request : http://help.github.com/send-pull-requests/
.. _git : http://git-scm.com/
.. _restructuredText: http://docutils.sourceforge.net/docs/ref/rst/introduction.html


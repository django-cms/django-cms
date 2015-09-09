.. _contributing-documentation:

##########################
Contributing documentation
##########################

Perhaps considered "boring" by hard-core coders, documentation is sometimes even
more important than code! This is what brings fresh blood to a project, and
serves as a reference for old timers. On top of this, documentation is the one
area where less technical people can help most - you just need to write
simple, unfussy English. Elegance of style is a secondary consideration, and
your prose can be improved later if necessary.

Contributions to the documentation earn the greatest respect from the
core developers and the django CMS community.

Documentation should be:

- written using valid `Sphinx`_/`restructuredText`_ syntax (see below for
  specifics); the file extension should be ``.rst``
- wrapped at 100 characters per line
- written in English, using British English spelling and punctuation
- accessible - you should assume the reader to be moderately familiar with
  Python and Django, but not anything else. Link to documentation of libraries
  you use, for example, even if they are "obvious" to you

Merging documentation is pretty fast and painless.

Except for the tiniest of change, we recommend that you test them before
submitting. Follow the same steps above to fork and clone the project locally.
Next, create a virtualenv so you can install the documentation tools::

    virtualenv djcms-docs-env
    source djcms-docs-env/bin/activate
    pip install sphinx sphinx_rtd_theme

Now you can ``cd`` into the ``django-cms/docs`` directory and build the documentation::

    make html
    open build/html/index.html

This allows you to review your changes in your local browser.


********
Spelling
********

We use `sphinxcontrib-spelling <https://pypi.python.org/pypi/sphinxcontrib-spelling/>`_, which in
turn uses `pyenchant <https://pypi.python.org/pypi/pyenchant/>`_ and `enchant
<http://www.abisource.com/projects/enchant/>`_ to check the spelling of the documentation.

You need to check your spelling before submitting documentation.


Install the spelling software
=============================

Install ``sphinxcontrib-spelling`` and ``pyenchant`` in your virtualenv::

    pip install sphinxcontrib-spelling
    pip install pyenchant

You will need to install ``enchant`` too, if it's not already installed. The easy way to check is
to run ``make spelling`` from the ``docs`` directory. If it runs successfully, you don't need to do
anything, but if not you will have to install ``enchant`` for your system. For example, on OS X::

    brew install enchant

or Debian Linux::

    apt-get install enchant


Check spelling
==============

``make spelling`` will report::

    build finished with problems.
    make: *** [spelling] Error 1

if any errors are found, and misspelt words will be listed in ``build/spelling/output.txt``

If no spelling errors have been detected, ``make spelling`` will report::

    build succeeded.

Words that are not in the built-in dictionary can be added to ``docs/spelling_wordlist``. **If**
you are certain that a word is incorrectly flagged as misspelt, add it to the ``spelling_wordlist``
document, in alphabetical order. **Please do not add new words unless you are sure they should be
in there.**

If you find technical terms are being flagged, please check that you have capitalised them
correctly - ``javascript`` and ``css`` are **incorrect** spellings for example. Commands and
special names (of classes, modules, etc) in double backticks - `````` - will mean that they are not
caught by the spelling checker.


*********************
Making a pull request
*********************

Before you commit any changes, you need to check spellings with ``make spelling`` and rebuild the
docs using ``make html``. If everything looks good, then it's time to push your changes to GitHub
and open a pull request in the usual way.


***********************
Documentation structure
***********************

Our documentation is divided into the following main sections:

* :doc:`/introduction/index` (``introduction``): step-by-step, beginning-to-end tutorials to get
  you up and running
* :doc:`/how_to/index` (``how_to``): step-by-step guides covering more advanced development
* :doc:`/topics/index` (``topics``): explanations of key parts of the system
* :doc:`/reference/index` (``reference``): technical reference for APIs, key
  models
  and so on
* :doc:`/contributing/index` (``contributing``)
* :doc:`/upgrade/index` (``upgrade``)
* :doc:`/user/index` (``user``): guides for *using* rather than setting up or developing for the
  CMS


********************
Documentation markup
********************

Sections
========

We mostly follow the Python documentation conventions for section marking::

    ##########
    Page title
    ##########

    *******
    heading
    *******

    sub-heading
    ===========

    sub-sub-heading
    ---------------

    sub-sub-sub-heading
    ^^^^^^^^^^^^^^^^^^^

    sub-sub-sub-sub-heading
    """""""""""""""""""""""


Inline markup
=============

* use backticks - `````` - for:
    * literals::

        The ``cms.models.pagemodel`` contains several important methods.

    * filenames::

        Before you start, edit ``settings.py``.

    * names of fields and other specific items in the Admin interface::

        Edit the ``Redirect`` field.

* use emphasis - ``*Home*`` - around:
    * the names of available options in or parts of the Admin::

        To hide and show the *Toolbar*, use the...

    * the names of important modes or states::

        ... in order to switch to *Edit mode*.

    * values in or of fields::

        Enter *Home* in the field.

* use strong emphasis - ``**`` - around:
    * buttons that perform an action::

        Hit **Save as draft**.



Rules for using technical words
===============================

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
==========

Create::

    .. _testing:

and use::

     :ref:`testing`

internal cross-references liberally.


Use absolute links to other documentation pages - ``:doc:`/how_to/toolbar``` -
rather than relative links - ``:doc:`/../toolbar```. This makes it easier to
run search-and-replaces when items are moved in the structure.


.. _restructuredText: http://docutils.sourceforge.net/docs/ref/rst/introduction.html
.. _Sphinx: http://sphinx.pocoo.org/

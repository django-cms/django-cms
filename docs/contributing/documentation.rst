.. _contributing-documentation:

**************************
Contributing documentation
**************************

Perhaps considered "boring" by hard-core coders, documentation is sometimes even
more important than code! This is what brings fresh blood to a project, and
serves as a reference for old timers. On top of this, documentation is the one
area where less technical people can help most - you just need to write
simple, unfussy English. Elegance of style is a secondary consideration, and
your prose can be improved later if necessary.

Documentation should be:

- written using valid `Sphinx`_/`restructuredText`_ syntax (see below for
  specifics); the file extension should be ``.rst``
- wrapped at 100 characters per line
- written in English, using British English spelling and punctuation
- accessible - you should assume the reader to be moderately familiar with
  Python and Django, but not anything else. Link to documentation of libraries
  you use, for example, even if they are "obvious" to you

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


Documentation markup
====================

Sections
--------

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
-------------

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

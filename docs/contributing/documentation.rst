.. _contributing-documentation:

Contributing documentation
==========================

Perhaps considered "boring" by hard-core coders, documentation is sometimes even more
important than code! This is what brings fresh blood to a project, and serves as a
reference for old timers. On top of this, documentation is the one area where less
technical people can help most - you just need to write simple, unfussy English.
Elegance of style is a secondary consideration, and your prose can be improved later if
necessary.

Contributions to the documentation earn the greatest respect from the core developers
and the django CMS community.

Documentation should be:

- written using valid Sphinx_/restructuredText_ syntax (see below for specifics); the
  file extension should be ``.rst``
- wrapped at 100 characters per line
- written in English, using British English spelling and punctuation
- accessible - you should assume the reader to be moderately familiar with Python and
  Django, but not anything else. Link to documentation of libraries you use, for
  example, even if they are "obvious" to you

Merging documentation is pretty fast and painless.

Except for the tiniest of change, we recommend that you test them before submitting.

Building the documentation
--------------------------

Follow the same steps above to fork and clone the project locally. Next, ``cd`` into the
``django-cms/docs`` and install the requirements:

.. code-block::

    make install

Now you can test and run the documentation locally using:

.. code-block::

    make run

This allows you to review your changes in your local browser using
``http://localhost:8001/``.

.. note::

    **What this does**

    ``make install`` is roughly the equivalent of:

    .. code-block::

        virtualenv env
        source env/bin/activate
        pip install -r requirements.txt
        cd docs
        make html

    ``make run`` runs ``make html``, and serves the built documentation on port 8001
    (that is, at ``http://localhost:8001/``.

    It then watches the ``docs`` directory; when it spots changes, it will automatically
    rebuild the documentation, and refresh the page in your browser.

Documentation requirements
--------------------------

The packages required by the documentation are managed by pip-tools_, which compiles
``requirements.txt`` ensuring compatibility between packages.

The packages that the documentation requires are in ``requirements.in`` which looks like
a regular requirements file. Specific versions of packages can be specified, or left
without a version in which case the latest version which is compatible with the other
packages will be used.

Example ``requirements.in``:

.. code-block::

    furo
    Sphinx>4
    sphinx-copybutton
    sphinxext-opengraph
    sphinxcontrib-spelling
    pyenchant>3

By running ``pip-compile`` the requirements are compiled into ``requirements.txt``.

Periodically requirements should be updated to ensure that new versions, most
importantly security patches, are used. This is done using the ``-U`` flag:

.. code-block::

    cd docs
    pip-compile -U

The generated ``requirements.txt`` pins specific versions and explains where each
required package comes from, for example:

.. code-block::

    datetime==4.3
        # via -r requirements.in
    django==3.2.5
        # via
        #   django-classy-tags
        #   django-cms
        #   django-formtools
        #   django-sekizai
        #   django-treebeard
    django-classy-tags==2.0.0
        # via
        #   django-cms
        #   django-sekizai
    django-cms==3.9.0
        # via -r requirements.in
    django-formtools==2.3
        # via django-cms

.. _spelling:

Spelling
--------

We use `sphinxcontrib-spelling <https://pypi.python.org/pypi/sphinxcontrib-spelling/>`_,
which in turn uses `pyenchant <https://pypi.python.org/pypi/pyenchant/>`_ and `enchant
<http://www.abisource.com/projects/enchant/>`_ to check the spelling of the
documentation.

You need to check your spelling before submitting documentation.

.. important::

    We use British English rather than US English spellings. This means that we use
    *colour* rather than *color*, *emphasise* rather than *emphasize* and so on.

Install the spelling software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``sphinxcontrib-spelling`` and ``pyenchant`` are Python packages that will be installed
in the virtualenv ``docs/env`` when you run ``make install`` (see above).

You will need to have ``enchant`` installed too, if it is not already. The easy way to
check is to run ``make spelling`` from the ``docs`` directory. If it runs successfully,
you don't need to do anything, but if not you will have to install ``enchant`` for your
system. For example, on OS X:

.. code-block::

    brew install enchant

or Debian Linux:

.. code-block::

    apt-get install enchant

Check spelling
~~~~~~~~~~~~~~

Run:

.. code-block::

    make spelling

in the ``docs`` directory to conduct the checks.

.. note::

    This script expects to find a virtualenv at ``docs/env``, as installed by ``make
    install`` (see above).

If no spelling errors have been detected, ``make spelling`` will report:

.. code-block::

    build succeeded.

Otherwise:

.. code-block::

    build finished with problems.
    make: *** [spelling] Error 1

It will list any errors in your shell. Misspelt words will be also be listed in
``build/spelling/output.txt``

Words that are not in the built-in dictionary can be added to
``docs/spelling_wordlist``. **If** you are certain that a word is incorrectly flagged as
misspelt, add it to the ``spelling_wordlist`` document, in alphabetical order. **Please
do not add new words unless you are sure they should be in there.**

If you find technical terms are being flagged, please check that you have capitalised
them correctly - ``javascript`` and ``css`` are **incorrect** spellings for example.
Commands and special names (of classes, modules, etc) in double backticks - `````` -
will mean that they are not caught by the spelling checker.

.. important::

    You may well find that some words that pass the spelling test on one system but not
    on another. Dictionaries on different systems contain different words and even
    behave differently. The important thing is that the spelling tests pass on `Travis
    <https://travis-ci.com/django-cms/django-cms>`_ when you submit a pull request.

Making a pull request
---------------------

Before you commit any changes, you need to check spellings with ``make spelling`` and
rebuild the docs using ``make html``. If everything looks good, then it's time to push
your changes to GitHub and open a pull request in the usual way.

Documentation structure
-----------------------

Our documentation is divided into the following main sections:

- :doc:`/introduction/index` (``introduction``): step-by-step, beginning-to-end
  tutorials to get you up and running
- :doc:`/how_to/index` (``how_to``): step-by-step guides covering more advanced
  development
- :doc:`/topics/index` (``topics``): explanations of key parts of the system
- :doc:`/reference/index` (``reference``): technical reference for APIs, key models and
  so on
- :doc:`/contributing/index` (``contributing``)
- :doc:`/upgrade/index` (``upgrade``)
- :doc:`/whoisbehind/index` (``who``): who is behind the django CMS project

Documentation markup
--------------------

Sections
~~~~~~~~

We mostly follow the Python documentation conventions for section marking:

.. code-block::

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
~~~~~~~~~~~~~

- use backticks - `````` - for:
      - literals:

        .. code-block::

            The ``cms.models.pagemodel`` contains several important methods.

      - filenames:

        .. code-block::

            Before you start, edit ``settings.py``.

      - names of fields and other specific items in the Admin interface:

        .. code-block::

            Edit the ``Redirect`` field.
- use emphasis - ``*Home*`` - around:
      - the names of available options in or parts of the Admin:

        .. code-block::

            To hide and show the *Toolbar*, use the...

      - the names of important modes or states:

        .. code-block::

            ... in order to switch to *Edit mode*.

      - values in or of fields:

        .. code-block::

            Enter *Home* in the field.
- use strong emphasis - ``**`` - around:
      - buttons that perform an action:

        .. code-block::

            Hit **View published** or **Save as draft**.

Rules for using technical words
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There should be one consistent way of rendering any technical word, depending on its
context. Please follow these rules:

- in general use, simply use the word as if it were any ordinary word, with no
  capitalisation or highlighting: "Your placeholder can now be used."
- at the start of sentences or titles, capitalise in the usual way: "Placeholder
  management guide"
- when introducing the term for the the first time, or for the first time in a document,
  you may highlight it to draw attention to it: "**Placeholders** are special model
  fields".
- when the word refers specifically to an object in the code, highlight it as a literal:
  "``Placeholder`` methods can be overwritten as required" - when appropriate, link the
  term to further reference documentation as well as simply highlighting it.

References
~~~~~~~~~~

Create:

.. code-block::

    .. _testing:

and use:

.. code-block::

    :ref:`testing`

internal cross-references liberally.

Use absolute links to other documentation pages - ``:doc:`/how_to/toolbar``` - rather
than relative links - ``:doc:`/../toolbar```. This makes it easier to run
search-and-replaces when items are moved in the structure.

.. _pip-tools: https://github.com/jazzband/pip-tools

.. _restructuredtext: http://docutils.sourceforge.net/docs/ref/rst/introduction.html

.. _sphinx: http://sphinx-doc.org//

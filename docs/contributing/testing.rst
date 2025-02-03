
Running and writing tests
=========================

Good code needs tests.

A project like django CMS simply can't afford to incorporate new code that doesn't come
with its own tests.

Tests provide some necessary minimum confidence: they can show the code will behave as
it expected, and help identify what's going wrong if something breaks it.

Not insisting on good tests when code is committed is like letting a gang of teenagers
without a driving license borrow your car on a Friday night, even if you think they are
very nice teenagers and they really promise to be careful.

We certainly do want your contributions and fixes, but we need your tests with them too.
Otherwise, we'd be compromising our codebase.

So, you are going to have to include tests if you want to contribute. However, writing
tests is not particularly difficult, and there are plenty of examples to crib from in
the code to help you.

Running tests
-------------

There's more than one way to do this, but here's one to help you get started:

.. code-block::

    # create a virtual environment
    virtualenv test-django-cms

    # activate it
    cd test-django-cms/
    source bin/activate

    # get django CMS from GitHub
    git clone https://github.com/django-cms/django-cms.git

    # install the dependencies for testing
    # note that requirements files for other Django versions are also provided
    pip install -r django-cms/test_requirements/django-X.Y.txt

    # run the test suite
    # note that you must be in the django-cms directory when you do this,
    # otherwise you'll get "Template not found" errors
    cd django-cms
    python manage.py test

It can take a few minutes to run.

When you run tests against your own new code, don't forget that it's useful to repeat
them for different versions of Python and Django.

Problems running the tests
~~~~~~~~~~~~~~~~~~~~~~~~~~

We are working to improve the performance and reliability of our test suite. We're aware
of certain problems, but need feedback from people using a wide range of systems and
configurations in order to benefit from their experience.

Please report any issues on our `GitHub repository
<https://github.com/django-cms/django-cms/issues>`_.

If you can help *improve* the test suite, your input will be especially valuable.

OS X users
++++++++++

In some versions of OS X, ``gettext`` needs to be installed so that it is available to
Django. If you run the tests and find that various tests in ``cms.tests.frontend`` raise
errors, it's likely that you have this problem.

A solution is:

.. code-block::

    brew install gettext && brew link --force gettext

(This requires the installation of `Homebrew <http://brew.sh>`_)

``ERROR: test_copy_to_from_clipboard (cms.tests.frontend.PlaceholderBasicTests)``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You may find that a single frontend test raises an error. This sometimes happens, for
some users, when the entire suite is run. To work around this you can invoke the test
class on its own:

.. code-block::

    manage.py test cms.PlaceholderBasicTests

and it should then run without errors.

``ERROR: zlib is required unless explicitly disabled using --disable-zlib, aborting``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you run into that issue, make sure to install zlib using Homebrew:

.. code-block::

    brew install libjpeg zlib && brew link --force zlib

Advanced testing options
~~~~~~~~~~~~~~~~~~~~~~~~

Run ``manage.py test --help`` for the full list of advanced options.

Use ``--parallel`` to distribute the test cases across your CPU cores.

Use ``--failed`` to only run the tests that failed during the last run.

Use ``--retest`` to run the tests using the same configuration as the last run.

Use ``--vanilla`` to bypass the advanced testing system and use the built-in Django test
command.

To use a different database, set the ``DATABASE_URL`` environment variable to a
dj-database-url compatible value.

Running Frontend Tests
----------------------

We have two types of frontend tests: unit tests and integration tests. For unit tests we
are using `Karma <http://karma-runner.github.io/>`_ as a test runner and `Jasmine
<http://jasmine.github.io/>`_ as a test framework.

In order to be able to run them you need to install necessary dependencies as outlined
in :ref:`frontend tooling installation instructions <contributing_frontend>`.

Linting runs against the test files as well with ``gulp lint``. In order to run
linting continuously, do:

.. code-block::

    gulp watch

Unit tests
~~~~~~~~~~

Unit tests can be run like this:

.. code-block::

    gulp unitTest

If your code is failing and you want to run only specific files, you can provide the
``--tests`` parameter with comma separated file names, like this:

.. code-block::

    gulp unitTest --tests=cms.base,cms.modal

If you want to run tests continuously you can use the watch command:

.. code-block::

    gulp unitTest --watch

This will rerun the suite whenever source or test file is changed. By default the tests
are running on `PhantomJS <http://phantomjs.org/>`_, but when running Karma in watch
mode you can also visit the server it spawns with an actual browser.

    INFO [karma]: Karma v0.13.15 server started at http://localhost:9876/

On Travis CI we are using SauceLabs integration to run tests in a set of different real
browsers, but you can opt out of running them on saucelabs using ``[skip saucelabs]``
marker in the commit message, similar to how you would skip the build entirely using
``[skip ci]``.

We're using Jasmine as a test framework and Istanbul as a code coverage tool.

Writing tests
-------------

Contributing tests is widely regarded as a very prestigious contribution (you're making
everybody's future work much easier by doing so). We'll always accept contributions of a
test without code, but not code without a test - which should give you an idea of how
important tests are.

:ref:`See how to write a test patch <test-writing>`.

What we need
~~~~~~~~~~~~

We have a wide and comprehensive library of unit-tests and integration tests with good
coverage.

Generally tests should be:

- Unitary (as much as possible). i.e. should test as much as possible only one
  function/method/class. That's the very definition of unit tests. Integration tests are
  interesting too obviously, but require more time to maintain since they have a higher
  probability of breaking.
- Short running. No hard numbers here, but if your one test doubles the time it takes
  for everybody to run them, it's probably an indication that you're doing it wrong.
- Easy to understand. If your test code isn't obvious, please add comments on what it's
  doing.

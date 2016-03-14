..  _testing:

#########################
Running and writing tests
#########################

Good code needs tests.

A project like django CMS simply can't afford to incorporate new code that
doesn't come with its own tests.

Tests provide some necessary minimum confidence: they can show the code will
behave as it expected, and help identify what's going wrong if something breaks
it.

Not insisting on good tests when code is committed is like letting a gang of
teenagers without a driving licence borrow your car on a Friday night, even if
you think they are very nice teenagers and they really promise to be careful.

We certainly do want your contributions and fixes, but we need your tests with
them too. Otherwise, we'd be compromising our codebase.

So, you are going to have to include tests if you want to contribute. However,
writing tests is not particularly difficult, and there are plenty of examples to
crib from in the code to help you.


*************
Running tests
*************

There's more than one way to do this, but here's one to help you get started::

    # create a virtual environment
    virtualenv test-django-cms

    # activate it
    cd test-django-cms/
    source bin/activate

    # get django CMS from GitHub
    git clone git@github.com:divio/django-cms.git

    # install the dependencies for testing
    # note that requirements files for other Django versions are also provided
    pip install -r django-cms/test_requirements/django-X.Y.txt

    # run the test suite
    # note that you must be in the django-cms directory when you do this,
    # otherwise you'll get "Template not found" errors
    cd django-cms
    python manage.py test


It can take a few minutes to run. Note that the selenium tests included in the
test suite require that you have Firefox installed.

When you run tests against your own new code, don't forget that it's useful to
repeat them for different versions of Python and Django.


Problems running the tests
==========================

We are working to improve the performance and reliability of our test suite. We're aware of certain
problems, but need feedback from people using a wide range of systems and configurations in order
to benefit from their experience.

Please use the open issue `#3684 Test suite is error-prone
<https://github.com/divio/django-cms/issues/3684>`_ on our GitHub repository to report such
problems.

If you can help *improve* the test suite, your input will be especially valuable.


OS X users
----------

In some versions of OS X, ``gettext`` needs to be installed so that it is
available to Django. If you run the tests and find that various tests in
``cms.tests.frontend`` and ``cms.tests.reversion_tests.ReversionTestCase``
raise errors, it's likely that you have this problem.

A solution is::

    brew install gettext && brew link --force gettext

(This requires the installation of `Homebrew <http://brew.sh>`_)

``ERROR: test_copy_to_from_clipboard (cms.tests.frontend.PlaceholderBasicTests)``
---------------------------------------------------------------------------------

You may find that a single frontend test raises an error. This sometimes happens, for some users,
when the entire suite is run. To work around this you can invoke the test class on its own::

    manage.py test cms.PlaceholderBasicTests

and it should then run without errors.


Advanced testing options
========================

Run ``manage.py test --help`` for full list of advanced options.

Use ``--parallel`` to distribute the test cases across your CPU cores.

Use ``--failed`` to only run the tests that failed during the last run.

Use ``--retest`` to run the tests using the same configuration as the last run.

Use ``--vanilla`` to bypass the advanced testing system and use the built-in
Django test command.

Use ``--migrate`` to run migrations during tests.

To use a different database, set the ``DATABASE_URL`` environment variable to a
dj-database-url compatible value.


Using X virtual framebuffer for headless frontend testing
---------------------------------------------------------

On Linux systems with X you can use `X virtual framebuffer
<http://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml>`_ to run frontend tests headless
(without the browser window actually showing). To do so, it's recommended to use the ``xvfb-run``
script to run tests.

.. important::

    The frontend tests have a minimum screen size to run successfully. You must
    set the screen size of the virtual frame buffer to at least 1280x720x8.
    You may do so using ``xvfb-run -s"-screen 0 1280x720x8" ...``.


*************
Writing tests
*************

Contributing tests is widely regarded as a very prestigious contribution (you're
making everybody's future work much easier by doing so). We'll always accept contributions of
test without code, but not code without test - which should give you an idea of how important
tests are.


What we need
============

We have a wide and comprehensive library of unit-tests and integration tests
with good coverage.

Generally tests should be:

* Unitary (as much as possible). i.e. should test as much as possible only one
  function/method/class. That's the very definition of unit tests. Integration
  tests are interesting too obviously, but require more time to maintain since
  they have a higher probability of breaking.
* Short running. No hard numbers here, but if your one test doubles the time it
  takes for everybody to run them, it's probably an indication that you're doing
  it wrong.
* Easy to understand. If your test code isn't obvious, please add comments on
  what it's doing.

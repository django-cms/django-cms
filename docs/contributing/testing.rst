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
    pip install -Ur django-cms/test_requirements/django-1.6.txt

    # run the test suite
    # note that you must be in the django-cms directory when you do this,
    # otherwise you'll get "Template not found" errors
    cd django-cms
    python develop.py test


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

In some versions of OS X, getttext needs to be installed so that it is
available to Django. If you run the tests and find that various tests in
``cms.tests.frontend`` and ``cms.tests.reversion_tests.ReversionTestCase``
raise errors, it's likely that you have this problem.

A solution is::

    brew install gettext && brew link --force gettext

(This requires the installation of `Homebrew <http://brew.sh>`_)

ERROR: test_copy_to_from_clipboard (cms.tests.frontend.PlaceholderBasicTests)
-----------------------------------------------------------------------------

You may find that a single frontend test raises an error. This sometimes happens, for some users,
when the entire suite is run. To work around this you can invoke the test class on its own::

    develop.py test cms.PlaceholderBasicTests

and it should then run without errors.

Advanced testing options
========================

``develop.py`` is the django CMS development helper script.

To use a different database, set the ``DATABASE_URL`` environment variable to a
dj-database-url compatible value.

.. program:: develop.py

.. option:: -h, --help

    Show help.

.. option:: --version

    Show CMS version.

.. option:: --user

    Specifies a custom user model to use for testing, the shell, or the server.  The name must be in the format <app name>.<model name>, and the custom app must reside in the cms.test_utils.projects module.


``develop.py test``
-------------------

.. program:: develop.py test

Runs the test suite. Optionally takes test labels as arguments to limit the tests which should be run.
Test labels should be in the same format as used in ``manage.py test``.

.. option:: --xvfb

    Use a virtual X framebuffer for frontend testing, requires `xvfbwrapper <https://github.com/cgoldberg/xvfbwrapper>`_ to be installed.

    With this option you won't need a physical display.

.. option:: --parallel

    Runs tests in parallel, using one worker process per available CPU core.

    Cannot be used together with :option:`develop.py test --failfast`.

    .. note::

        The output of the worker processes will be shown interleaved, which means that you'll get the
        results from each worker process individually, which might cause confusing output at the end of
        the test run.

.. option:: --failfast

    Stop running tests on the first failure or error.


``develop.py timed test``
-------------------------

.. program:: develop.py timed test

Run the test suite and print the ten slowest tests. Optionally takes test labels as arguments to limit the tests which should be run.
Test labels should be in the same format as used in ``manage.py test``.


``develop.py isolated test``
----------------------------

.. program:: develop.py isolated test

Runs each test in the test suite in a new process, thus making sure that tests don't leak state. This takes a
very long time to run. Optionally takes test labels as arguments to limit the tests which should be run.
Test labels should be in the same format as used in ``manage.py test``.

.. option:: --parallel

    Same as :option:`develop.py test --parallel`.


``develop.py server``
---------------------

.. program:: develop.py server

Run a server locally for testing. This is similar to ``manage.py runserver``.

.. option:: --port <port>

    Port to bind to. Defaults to 8000.

.. option:: --bind <bind>

    Interface to bind to. Defaults to 127.0.0.1.

.. option:: --migrate

    Use migrations instead of plain syncdb.

.. option:: application-name, migration-number

    Options to specify a single migration to migrate to. When using Django 1.6
    it only works if --migrate option is specified.



``develop.py shell``
--------------------

.. program:: develop.py shell

Opens a Django shell. This is similar to ``manage.py shell``.


``develop.py compilemessages``
------------------------------

.. program:: develop.py compilemessages

Compiles the po files to mo files. This is similar to ``manage.py compilemessages``.


*************
Writing tests
*************

Contributing tests is widely regarded as a very prestigious contribution (you're
making everybody's future work much easier by doing so). Good karma for you.
Cookie points. Maybe even a beer if we meet in person :)

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

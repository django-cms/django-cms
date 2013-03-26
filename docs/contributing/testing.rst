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
    pip install -r django-cms/test_requirements/django-1.4.txt 
    # run the test suite
    django-cms/runtests.py

It can take a few minutes to run.

When you run tests against your own new code, don't forget that it's useful to
repeat them for different versions of Python and Django.

multiple environments
=====================

There is a ```tox`` <http://tox.readthedocs.org/en/latest/>`_ configuration
that allows running the testsuite in a number of combinations of python and
django with just one command.::

    # install tox and detox. It's up to you if you want to install this tool
    # globally or inside a virtualenv. tox automatically creates
    # virtualenvs.
    pip install tox detox

    # run the testsuite for all supported environments
    tox
    # OR run the testsuite for all supported environments simultaneously
    # in multiple processes
    detox

    # OR run the testsuite in a specific environment (see tox.ini for all
    # possibilities)
    detox -e py26-django-dev,py27-django-dev

``detox`` is just a wrapper around ``tox`` that runs each environment in a
parallel process.

It is also possible to only run specific test cases::

    # run a specific testcase in the default environments
    tox -- PluginsTestCase.test_add_edit_plugin
    # run a specific testcase in specific environments
    tox -e py27-django14,py27-django-dev -- PluginsTestCase.test_add_edit_plugin


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
  
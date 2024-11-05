..  _contributing_patch:

####################
Contributing a patch
####################

.. _start-contributing:

**********
The basics
**********

The basic workflow for a code contribution will typically run as follows:

#. Fork the `django CMS project <https://github.com/django-cms/django-cms>`_ GitHub repository to your
   own GitHub account
#. Clone your fork locally::

    git clone git@github.com:YOUR_USERNAME/django-cms.git

#. Create a virtualenv::

    cd django-cms
    python3 -m venv .venv
    source .venv/bin/activate

#. Install its dependencies::

    pip install -r test_requirements/django-X.Y.txt

   Replace ``X.Y`` with whichever version of Django you want to work with.
   Check the supported versions in the "test_requirements/" directory

#. Create a new branch for your work::

    git checkout -b my_fix

#. Edit the django CMS codebase to implement the fix or feature.
#. Run the test suite::

    python manage.py test

#. Commit and push your code::

    git commit
    git push origin my_fix

#. Open a pull request on GitHub.

.. _test-writing:

*******************
How to write a test
*******************

The django CMS test suite contains a mix of unit tests, functional tests, regression tests and
integration tests.

Depending on your contribution, you will write a mix of them.

Let's start with something simple. We'll assume you have set up your environment correctly as
:ref:`described above <start-contributing>`.

Let's say you want to test the behaviour of the ``CMSPluginBase.render`` method:

.. code-block:: python

    class CMSPluginBase(admin.ModelAdmin, metaclass=CMSPluginBaseMetaclass):

        ...

        def render(self, context, instance, placeholder):
            context['instance'] = instance
            context['placeholder'] = placeholder
            return context

Writing a unit test for it will require us to test whether the returned ``context`` object contains
the declared attributes with the correct values.

We will start with a new class in an existing django CMS test module (``cms.tests.test_plugins`` in
this case):

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):
        pass

Let's try to run it:

.. code-block:: bash

    python manage.py test cms.tests.test_plugins.SimplePluginTestCase


This will call the new test case class only and it's handy when creating new tests and iterating
quickly through the steps. A full test run (``python manage.py test``) is required before opening
a pull request.

This is the output you'll get::

    Found 0 test(s).
    System check identified no issues (0 silenced).

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    NO TESTS RAN

Which is correct as we have no test in our test case. Let's add an empty one:

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):

        def test_render_method(self):
            pass

Running the test command again will return a slightly different output::

    Found 1 test(s).
    Creating test database for alias 'default'...
    System check identified no issues (0 silenced).
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.001s

    OK
    Destroying test database for alias 'default'...

This looks better, but it's not that meaningful as we're not testing anything.

Write a real test:

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):

        def test_render_method(self):
            """
            Tests the CMSPluginBase.render method by checking that the appropriate variables
            are set in the returned context
            """
            from cms.api import create_page
            my_page = create_page('home', language='en', template='col_two.html')
            placeholder = my_page.get_placeholders(language='en')
            context = self.get_context('/', page=my_page)
            plugin = CMSPluginBase()

            new_context = plugin.render(context, None, placeholder)
            self.assertTrue('placeholder' in new_context)
            self.assertEqual(placeholder, context['placeholder'])
            self.assertTrue('instance' in new_context)
            self.assertIsNone(new_context['instance'])

and run it::

    Found 1 test(s).
    Creating test database for alias 'default'...
    System check identified no issues (0 silenced).
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.018s

    OK
    Destroying test database for alias 'default'...

The output is quite similar to the previous run, but the longer execution time gives us a hint that
this test is actually doing something.

Let's quickly check the test code.

To test ``CMSPluginBase.render`` method we need a RequestContext instance and a placeholder. As
``CMSPluginBase`` does not have any :ref:`configuration model <storing configuration>`,
the instance argument can be ``None``.

#. Create a page instance to get the placeholder
#. Get the placeholder by filtering the placeholders of the page instance on the language
#. Create a context instance by using the provided super class method
#. Call the render method on a ``CMSPluginBase`` instance; being stateless, it's easy to call
   ``render`` of a bare instance of the ``CMSPluginBase`` class, which helps in tests
#. Assert a few things the method must provide on the returned context instance

As you see, even a simple test like this assumes and uses many feature of the test utilities
provided by django CMS. Before attempting to write a test, take your time to explore the content of
``cms.test_utils`` package and check the shipped templates, example applications and, most of all,
the base ``testcases`` defined in ``cms.test_utils.testscases`` which provide *a lot* of useful
methods to prepare the environment for our tests or to create useful test data.


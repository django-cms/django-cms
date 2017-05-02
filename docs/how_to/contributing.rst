..  _contributing_patch:

#########################
How to contribute a patch
#########################

.. note:: For more background on the material covered in this how-to section, see the
   :ref:`contributing-code` and :ref:`testing` sections of the documentation.

django CMS is an open project, and welcomes the participation of anyone who would like to
contribute, whatever their any level of knowledge.

As well as code, we welcome contributions to django CMS's :ref:`documentation
<contributing-documentation>` and :ref:`translations <contributing-translations>`.

.. note::
   Feel free to dive into coding for django CMS in whichever way suits you. However, you need to be
   aware of the :ref:`guidelines <contributing-code>` and :ref:`policies <management>` for
   django CMS project development. Adhering to them will make much easier for the core developers
   to validate and accept your contribution.


.. _start-contributing:

**********
The basics
**********

The basic workflow for a code contribution will typically run as follows:

#. Fork the `django CMS project <https://github.com/divio/django-cms>`_ GitHub repository to your
   own GitHub account
#. Clone your fork locally::

    git clone git@github.com:YOUR_USERNAME/django-cms.git

#. Create a virtualenv::

    virtualenv cms-develop
    source cms-develop/bin/activate

#. Install its dependencies::

    cd django-cms
    pip install -r test_requirements/django-X.Y.txt

   Replace ``X.Y`` with whichever version of Django you want to work with.

#. Create a new branch for your work::

    git checkout -b my_fix

#. Edit the django CMS codebase to implement the fix or feature.
#. Run the test suite::

    python manage.py test

#. Commit and push your code::

    git commit
    git push origin my_fix

#. Open a pull request on GitHub.


.. _target-branches:

Target branches
===============

See :ref:`branch_policy` for information about branch policy.


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

    class CMSPluginBase(six.with_metaclass(CMSPluginBaseMetaclass, admin.ModelAdmin)):

        ...

        def render(self, context, instance, placeholder):
            context['instance'] = instance
            context['placeholder'] = placeholder
            return context

Writing a unit test for it will require us to test whether the returned ``context`` object contains
the declared attributes with the correct values.

We will start with a new class in an existing django CMS test module (``cms.tests.plugins`` in
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

    Creating test database for alias 'default'...

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    OK

Which is correct as we have no test in our test case. Let's add an empty one:

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):

        def test_render_method(self):
            pass

Running the test command again will return a slightly different output::

    Creating test database for alias 'default'...
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.001s

    OK

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
            placeholder = my_page.placeholders.get(slot='col_left')
            context = self.get_context('/', page=my_page)
            plugin = CMSPluginBase()

            new_context = plugin.render(context, None, placeholder)
            self.assertTrue('placeholder' in new_context)
            self.assertEqual(placeholder, context['placeholder'])
            self.assertTrue('instance' in new_context)
            self.assertIsNone(new_context['instance'])

and run it::

    Creating test database for alias 'default'...
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.044s

    OK

The output is quite similar to the previous run, but the longer execution time gives us a hint that
this test is actually doing something.

Let's quickly check the test code.

To test ``CMSPluginBase.render`` method we need a RequestContext instance and a placeholder. As
``CMSPluginBase`` does not have any :ref:`configuration model <storing configuration>`,
the instance argument can be ``None``.

#. Create a page instance to get the placeholder
#. Get the placeholder by filtering the placeholders of the page instance on the expected
   placeholder name
#. Create a context instance by using the provided super class method
#. Call the render method on a ``CMSPluginBase`` instance; being stateless, it's easy to call
   ``render`` of a bare instance of the ``CMSPluginBase`` class, which helps in tests
#. Assert a few things the method must provide on the returned context instance

As you see, even a simple test like this assumes and uses many feature of the test utilities
provided by django CMS. Before attempting to write a test, take your time to explore the content of
``cms.test_utils`` package and check the shipped templates, example applications and, most of all,
the base ``testcases`` defined in ``cms.test_utils.testscases`` which provide *a lot* of useful
methods to prepare the environment for our tests or to create useful test data.

********************
Submitting your code
********************

After the code and the tests are ready and packed in commits, you must submit it for review and
merge in the django CMS GitHub project.

As noted above, always create a new branch for your code, be it a fix or a new feature, before
committing changes, then create your pull request from your branch to the :ref:`target
branch <target-branches>` on django CMS.


Acceptance criteria
===================

Matching these criteria from the very beginning will help the core developers to be able
to review your submission more quickly and efficiently and will increase the chances of making a
successful pull request.

Please see our :ref:`development_policies` for guidance on which branches to use, how to prepare pull requests and so
on.

Features
--------

To be accepted, proposed features should have *at least*:

 * natural language documentation in the ``docs`` folder describing the feature, its usage and
   potentially backward incompatibilities.
 * inline documentation (comments and docstrings) in the critical areas of the code explaining
   the behaviour
 * appropriate test coverage
 * Python 2/3 compatibility
 * South and Django migrations (where applicable)

The pull request description must briefly describe the feature and the intended goal and benefits.

Bugs
----

To be accepted, proposed bug fixes should have *at least*:

 * inline documentation (comments and docstrings) in the critical areas of the code explaining
   the behaviour
 * at least 1 regression test that demonstrates the issue and the fix
 * Python 2/3 compatibility
 * South and Django migrations (where applicable)

The pull request description must briefly describe the bug and the steps for its solution; in case
the bug has been opened elsewhere, it must be linked in the pull request description, describing
the fix.

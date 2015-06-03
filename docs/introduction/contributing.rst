..  _tutorial_contributing:_

============
Contributing
============

.. note:: The topics of this chapter is covered in more details into the :ref:`contributing` and
          :ref:`testing` sections of the documentation

django CMS is an open source and open projects which welcomes anyone who want to provide its
contribution at any level of knowledge.

You can contribute code, :ref:`documentation <contributing-documentation>` and
:ref:`translations <contributing-translations>`.

.. _start-contributing:

**************************
Starting contributing code
**************************

Before actually coding anything, please read the :ref:`guidelines <contributing-code>` and the
:ref:`policies <management>` regulating the django CMS project development. Adhering to them
will make much easier for the core developers to validate and accept your contribution.

The basic step to contribute are:

#. fork :ref:`django CMS project <https://github.com/divio/django-cms>` repostory on github
#. clone your fork on your local computer::

    git clone git@github.com:YOUR_USERNAME/django-cms.git

#. create a virtualenv::

    virtualenv cms-develop
    source cms-develop/bin/activate

#. install the dependencies::

    cd django-cms
    pip install -r test_requirements/django-1.7.txt

   or whichever Django version you target

#. code you contribution
#. run the tests::

    python develop.py test

#. commit and push your code into a feature branch::

    git checkout -b my_fix
    git commit
    git push origin my_fix

#. open a pull request on github

Target branches
===============

At one point in time django CMS project will have at least two active branches:

* latest ``support/version.x`` which you sholud target if you submit bugfixes for ``version.x``
* ``develop`` for new features and bugfixes for latest version if a corresponding
  ``support/version.y`` does not exists (yet)


*******************
How to write a test
*******************

django CMS test suite contains a mix of unit tests, functional tests, regression tests and
integration tests.

Depending on your contribution, you will write a mix of them.

Let's start with something simple.

Let's say you want to test the behavior of ``CMSPluginBase.render`` method:

.. code-block:: python

    class CMSPluginBase(six.with_metaclass(CMSPluginBaseMetaclass, admin.ModelAdmin)):

        ...

        def render(self, context, instance, placeholder):
            context['instance'] = instance
            context['placeholder'] = placeholder
            return context

Writing a unit test for it will require us to test whether the return context object contains the
declared attributes with the correct values.

We will start with a new class in an existing django CMS test module (``cms.tests.plugins`` in
this case):

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):
        pass

Let's try to run it (given you've setup correctly your environment as in `start-contributing`_:

.. code-block:: bash

    python develop.py test cms.SimplePluginTestCase

This will call the new test case class only and it's hany when creating new tests and iterating
quickly throught the steps. A full test run (``python develop.py test``) is required before opening
a pull request.

This is the output you'll get::

    Creating test database for alias 'default'...

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    OK

Which is correct as we have no test in our test case. Let's add and (empty) one:

.. code-block:: python

    class SimplePluginTestCase(CMSTestCase):

        def test_render_method(self):
            pass

Running the test command again will return a sighltly different output::

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

Output is quite similar than the previous run, only the longer execution time gives us a hint that
this test is actually doing something.

Let's quickly check the test code.

To test ``CMSPluginBase.render`` method we need a RequestContext instance and a placeholder. As
``CMSPluginBase`` does not have any :ref:`configuration model`, the instance argument can be ``None``.

#. Create a page instance to get the placeholder
#. Get the placeholder by filtering the placeholders of the page instance on the expected
   placeholder name
#. Create a context instance by using the provided super class method
#. Call the render method on a CMSPluginBase instance; being stateless, it's easy to call
   ``render`` of a bare instance of the ``CMSPluginBase`` class, which helps in tests
#. Assert a few things the method must provide on the returned context instance

As you see, even a simple test like this, assumes and uses many feature of the test utils provided
by django CMS. Before attempting to write a test, take your time to explore the content of
``cms.test_utils`` package and check the shipped templates, example applications and, most of all,
the base testcases defined in ``cms.test_utils.testscases`` which provide *a lot* of useful
methods to prepare the environment for our tests or to create useful test data.
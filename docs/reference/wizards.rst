.. versionadded:: 3.2

.. _wizard_reference:

########################
Content creation wizards
########################

See the :ref:`How-to section on wizards <wizard_how_to>` for an introduction to
creating wizards.

Wizard classes are sub-classes of ``cms.wizards.wizard_base.Wizard``.

They need to be registered with the ``cms.wizards.wizard_pool.wizard_pool``::

    wizard_pool.register(my_app_wizard)

Finally, a wizard needs to be instantiated, for example::

    my_app_wizard = MyAppWizard(
        title="New MyApp",
        weight=200,
        form=MyAppWizardForm,
        description="Create a new MyApp instance",
    )

When instantiating a Wizard object, use the keywords:

    :title: The title of the wizard. This will appear in a large font size on
            the wizard "menu"
    :weight: The "weight" of the wizard when determining the sort-order.
    :form: The form to use for this wizard. This is mandatory, but can be
           sub-classed from `django.forms.form` or `django.forms.ModelForm`.
    :model: If a Form is used above, this keyword argument must be supplied and
            should contain the model class. This is used to determine the unique
            wizard "signature" amongst other things.
    :template_name: An optional template can be supplied.
    :description: The description is optional, but if it is not supplied, the
                  CMS will create one from the pattern:
                  "Create a new «model.verbose_name» instance."
    :edit_mode_on_success: If set, the CMS will switch the user to edit-mode by
                           adding an ``edit`` param to the query-string of the
                           URL returned by ``get_success_url``. This is ``True``
                           by default.


***********
Base Wizard
***********

All wizard classes should inherit from ``cms.wizards.wizard_base.Wizard``. This
class implements a number of methods that may be overridden as required.

*******************
Base Wizard methods
*******************

get_description
===============

Simply returns the ``description`` property assigned during instantiation or one
derived from the model if description is not provided during instantiation.
Override this method if this needs to be determined programmatically.


get_title
=========

Simply returns the ``title`` property assigned during instantiation. Override
this method if this needs to be determined programmatically.


get_success_url
===============

Once the wizard has completed, the user will be redirected to the URL of the new
object that was created. By default, this is done by return the result of
calling the ``get_absolute_url`` method on the object. This may then be modified
to force the user into edit mode if the wizard property ``edit_mode_on_success``
is True.

In some cases, the created content will not implement ``get_absolute_url`` or
that redirecting the user is undesirable. In these cases, simply override this
method. If ``get_success_url`` returns ``None``, the CMS will just redirect to
the current page after the object is created.

This method is called by the CMS with the parameter:

    :obj: The created object


get_weight
==========

Simply returns the ``weight`` property assigned during instantiation. Override
this method if this needs to be determined programmatically.


user_has_add_permission
=======================

This should return a boolean reflecting whether the user has permission to
create the underlying content for the wizard.

This method is called by the CMS with these parameters:

    :user: The current user
    :page: The current CMS page the user is viewing when invoking the wizard



***************
``wizard_pool``
***************

``wizard_pool`` includes a read-only property ``discovered`` which returns the
Boolean ``True`` if wizard-discovery has already occurred and ``False``
otherwise.

*******************
Wizard pool methods
*******************

is_registered
=============

Sometimes, it may be necessary to check to see if a specific wizard has been
registered. To do this, simply call::

    value = wizard_pool.is_registered(«wizard»)


register
========

You may notice from the example above that the last line in the sample code is::

    wizard_pool.register(my_app_wizard)

This sort of thing should look very familiar, as a similar approach is used for
cms_apps, template tags and even Django's admin.

Calling the wizard pool's ``register`` method will register the provided wizard
into the pool, unless there is already a wizard of the same module and class
name. In this case, the register method will raise a
``cms.wizards.wizard_pool.AlreadyRegisteredException``.


unregister
==========

It may be useful to unregister wizards that have already been registered with
the pool. To do this, simply call::

    value = wizard_pool.unregister(«wizard»)

The value returned will be a Boolean: ``True`` if a wizard was successfully
unregistered or ``False`` otherwise.


get_entry
=========

If you would like to get a reference to a specific wizard in the pool, just call
``get_entry()`` as follows::

    wizard = wizard_pool.get_entry(my_app_wizard)


get_entries
===========

``get_entries()`` is useful if it is required to have a list of all registered
wizards. Typically, this is used to iterate over them all. Note that they will
be returned in the order of their ``weight``: smallest numbers for weight are
returned first.::

    for wizard in wizard_pool.get_entries():
        # do something with a wizard...


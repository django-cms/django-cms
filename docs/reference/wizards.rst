.. versionadded:: 3.2

.. _wizard_reference:

########################
Content creation wizards
########################

See the :ref:`How-to section on wizards <wizard_how_to>` for an introduction to
creating wizards.

Wizard classes are sub-classes of :class:`cms.wizards.wizard_base.Wizard`.

Before making a wizard available to the CMS it needs to be instantiated,
for example::

    my_app_wizard = MyAppWizard(
        title="New MyApp",
        weight=200,
        form=MyAppWizardForm,
        description="Create a new MyApp instance",
    )

When instantiating a Wizard object, use the keywords:

..  autoclass:: cms.wizards.wizard_base.WizardBase
    :members:

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
:edit_mode_on_success: Whether the user will get redirected to object edit url after a
                       successful creation or not. This only works if the object is registered 
                       for toolbar enabled models.


.. important::

    As of version 4 of django CMS wizards are no longer registered with the
    ``wizard_pool``. Instead you need to create a app config in ``cms_config.py``
    to register wizards.

.. versionadded:: 4.0

Wizards are made available to the CMS by adding a :class:`cms.app_base.CMSAppConfig`
subclass to your apps's `cms_config.py`. As an example, here's how the CMS itself
registers its wizards::

    class CMSCoreConfig(CMSAppConfig):
        cms_enabled = True  # Use cms core's functionality
        cms_wizards = [cms_page_wizard, cms_subpage_wizard]   # Namely, those wizards

For the above example the configuration might look like this::

    from .cms_wizards import my_app_wizard

    class MyAppConfig(CMSAppConfig):
        cms_enabled = True
        cms_wizards = [my_app_wizard]


************
Wizard class
************

..  module:: cms.wizards.wizard_base

..  autoclass:: cms.wizards.wizard_base.Wizard
    :members:
    :inherited-members:


*******
Helpers
*******

..  module:: cms.wizards.helpers

..  autofunction:: get_entry

..  autofunction:: get_entries


***********
wizard_pool
***********

.. warning::

    The wizard pool is deprecated since version 4.0 and will be removed in a future
    version.

..  module:: cms.wizards.wizard_pool

..  autodata:: cms.wizards.wizard_pool.wizard_pool
    :no-value:

..  autoclass:: cms.wizards.wizard_pool.WizardPool
    :members:
    :inherited-members:


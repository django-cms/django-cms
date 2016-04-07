.. versionadded:: 3.2

.. _wizard_how_to:

########################
Content creation wizards
########################

django CMS offers a framework for creating 'wizards' - helpers - for content editors.

They provide a simplified workflow for common tasks.

A django CMS Page wizard already exists, but you can create your own for other content types very easily.


********************************
Create a content-creation wizard
********************************

Creating a CMS content creation wizard for your own module is fairly easy.

To begin, create a folder in the root level of your module called
``cms_wizards.py``. In this file, import Wizard as follows::

    from cms.wizards.wizard_base import Wizard
    from cms.wizards.wizard_pool import wizard_pool

Then, simply subclass Wizard, instantiate it, then register it. If you were to
do this for ``MyApp``, it might look like this::

    # my_apps/forms.py

    from django import forms

    class MyAppWizardForm(forms.ModelForm):
        model = MyApp
        exclude = []


    # my_apps/cms_wizards.py

    from cms.wizards.wizard_base import Wizard
    from cms.wizards.wizard_pool import wizard_pool

    from .forms import MyAppWizardForm
    from .models import MyApp

    class MyAppWizard(Wizard):
        pass

    my_app_wizard = MyAppWizard(
        title="New MyApp",
        weight=200,
        form=MyAppWizardForm,
        description="Create a new MyApp instance",
    )

    wizard_pool.register(my_app_wizard)

That's it!

.. note::

    the module name ``cms_wizards`` is special, in that any such-named modules in
    your project's Python path will automatically be loaded, triggering the
    registration of any wizards found in them. Wizards may be declared and
    registered in other modules, but they might not be automatically loaded.

The above example is using a ModelForm, but you can also use ``forms.Form``.
In this case, you **must** provide the model class as another keyword argument
when you instantiate the Wizard object.

You must subclass ``cms.wizards.wizard_base.Wizard`` to use it. This is because
each wizard's uniqueness is determined by its class and module name.

See the :ref:`Reference section on wizards <wizard_reference>` for technical details of the wizards
API.

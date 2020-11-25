:sequential_nav: both

########################
Content creation wizards
########################

Content creation wizards allow you to make use of the toolbar's **Create** button in your own
applications. It opens up a simple dialog box with the basic fields required to create a new item.

django CMS uses it for creating Pages, but you can add your own models to it.

In the ``polls_cms_integration`` application, add a ``forms.py`` file::

    from django import forms

    from polls.models import Poll


    class PollWizardForm(forms.ModelForm):
        class Meta:
            model = Poll
            exclude = []

Then add a ``cms_wizards.py`` file, containing::

    from cms.wizards.wizard_base import Wizard
    from cms.wizards.wizard_pool import wizard_pool

    from polls_cms_integration.forms import PollWizardForm


    class PollWizard(Wizard):
        pass

    poll_wizard = PollWizard(
        title="Poll",
        weight=200,  # determines the ordering of wizards in the Create dialog
        form=PollWizardForm,
        description="Create a new Poll",
    )

    wizard_pool.register(poll_wizard)

Refresh the Polls page, hit the **Create** button in the toolbar - and the wizard dialog will open,
offering you a new wizard for creating Polls.

.. note::

    Once again, this particular example is for illustration only. In the case of a Poll, with
    its multiple Questions associated with it via foreign keys, we really want to be able to
    edit those questions at the same time too.

    That would require a much more sophisticated form and processing than is possible within the
    scope of this tutorial.

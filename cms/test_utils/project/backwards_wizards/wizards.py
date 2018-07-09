from cms.wizards.wizard_base import Wizard

from cms.test_utils.project.sampleapp.forms import SampleWizardForm


class SampleWizard(Wizard):
    pass


wizard = SampleWizard(
    title="Sample",
    weight=505,
    form=SampleWizardForm,
    description="Create something",
)

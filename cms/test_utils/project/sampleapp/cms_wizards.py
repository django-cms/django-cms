from cms.wizards.wizard_base import Wizard

from cms.test_utils.project.sampleapp.forms import SampleWizardForm


class SampleWizard(Wizard):
    pass


sample_wizard = SampleWizard(
    title="Sample",
    weight=105,
    form=SampleWizardForm,
    description="Create a new Sample",
)

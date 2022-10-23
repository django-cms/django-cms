from cms.test_utils.project.sampleapp.forms import SampleWizardForm
from cms.wizards.wizard_base import Wizard


class SampleWizard(Wizard):
    pass


sample_wizard = SampleWizard(
    title="Sample",
    weight=105,
    form=SampleWizardForm,
    description="Create a new Sample",
)

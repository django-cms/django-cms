from cms.test_utils.project.sampleapp.forms import SampleWizardForm
from cms.wizards.wizard_base import Wizard


class SampleWizard(Wizard):
    pass


wizard = SampleWizard(
    title="Sample",
    weight=505,
    form=SampleWizardForm,
    description="Create something",
)

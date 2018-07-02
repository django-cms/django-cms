from cms.app_base import CMSAppConfig
from cms.test_utils.project.sampleapp.cms_wizards import sample_wizard


class SampleAppConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [sample_wizard]

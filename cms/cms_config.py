from cms.app_base import CMSAppExtension, CMSAppConfig
from cms.cms_wizards import cms_page_wizard, cms_subpage_wizard


class CMSCoreConfig(CMSAppConfig):
    cms_enabled = True
    cms_wizards = [cms_page_wizard, cms_subpage_wizard]


class CMSCoreExtensions(CMSAppExtension):

    def __init__(self):
        self.wizards = {}  # this is instead of wizard_pool._entries

    def configure_wizards(self, cms_config):
        if not hasattr(cms_config, 'cms_wizards'):
            return
        for wizard in cms_config.cms_wizards:
            self.wizards[wizard.id] = wizard

    def configure_app(self, cms_config):
        self.configure_wizards(cms_config)

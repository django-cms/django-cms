from cms.app_base import CMSAppExtension


class CMSSomeFeatureConfig(CMSAppExtension):

    def __init__(self, *args, **kwargs):
        self.num_configured_apps = 0
        self.configured_apps = []

    def configure_app(self, cms_config):
        self.num_configured_apps += 1
        self.configured_apps.append(cms_config.app_config.label)

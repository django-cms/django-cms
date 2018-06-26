from cms.app_base import CMSAppConfig, CMSAppExtension


class CMSConfig(CMSAppConfig):
    app_with_cms_feature_enabled = False


class CMSExtension(CMSAppExtension):

    def configure_app(self, cms_config):
        pass

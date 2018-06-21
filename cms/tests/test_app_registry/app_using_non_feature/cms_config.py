from cms.app_base import CMSAppConfig


class NonFeatureCMSConfig(CMSAppConfig):
    # Attempting to use features from a cms app that doesnt define any
    # features
    app_with_cms_config_enabled = True

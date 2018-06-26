from cms.app_base import CMSAppConfig


class NonFeatureCMSConfig(CMSAppConfig):
    # Attempting to use features from a cms app that doesnt define a
    # configure_app method
    app_with_feature_not_implemented_enabled = True

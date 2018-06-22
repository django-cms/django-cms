from cms.app_base import CMSAppConfig


class CMSConfigConfig(CMSAppConfig):
    app_with_cms_feature_enabled = True
    # a test attr that should get changed to True by
    # app_with_cms_feature on successful configuration
    configured = False

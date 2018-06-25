from cms.app_base import CMSAppExtension


def some_function(*args, **kwargs):
    # this should not be called by autodiscover
    raise Exception('some_function called')


class SomeClass():
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeClass instantiated')


class CMSSomeFeatureConfig(CMSAppExtension):

    num_configured_apps = 0

    def configure_app(self, app):
        app.cms_config.configured = True
        self.num_configured_apps += 1


class SomeOtherClass():
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeOtherClass instantiated')

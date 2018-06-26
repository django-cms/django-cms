from cms.app_base import CMSAppExtension


def some_function(*args, **kwargs):
    # this should not be called by autodiscover
    raise Exception('some_function called')


class SomeClass(object):
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeClass instantiated')


class CMSSomeFeatureConfig(CMSAppExtension):

    def __init__(self, *args, **kwargs):
        self.num_configured_apps = 0
        self.configured_apps = []

    def configure_app(self, cms_config):
        self.num_configured_apps += 1
        self.configured_apps.append(cms_config.app_config.label)


class SomeOtherClass(object):
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeOtherClass instantiated')

from cms.app_registration import CMSAppConfig


def some_function(*args, **kwargs):
    # this should not be called by autodiscover
    raise Exception('some_function called')


class SomeClass():
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeClass instantiated')


class CMSSomeFeatureConfig(CMSAppConfig):

    def register_extension(self, app):
        pass


class SomeOtherClass():
    # this should not be picked up by autodiscover

    def __init__(self, *args, **kwargs):
        raise Exception('SomeOtherClass instantiated')

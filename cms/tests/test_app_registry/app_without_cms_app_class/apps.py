from django.apps import AppConfig


class WithoutCMSAppClassConfig(AppConfig):
    name = 'cms.tests.test_app_registry.app_without_cms_app_class'
    label = 'app_without_cms_app_class'

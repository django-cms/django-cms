from django.apps import AppConfig


class NonFeatureCMSConfig(AppConfig):
    name = 'cms.tests.test_app_registry.app_using_non_feature'
    label = 'app_using_non_feature'

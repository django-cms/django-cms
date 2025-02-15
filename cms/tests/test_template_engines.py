from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from cms.test_utils.testcases import CMSTestCase


class TemplateEngineTests(CMSTestCase):
    def test_accepts_custom_django_template_backend(self):
        """
        Test that django CMS accepts template engines that inherit from DjangoTemplates
        """
        custom_templates_settings = [
            {
                "BACKEND": "cms.test_utils.project.template_backends.CustomDjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": ["django.template.context_processors.request"],
                },
            }
        ]

        with override_settings(TEMPLATES=custom_templates_settings):
            from cms.utils.setup import validate_settings

            validate_settings()

    def test_rejects_non_django_template_backend(self):
        """
        Test that django CMS rejects template engines that don't inherit from DjangoTemplates
        """
        non_django_templates_settings = [
            {
                "BACKEND": "cms.test_utils.project.template_backends.NonDjangoTemplates",
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": ["django.template.context_processors.request"],
                },
            }
        ]

        with override_settings(TEMPLATES=non_django_templates_settings):
            from cms.utils.setup import validate_settings

            with self.assertRaises(ImproperlyConfigured) as context:
                validate_settings()

            self.assertIn(
                "django.template.backends.django.DjangoTemplates",
                str(context.exception),
                "Should reject non-Django template backends",
            )

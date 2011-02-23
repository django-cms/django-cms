from django.conf import settings

try:
    from xmlrunner.extra.djangotestrunner import XMLTestRunner as TestRunner
    # make sure we are backwards compatible regarding the output dir
    settings.TEST_OUTPUT_DIR = getattr(settings, 'JUNIT_OUTPUT_DIR', '.')
except:
    from django.test.simple import DjangoTestSuiteRunner as TestRunner

class CMSTestSuiteRunner(TestRunner):
    pass

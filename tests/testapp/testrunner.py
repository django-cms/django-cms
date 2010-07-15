from django.test.simple import DjangoTestSuiteRunner
from xmlrunner import XMLTestRunner


class DjangoXMLTestRunner(DjangoTestSuiteRunner):
    def run_suite(self, suite, **kwargs):
        return XMLTestRunner().run(suite)
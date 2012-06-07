from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.utils.unittest.suite import TestSuite
import operator
import os
import time

try:
    from xmlrunner import XMLTestRunner as runner
except:
    runner = False


TIMINGS = {}

def time_it(func):
    def _inner(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()

        TIMINGS[unicode(func)] = end - start
    return _inner


class TimingSuite(TestSuite):
    def addTest(self, test):
        test = time_it(test)
        super(TimingSuite, self).addTest(test)


class CMSTestSuiteRunner(DjangoTestSuiteRunner):
    use_runner = runner

    def run_suite(self, suite, **kwargs):
        if self.use_runner and not self.failfast and os.environ.get('XML_REPORTS', '0') == '1':
            return self.use_runner(
                output=getattr(settings, 'JUNIT_OUTPUT_DIR', '.')
            ).run(suite)
        else:
            return super(CMSTestSuiteRunner, self).run_suite(suite, **kwargs)

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = [app.split('.')[-1] for app in settings.APPS_TO_TEST]
        suite = super(CMSTestSuiteRunner, self).build_suite(test_labels, extra_tests, **kwargs)
        if os.environ.get('TIMETESTS', '0') == '1':
            return TimingSuite(suite)
        else:
            return suite

    def teardown_test_environment(self, **kwargs):
        super(CMSTestSuiteRunner, self).teardown_test_environment(**kwargs)
        if os.environ.get('TIMETESTS', False):
            by_time = sorted(
                    TIMINGS.iteritems(),
                    key=operator.itemgetter(1),
                    reverse=True)[:10]
            print("Ten slowest tests:")
            for func_name, timing in by_time:
                print("{t:.2f}s {f}".format(f=func_name, t=timing))


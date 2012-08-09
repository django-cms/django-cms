from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.utils.unittest.suite import TestSuite
import operator
import time


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
        
        
class JenkinsTestRunner(DjangoTestSuiteRunner):
    def run_suite(self, suite, **kwargs):
        from xmlrunner import XMLTestRunner
        return XMLTestRunner(output=settings.JUNIT_OUTPUT_DIR).run(suite)



class NormalTestRunner(DjangoTestSuiteRunner):
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = super(NormalTestRunner, self).build_suite(test_labels, extra_tests, **kwargs)
        if settings.TIME_TESTS:
            return TimingSuite(suite)
        else:
            return suite

    def teardown_test_environment(self, **kwargs):
        super(NormalTestRunner, self).teardown_test_environment(**kwargs)
        if settings.TIME_TESTS:
            by_time = sorted(
                    TIMINGS.iteritems(),
                    key=operator.itemgetter(1),
                    reverse=True)[:10]
            print("Ten slowest tests:")
            for func_name, timing in by_time:
                print("{t:.2f}s {f}".format(f=func_name, t=timing))


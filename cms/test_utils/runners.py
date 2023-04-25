import operator
import time

from django.test.simple import DjangoTestSuiteRunner
from django.utils.encoding import force_str
from django.utils.unittest import TestSuite

TIMINGS = {}

def time_it(func):
    def _inner(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()

        TIMINGS[force_str(func)] = end - start
    return _inner


class TimingSuite(TestSuite):
    def addTest(self, test):
        test = time_it(test)
        super().addTest(test)


class TimedTestRunner(DjangoTestSuiteRunner):
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels, extra_tests, **kwargs)
        return TimingSuite(suite)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        by_time = sorted(
                TIMINGS.items(),
                key=operator.itemgetter(1),
                reverse=True)[:10]
        print("Ten slowest tests:")
        for func_name, timing in by_time:
            print("{t:.2f}s {f}".format(f=func_name, t=timing))

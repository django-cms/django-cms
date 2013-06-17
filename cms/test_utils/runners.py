from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from cms.utils.compat.dj import force_unicode
import operator
import time
from django.utils.unittest import TestSuite


TIMINGS = {}

def time_it(func):
    def _inner(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()

        TIMINGS[force_unicode(func)] = end - start
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
                    TIMINGS.items(),
                    key=operator.itemgetter(1),
                    reverse=True)[:10]
            print(u"Ten slowest tests:")
            for func_name, timing in by_time:
                print(u"{t:.2f}s {f}".format(f=func_name, t=timing))


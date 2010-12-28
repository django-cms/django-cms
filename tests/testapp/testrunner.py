from django.test.simple import DjangoTestSuiteRunner

try:
	from xmlrunner import XMLTestRunner as runner
except:
    runner = False

class CMSTestSuiteRunner(DjangoTestSuiteRunner):
    use_runner = runner

    def run_suite(self, suite, **kwargs):
        if self.use_runner and not self.failfast:
            return self.use_runner().run(suite)
        else:
            return super(CMSTestSuiteRunner, self).run_suite(suite, **kwargs)
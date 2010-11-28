from django.test.simple import DjangoTestSuiteRunner

try:
	from xmlrunner import XMLTestRunner as runner
except:
    runner = False

class CMSDjangoTestRunner(DjangoTestSuiteRunner):
    use_runner = runner

    def run_suite(self, suite, **kwargs):
        if self.use_runner:
            return self.use_runner().run(suite)
        else:
            return super(CMSDjangoTestRunner, self).run_suite(suite, **kwargs)
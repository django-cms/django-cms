from cms.test_utils.cli import configure
import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jenkins', action='store_true', default=False,
            dest='jenkins')
    parser.add_argument('--jenkins-data-dir', default='.', dest='jenkins_data_dir')
    parser.add_argument('--coverage', action='store_true', default=False,
            dest='coverage')
    parser.add_argument('--failfast', action='store_true', default=False,
            dest='failfast')
    parser.add_argument('--verbosity', default=1)
    parser.add_argument('--time-tests', action='store_true', default=False,
            dest='time_tests')
    args = parser.parse_args()
    args.urlconf = 'cms.test_utils.project.urls'
    if getattr(args, 'jenkins', False):
        TEST_RUNNER = 'cms.test_utils.runners.JenkinsTestRunner'
    else:
        TEST_RUNNER = 'cms.test_utils.runners.NormalTestRunner'
    JUNIT_OUTPUT_DIR = getattr(args, 'jenkins_data_dir', '.')
    TIME_TESTS = getattr(args, 'time_tests', False)
    configure(TEST_RUNNER=TEST_RUNNER, JUNIT_OUTPUT_DIR=JUNIT_OUTPUT_DIR,
        TIME_TESTS=TIME_TESTS, ROOT_URLCONF='cms.test_utils.project.urls')
    from django.conf import settings
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    test_runner = TestRunner(verbosity=args.verbosity, interactive=False, failfast=args.failfast)
    failures = test_runner.run_tests(['cms', 'menus'])
    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    main()

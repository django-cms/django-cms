import sys
if __name__ == "__main__":
    from run_tests import configure_settings
    test_args, test_labels, failfast, settings = configure_settings(False, sys.argv[:])
    from django.core.management import execute_manager
    execute_manager(settings, argv=test_args[:])
    
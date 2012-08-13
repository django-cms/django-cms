#!/usr/bin/env python
from __future__ import with_statement
import pkgutil
import pyclbr
import subprocess
import argparse
from unittest.loader import findTestCases
from cms.test_utils.cli import configure
from cms.test_utils.tmpdir import temp_dir
import sys
import os.path
import unittest
from django.utils.unittest.loader import defaultTestLoader

def main(argv,test_runner='cms.test_utils.runners.NormalTestRunner', junit_output_dir='.',
         time_tests=False, failfast=False):
    testlist = []
    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            configure(TEST_RUNNER=test_runner, JUNIT_OUTPUT_DIR=junit_output_dir,
                      TIME_TESTS=time_tests, ROOT_URLCONF='cms.test_utils.project.urls',
                      STATIC_ROOT=STATIC_ROOT, MEDIA_ROOT=MEDIA_ROOT)
            from django.conf import settings
            tests = defaultTestLoader.discover('cms/tests',pattern="__init__.py")
            for suite in tests:
                for test in suite:
                    for t in test:
                        testlist.append(t.__class__.__name__+"."+t._testMethodName)
            for cls in testlist:
                print cls
                args = ['python', 'runtests.py'] + argv + [cls]
                p = subprocess.Popen(args, stdout = subprocess.PIPE, stderr= subprocess.PIPE)
                output, error = p.communicate()
                if p.returncode > 0:
                    print error,p.returncode
                    if failfast:
                        sys.exit(p.returncode)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--failfast', action='store_true', default=False,
                        dest='failfast')
    args = parser.parse_args()
    main(sys.argv[1:],failfast=args.failfast)


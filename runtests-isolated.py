#!/usr/bin/env python
from __future__ import with_statement
import pkgutil
import pyclbr
import subprocess
import argparse
import sys
import os.path
#from iterools import ifilter

def main(argv, failfast=False, test_labels=None):
    testlist = []
    for module in [name for _, name, _ in pkgutil.iter_modules([os.path.join("cms","tests")])]:
        clsmembers = pyclbr.readmodule("cms.tests.%s" % module)
        for clsname,cls in clsmembers.items():
            testlist.append(cls)

    for cls in testlist:
        for method, line in cls.methods.items():
            if not method.startswith('test_'):
                continue
            test = '%s.%s' % (cls.name, method)
            if not test_labels or filter(lambda x: test.find(x)>-1, test_labels):
                print "Running ",test,
                args = ['python', 'runtests.py'] + argv + [test]
                p = subprocess.Popen(args, stdout = subprocess.PIPE, stderr= subprocess.PIPE)
                output, error = p.communicate()
                if p.returncode > 0:
                    print error
                    if failfast:
                        sys.exit(p.returncode)
                else:
                    print

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--failfast', action='store_true', default=False,
                        dest='failfast')
    parser.add_argument('test_labels', nargs='*')
    args = parser.parse_args()
    main(sys.argv[2:],failfast=args.failfast,test_labels=args.test_labels)

#!/usr/bin/env python
from __future__ import with_statement
import pkgutil
import pyclbr
import subprocess
import argparse
import sys
import os.path

def main(argv, failfast=False):
    testlist = []
    for module in [name for _, name, _ in pkgutil.iter_modules([os.path.join("cms","tests")])]:
        clsmembers = pyclbr.readmodule("cms.tests.%s" % module)
        for clsname,cls in clsmembers.items():
            testlist.append(clsname)
            #mod =  __import__(cls.module, fromlist=[cls.name])
            #clsdef = getattr(mod,cls.name)
            #if issubclass(clsdef,TestCase):
            #    testlist.append(clsdef.__name__)
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


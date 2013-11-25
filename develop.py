#!/bin/env python
from __future__ import print_function
import multiprocessing
import pkgutil
import pyclbr
import subprocess
import os
import sys
import warnings

from docopt import docopt
from django import VERSION
from django.utils import autoreload

from cms import __version__
from cms.test_utils.cli import configure
from cms.test_utils.tmpdir import temp_dir

__doc__ = '''django CMS development helper script. 

To use a different database, set the DATABASE_URL environment variable to a
dj-database-url compatible value.

Usage:
    develop.py test [--parallel | --failfast] [--migrate] [<test-label>...]
    develop.py timed test [test-label...]
    develop.py isolated test [<test-label>...] [--parallel] [--migrate]
    develop.py server [--port=<port>] [--bind=<bind>] [--migrate]
    develop.py shell
    develop.py compilemessages
    develop.py makemessages

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --parallel                  Run tests in parallel.
    --migrate                   Use south migrations in test or server command.
    --failfast                  Stop tests on first failure (only if not --parallel).
    --port=<port>               Port to listen on [default: 8000].
    --bind=<bind>               Interface to bind to [default: 127.0.0.1].
'''


def server(bind='127.0.0.1', port=8000, migrate=False):
    if os.environ.get("RUN_MAIN") != "true":
        from south.management.commands import syncdb, migrate
        if migrate:
            syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default')
            migrate.Command().handle(interactive=False, verbosity=1)
        else:
            syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default', migrate=False, migrate_all=True)
            migrate.Command().handle(interactive=False, verbosity=1, fake=True)
        from django.contrib.auth.models import User
        if not User.objects.filter(is_superuser=True).exists():
            usr = User()
            usr.username = 'admin'
            usr.email = 'admin@admin.com'
            usr.set_password('admin')
            usr.is_superuser = True
            usr.is_staff = True
            usr.is_active = True
            usr.save()
            print('')
            print("A admin user (username: admin, password: admin) has been created.")
            print('')
    from django.contrib.staticfiles.management.commands import runserver
    rs = runserver.Command()
    rs.stdout = sys.stdout
    rs.stderr = sys.stderr
    rs.use_ipv6 = False
    rs._raw_ipv6 = False
    rs.addr = bind
    rs.port = port
    autoreload.main(rs.inner_run, (), {
        'addrport': '%s:%s' % (bind, port),
        'insecure_serving': True,
        'use_threading': True
    })

def _split(itr, num):
    split = []
    size = int(len(itr) / num)
    for index in range(num):
        split.append(itr[size * index:size * (index + 1)])
    return split

def _get_test_labels():
    test_labels = []
    for module in [name for _, name, _ in pkgutil.iter_modules([os.path.join("cms","tests")])]:
        clsmembers = pyclbr.readmodule("cms.tests.%s" % module)
        for clsname, cls in clsmembers.items():
            for method, _ in cls.methods.items():
                if method.startswith('test_'):
                    test_labels.append('cms.%s.%s' % (clsname, method))
    return test_labels

def _test_run_worker(test_labels, failfast=False, test_runner='django.test.simple.DjangoTestSuiteRunner'):
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')
    from django.conf import settings
    settings.TEST_RUNNER = test_runner
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    test_runner = TestRunner(verbosity=1, interactive=False, failfast=failfast)
    failures = test_runner.run_tests(test_labels)
    return failures

def _test_in_subprocess(test_labels):
    return subprocess.call(['python', 'develop.py', 'test'] + test_labels)

def isolated(test_labels, parallel=False):
    test_labels = test_labels or _get_test_labels()
    if parallel:
        pool = multiprocessing.Pool()
        mapper = pool.map
    else:
        mapper = map
    results = mapper(_test_in_subprocess, ([test_label] for test_label in test_labels))
    failures = [test_label for test_label, return_code in zip(test_labels, results) if return_code != 0]
    return failures

def timed(test_labels):
    return _test_run_worker(test_labels, test_runner='cms.test_utils.runners.TimedTestRunner')

def test(test_labels, parallel=False, failfast=False):
    test_labels = test_labels or _get_test_labels()
    if parallel:
        worker_tests = _split(test_labels, multiprocessing.cpu_count())

        pool = multiprocessing.Pool()
        failures = sum(pool.map(_test_run_worker, worker_tests))
        return failures
    else:
        return _test_run_worker(test_labels, failfast)

def compilemessages():
    from django.core.management import call_command
    os.chdir('cms')
    call_command('compilemessages', all=True)

def makemessages():
    from django.core.management import call_command
    os.chdir('cms')
    call_command('makemessages', all=True)

def shell():
    from django.core.management import call_command
    call_command('shell')

if __name__ == '__main__':
    args = docopt(__doc__, version=__version__)

    # configure django
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')

    default_name = ':memory:' if args['test'] else 'local.sqlite'

    db_url = os.environ.get("DATABASE_URL", "sqlite://localhost/%s" % default_name)
    migrate = args.get('--migrate', False)

    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            use_tz = VERSION[:2] >= (1, 4)
            configure(db_url=db_url,
                ROOT_URLCONF='cms.test_utils.project.urls',
                STATIC_ROOT=STATIC_ROOT,
                MEDIA_ROOT=MEDIA_ROOT,
                USE_TZ=use_tz,
                SOUTH_TESTS_MIGRATE=migrate
            )

            # run
            if args['test']:
                if args['isolated']:
                    failures = isolated(args['<test-label>'], args['--parallel'])
                    print()
                    print("Failed tests")
                    print("============")
                    if failures:
                        for failure in failures:
                            print(" - %s" % failure)
                    else:
                        print(" None")
                    num_failures = len(failures)
                elif args['timed']:
                    num_failures = timed(args['<test-label>'])
                else:
                    num_failures = test(args['<test-label>'], args['--parallel'], args['--failfast'])
                sys.exit(num_failures)
            elif args['server']:
                server(args['--bind'], args['--port'], migrate)
            elif args['shell']:
                shell()
            elif args['compilemessages']:
                compilemessages()
            elif args['makemessages']:
                compilemessages()

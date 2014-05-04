#!/usr/bin/env python
from __future__ import print_function, with_statement
import contextlib
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
from django.utils.encoding import force_text
from django.core.management import call_command

import cms
from cms.utils.compat import DJANGO_1_6
from cms.test_utils.cli import configure
from cms.test_utils.util import static_analysis
from cms.test_utils.tmpdir import temp_dir

__doc__ = '''django CMS development helper script. 

To use a different database, set the DATABASE_URL environment variable to a
dj-database-url compatible value.  The AUTH_USER_MODEL environment variable can be
used to change the user model in the same manner as the --user option.

Usage:
    develop.py test [--parallel | --failfast] [--migrate] [--user=<user>] [<test-label>...] [--xvfb]
    develop.py timed test [test-label...] [--xvfb]
    develop.py isolated test [<test-label>...] [--parallel] [--migrate] [--xvfb]
    develop.py server [--port=<port>] [--bind=<bind>] [--migrate] [--user=<user>]
    develop.py shell
    develop.py compilemessages
    develop.py makemessages
    develop.py pyflakes
    develop.py authors

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --parallel                  Run tests in parallel.
    --migrate                   Use south migrations in test or server command.
    --failfast                  Stop tests on first failure (only if not --parallel).
    --port=<port>               Port to listen on [default: 8000].
    --bind=<bind>               Interface to bind to [default: 127.0.0.1].
    --user=<user>               Specify which user model to run tests with (if other than auth.User).
    --xvfb                      Use a virtual X framebuffer for frontend testing, requires xvfbwrapper to be installed.
'''


def server(bind='127.0.0.1', port=8000, migrate_opt=False):
    if os.environ.get("RUN_MAIN") != "true":
        if DJANGO_1_6:
            from south.management.commands import syncdb, migrate
            if migrate_opt:
                syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default')
                migrate.Command().handle(interactive=False, verbosity=1)
            else:
                syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default', migrate=False, migrate_all=True)
                migrate.Command().handle(interactive=False, verbosity=1, fake=True)
        else:
            call_command("migrate", database='default')
        from cms.compat import get_user_model
        User = get_user_model()        
        if not User.objects.filter(is_superuser=True).exists():
            usr = User()

            if(User.USERNAME_FIELD != 'email'):
                setattr(usr, User.USERNAME_FIELD, 'admin')

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
    test_labels = sorted(test_labels)
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
    call_command('makemessages', locale=('en',))


def shell():
    from django.core.management import call_command
    call_command('shell')


def generate_authors():
    print("Generating AUTHORS")

    # Get our list of authors
    print("Collecting author names")
    r = subprocess.Popen(["git", "log", "--use-mailmap", "--format=%aN"], stdout=subprocess.PIPE)
    seen_authors = []
    authors = []
    with open('AUTHORS', 'r') as f:
        for line in f.readlines():
            if line.startswith("*"):
                author = force_text(line).strip("* \n")
                if author.lower() not in seen_authors:
                    seen_authors.append(author.lower())
                    authors.append(author)
    for author in r.stdout.readlines():
        author = force_text(author).strip()
        if author.lower() not in seen_authors:
            seen_authors.append(author.lower())
            authors.append(author)

    # Sort our list of Authors by their case insensitive name
    authors = sorted(authors, key=lambda x: x.lower())

    # Write our authors to the AUTHORS file
    print(u"Authors (%s):\n\n\n* %s" % (len(authors), u"\n* ".join(authors)))


def main():
    args = docopt(__doc__, version=cms.__version__)

    if args['pyflakes']:
        return static_analysis.pyflakes()
    
    if args['authors']:
        return generate_authors()

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

            configs = {
                'db_url': db_url,
                'ROOT_URLCONF': 'cms.test_utils.project.urls',
                'STATIC_ROOT': STATIC_ROOT,
                'MEDIA_ROOT': MEDIA_ROOT,
                'USE_TZ': use_tz,
                'SOUTH_TESTS_MIGRATE': migrate,
            }

            if args['test']:
                configs['SESSION_ENGINE'] = "django.contrib.sessions.backends.cache"

            # Command line option takes precedent over environment variable
            auth_user_model = args['--user']

            if not auth_user_model:
                auth_user_model = os.environ.get("AUTH_USER_MODEL", None)

            if auth_user_model:
                if VERSION[:2] < (1, 5):
                    print()
                    print("Custom user models are not supported before Django 1.5")
                    print()
                else:
                    configs['AUTH_USER_MODEL'] = auth_user_model

            configure(**configs)

            # run
            if args['test']:
                # make "Address already in use" errors less likely, see Django
                # docs for more details on this env variable.
                os.environ.setdefault(
                    'DJANGO_LIVE_TEST_SERVER_ADDRESS',
                    'localhost:8000-9000'
                )
                if args['--xvfb']:
                    import xvfbwrapper
                    context = xvfbwrapper.Xvfb(width=1280, height=720)
                else:
                    @contextlib.contextmanager
                    def null_context():
                        yield
                    context = null_context()

                with context:
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
                makemessages()


if __name__ == '__main__':
    main()

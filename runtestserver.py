#!/usr/bin/env python
from cms.test_utils.cli import configure
from cms.test_utils.tmpdir import temp_dir
import argparse
from django.utils import autoreload
import os
import sys
import urlparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='8000')
    parser.add_argument('-b', '--bind', default='127.0.0.1')
    args = parser.parse_args()
    new_db = not os.path.exists('cmstestdb.sqlite')
    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            configure("sqlite://cmstestdb.sqlite",
                ROOT_URLCONF='cms.test_utils.project.urls',
                STATIC_ROOT=STATIC_ROOT,
                MEDIA_ROOT=MEDIA_ROOT,
            )
            if os.environ.get("RUN_MAIN") != "true":
                from django.core.management import call_command
                call_command('syncdb', interactive=False, migrate_all=new_db)
                call_command('migrate', interactive=False, fake=new_db)
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
                    print
                    print "A admin user (username: admin, password: admin) has been created."
                    print
            from django.contrib.staticfiles.management.commands import runserver
            rs = runserver.Command()
            rs.stdout = sys.stdout
            rs.stderr = sys.stderr
            rs.use_ipv6 = False
            rs._raw_ipv6 = False
            rs.addr = args.bind
            rs.port = args.port
            autoreload.main(rs.inner_run, (), {'addrport':'%s:%s' % (args.bind, args.port), 'insecure_serving':True, 'use_threading':True})

if __name__ == '__main__':
    main()

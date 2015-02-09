# -*- coding: utf-8 -*-
from __future__ import absolute_import
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.encoding import force_text

from cms.api import publish_pages


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--unpublished',
            action='store_true',
            dest='include_unpublished',
            default=False,
            help='Include unpublished drafts',
        ),
        make_option(
            '-l', '--language',
            dest='language',
            help='Language code to publish',
        ),
        make_option(
            '-s', '--site',
            dest='site',
            help='Site id to publish',
        ),
    )

    def handle_noargs(self, **options):
        """Create published public version of selected drafts.
        """
        include_unpublished = options.get('include_unpublished')
        language = options.get('language')
        site = options.get('site')
        if site:
            try:
                site = int(site)
            except ValueError:
                site = None
        else:
            site = None

        pages_published = 0
        pages_total = 0
        try:
            self.stdout.write(u"\nPublishing public drafts....\n")
            nr = 0
            for page, add in publish_pages(include_unpublished, language, site):
                m = '*' if add else ' '
                self.stdout.write(u"%d.\t%s  %s [%d]\n" % (nr + 1, m, force_text(page), page.id))
                pages_total += 1
                if add:
                    pages_published += 1
                nr += 1
        except User.DoesNotExist:
            raise CommandError("No super user found, create one using `manage.py createsuperuser`.")

        self.stdout.write(u"\n")
        self.stdout.write(u"=" * 40)
        self.stdout.write(u"\nTotal:     %s\n" % pages_total)
        self.stdout.write(u"Published: %s\n" % pages_published)

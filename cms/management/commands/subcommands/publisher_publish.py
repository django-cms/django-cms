# -*- coding: utf-8 -*-
from __future__ import absolute_import
from optparse import make_option

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.encoding import force_text

from cms.api import publish_pages
from cms.utils.permissions import set_current_user


class PublishCommand(NoArgsCommand):
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
                site = Site.objects.get(pk=site)
            except (ValueError, Site.DoesNotExist):
                raise CommandError("There is no site with given site id.")
        else:
            site = None

        try:
            user = get_user_model().objects.filter(is_active=True, is_staff=True, is_superuser=True)[0]
        except IndexError:
            raise CommandError("No super user found, create one using `manage.py createsuperuser`.")

        set_current_user(user) # set him as current user

        pages_published = 0
        pages_total = 0
        self.stdout.write(u"\nPublishing public drafts....\n")
        index = 0
        for page, add in publish_pages(include_unpublished, language, site):
            m = '*' if add else ' '
            self.stdout.write(u"%d.\t%s  %s [%d]\n" % (index + 1, m, force_text(page), page.id))
            pages_total += 1
            if add:
                pages_published += 1
            index += 1

        self.stdout.write(u"\n")
        self.stdout.write(u"=" * 40)
        self.stdout.write(u"\nTotal:     %s\n" % pages_total)
        self.stdout.write(u"Published: %s\n" % pages_published)

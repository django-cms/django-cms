# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import CommandError
from django.utils.encoding import force_text

from cms.api import publish_pages
from cms.utils.permissions import set_current_user

from .base import SubcommandsCommand


class PublishCommand(SubcommandsCommand):
    help_string = 'Create published public version of selected drafts.'
    command_name = 'publisher-publish'

    def add_arguments(self, parser):
        parser.add_argument('--unpublished', action='store_true', dest='include_unpublished',
                            default=False, help='Include unpublished drafts')
        parser.add_argument('-l', '--language', dest='language', help='Language code to publish')
        parser.add_argument('--site', action='store', dest='site', help='Site ID to publish')

    def handle(self, *args, **options):
        """
        Create published public version of selected drafts.
        """
        include_unpublished = options.get('include_unpublished')
        language = options.get('language')
        site = self.get_site(options.get('site'))

        # we need a super user to assign the publish action to
        try:
            user = get_user_model().objects.filter(is_active=True, is_staff=True, is_superuser=True)[0]
        except IndexError:
            raise CommandError('No super user found, create one using `manage.py createsuperuser`.')
        # set him as current user
        set_current_user(user)

        pages_published = 0
        pages_total = 0
        self.stdout.write('\nPublishing public drafts....\n')
        index = 0
        for page, add in publish_pages(include_unpublished, language, site):
            m = '*' if add else ' '
            self.stdout.write('%d.\t%s  %s [%d]\n' % (index + 1, m, force_text(page), page.id))
            pages_total += 1
            if add:
                pages_published += 1
            index += 1

        self.stdout.write('\n')
        self.stdout.write('=' * 40)
        self.stdout.write('\nTotal:     %s\n' % pages_total)
        self.stdout.write('Published: %s\n' % pages_published)

    def get_site(self, site_id):
        if site_id:
            try:
                return Site.objects.get(pk=site_id)
            except (ValueError, Site.DoesNotExist):
                raise CommandError('There is no site with given site id.')
        else:
            return None

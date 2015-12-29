# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import CommandError
from django.db import transaction

from cms.models import Page


from .base import SubcommandsCommand


class CopySiteCommand(SubcommandsCommand):
    help_string = 'Copy the CMS pagetree from a specific SITE_ID.'
    command_name = 'copy-site'

    def add_arguments(self, parser):
        parser.add_argument('--from-site', action='store', dest='from_site', required=True,
                            help='Language to copy the content from.')
        parser.add_argument('--to-site', action='store', dest='to_site', required=True,
                            help='Language to copy the content to.')

    def handle(self, *args, **options):
        try:
            from_site = int(options.get('from_site', None))
        except Exception:
            from_site = settings.SITE_ID
        try:
            to_site = int(options.get('to_site', None))
        except Exception:
            to_site = settings.SITE_ID
        try:
            assert from_site != to_site
        except AssertionError:
            raise CommandError('Sites must be different')

        from_site = self.get_site(from_site)
        to_site = self.get_site(to_site)

        pages = Page.objects.drafts().filter(site=from_site, depth=1)

        with transaction.atomic():
            for page in pages:
                page.copy_page(None, to_site)
            self.stdout.write('Copied CMS Tree from SITE_ID {0} successfully to SITE_ID {1}.\n'.format(from_site.pk, to_site.pk))

    def get_site(self, site_id):
        if site_id:
            try:
                return Site.objects.get(pk=site_id)
            except (ValueError, Site.DoesNotExist):
                raise CommandError('There is no site with given site id.')
        else:
            return None

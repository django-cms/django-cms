# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.db import transaction

from cms.models import Page


class CopySiteCommand(BaseCommand):
    help = 'Copy the CMS pagetree from a specific SITE_ID.'
    args = '<site_from site_to>'

    def handle(self, *args, **options):
        try:
            assert len(args) >= 2

            from_site_id = int(args[0])
            to_site_id = int(args[1])

            assert from_site_id != to_site_id
        except AssertionError:
            raise CommandError("Error: bad arguments -- Usage: manage.py cms copy-site <site_from> <site_to>")

        to_site = self.get_site(to_site_id)

        pages = Page.objects.drafts().filter(site=from_site_id, depth=1)

        with transaction.atomic():
            for page in pages:
                page.copy_page(None, to_site)
            self.stdout.write("Copied CMS Tree from SITE_ID {0} successfully to SITE_ID {1}.\n".format(from_site_id, to_site_id))

    def get_site(self, site_id):
        try:
            return Site.objects.get(pk=site_id)
        except Site.DoesNotExist:
            raise CommandError("\nUnknown site: {0}. Please create a new site first.\n".format(site_id))

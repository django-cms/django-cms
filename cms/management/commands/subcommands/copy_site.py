from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.db import transaction

from cms.models import Page


class CopySiteCommand(BaseCommand):
    help = 'Copy the CMS pagetree from a specific SITE_ID.'
    option_list = BaseCommand.option_list + (
        make_option('--from', dest='from_site', default=None,
            help='Specifies the SITE_ID to copy from.'),
        make_option('--to', dest='to_site', default=None,
            help='Specifies the SITE_ID to copy to.')
    )

    def handle(self, *args, **options):
        from_site_id = options.get('from_site', None)
        to_site_id = options.get('to_site', None)

        if not from_site_id or not to_site_id:
            raise CommandError("You must use --from and --to to use this command.")

        from_site = self.get_site(from_site_id)
        to_site = self.get_site(to_site_id)

        pages = Page.objects.drafts().filter(site=from_site_id, depth=1)

        with transaction.atomic():
            for page in pages:
                page.copy_page(page, to_site)
            self.stdout.write("Copied CMS Tree from SITE_ID {0} successfully to SITE_ID {1}.\n".format(from_site_id, to_site_id))

    def get_site(self, site_id):
        try:
            return Site.objects.get(pk=site_id)
        except Site.DoesNotExist:
            raise CommandError("\nUnknown site: {0}. Please create a new site first.\n".format(site_id))

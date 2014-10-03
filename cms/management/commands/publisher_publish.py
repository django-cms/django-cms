# -*- coding: utf-8 -*-
from __future__ import absolute_import
from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.translation import activate
from cms.utils.compat.dj import force_unicode

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

        self.publish_pages(include_unpublished, language, site)

    def publish_pages(self, include_unpublished, language, site):
        from cms.models import Page
        from cms.utils.compat.dj import get_user_model
        from cms.utils.permissions import set_current_user

        # thread locals middleware needs to know, who are we - login as a first
        # super user

        try:
            user = get_user_model().objects.filter(is_active=True, is_staff=True, is_superuser=True)[0]
        except IndexError:
            raise CommandError("No super user found, create one using `manage.py createsuperuser`.")

        set_current_user(user) # set him as current user

        qs = Page.objects.drafts()
        if not include_unpublished:
            qs = qs.filter(title_set__published=True).distinct()
        if site:
            qs = qs.filter(site_id=site)

        pages_total, pages_published = qs.count(), 0

        self.stdout.write(u"\nPublishing public drafts....\n")
        output_language = None
        for i, page in enumerate(qs):
            m = " "
            add = True
            titles = page.title_set
            if not include_unpublished:
                titles = titles.filter(published=True)
            for lang in titles.values_list("language", flat=True):
                if language is None or lang == language:
                    if not output_language:
                        output_language = lang
                    if not page.publish(lang):
                        add = False
            # we may need to activate the first (main) language for proper page title rendering
            activate(output_language)
            if add:
                pages_published += 1
                m = "*"
            self.stdout.write(u"%d.\t%s  %s [%d]\n" % (i + 1, m, force_unicode(page), page.id))

        self.stdout.write(u"\n")
        self.stdout.write(u"=" * 40)
        self.stdout.write(u"\nTotal:     %s\n" % pages_total)
        self.stdout.write(u"Published: %s\n" % pages_published)

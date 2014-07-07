# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.core.management.base import NoArgsCommand, CommandError
from django.utils.translation import activate
from cms.utils.compat.dj import force_unicode

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        """Create published public version of all published drafts.
        """
        self.publish_pages()
        
    def publish_pages(self):
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

        qs = Page.objects.drafts().filter(title_set__published=True)
        pages_total, pages_published = qs.count(), 0
        
        print(u"\nPublishing public drafts....\n")
        output_language = None
        for i, page in enumerate(qs):
            m = " "
            add = True
            for lang in page.title_set.filter(published=True).values_list("language", flat=True):
                if not output_language:
                    output_language = lang
                if not page.publish(lang):
                    add = False
            # we may need to activate the first (main) language for proper page title rendering
            activate(output_language)
            if add:
                pages_published += 1
                m = "*"
            print(u"%d.\t%s  %s [%d]" % (i + 1, m, force_unicode(page), page.id))
        
        print(u"\n")
        print(u"=" * 40)
        print(u"Total:     %s" % pages_total)
        print(u"Published: %s" % pages_published)
        

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        """Create published public version of all published drafts. Useful, 
        when CMS_MODERATOR gets turned on after some time. 
        """
        if not getattr(settings, 'CMS_MODERATOR', False):
            raise CommandError("This command may be used only with settings.CMS_MODERATOR") 
        
        self.publish_pages()
        
    def publish_pages(self):
        from django.contrib.auth.models import User
        from cms.models import Page
        from cms.utils.permissions import set_current_user
        
        # thread locals middleware needs to know, who are we - login as a first
        # super user
        
        try:
            user = User.objects.filter(is_active=True, is_staff=True, is_superuser=True)[0]
        except IndexError:
            raise CommandError("No super user found, create one using `manage.py createsuperuser`.")
        
        set_current_user(user) # set him as current user
        
        qs = Page.objects.drafts().filter(published=True)
        pages_total, pages_published = qs.count(), 0
        
        print "\nPublishing public drafts....\n"
        
        for i, page in enumerate(qs):
            m = " "
            if page.publish():
                pages_published += 1
                m = "*"
            print "%d.\t%s  %s [%d]" % (i + 1, m, unicode(page), page.id) 
        
        print "\n"
        print "=" * 40
        print "Total:    ", pages_total
        print "Published:", pages_published
        

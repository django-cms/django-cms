from django.db import models
from django.contrib.sites.models import Site
from django.db.models import Q
from datetime import datetime

from cms import settings

class PageManager(models.Manager):
    def on_site(self, site=None):
        if hasattr(site, 'domain'):
            return self.filter(**{'sites__domain__exact': site.domain})
        return self

    def root(self, site=None):
        """
        Return a queryset with pages that don't have parents, a.k.a. root.
        """
        return self.on_site(site).filter(parent__isnull=True)

    def valid_targets(self, page_id, request, perms, page=None):
        """
        Give valid targets to move a page into the tree
        """
        if page is None:
            page = self.get(pk=page_id)
        exclude_list = []
        if page:
            exclude_list.append(page.id)
            for p in page.get_descendants():
                exclude_list.append(p.id)
        if perms != "All":
            return self.filter(id__in=perms).exclude(id__in=exclude_list)
        else:
            return self.exclude(id__in=exclude_list)

    def published(self, site=None):
        pub = self.on_site(site).filter(status=self.model.PUBLISHED)

        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__lte=datetime.now())

        if settings.CMS_SHOW_END_DATE:
            pub = pub.filter(
                Q(publication_end_date__gt=datetime.now()) |
                Q(publication_end_date__isnull=True)
            )
        return pub

    def drafts(self, site=None):
        pub = self.on_site(site).filter(status=self.model.DRAFT)
        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__gte=datetime.now())
        return pub

    def expired(self, site=None):
        return self.on_site(site).filter(
            publication_end_date__lte=datetime.now())
        
        
class TitleManager(models.Manager):
    def get_title(self, page, language, language_fallback=False, latest_by='creation_date'):
        """
        Gets the latest content for a particular page and language. Falls back
        to another language if wanted.
        """
        try:
            title = self.get(language=language, page=page)
            return title
        except self.model.DoesNotExist:
            pass
        if language_fallback:
            try:
                title = self.filter(page=page).latest(latest_by)
                return title
            except self.model.DoesNotExist:
                pass
        return None        
    
    def get_page_slug(self, slug, site=None, latest_by='creation_date'):
        """
        Returns the latest slug for the given slug and checks if it's available 
        on the current site.
        """
        if not site:
            site = Site.objects.get_current()
        try:
            titles = self.filter(
                slug=slug,
                page__sites__domain=site.domain,
            ).select_related()#'page')
        except self.model.DoesNotExist:
            return None
        else:
            return titles
        
    def set_or_create(self, page, language, slug=None, title=None):
        """
        set or create a title for a particular page and language
        """
        if settings.CMS_SANITIZE_USER_INPUT and title != None:
            title = self.sanitize(title)
        try:
            obj = self.filter(page=page, language=language).latest('creation_date')
            if title != None:
                obj.title = title
            if slug != None:
                obj.slug = slug
        except self.model.DoesNotExist:
            obj = self.model(page=page, language=language, title=title, slug=slug)
        obj.save()
        return obj

class ContentManager(models.Manager):

    def sanitize(self, content):
        """
        Sanitize the content to avoid XSS and so
        """
        import html5lib
        from html5lib import sanitizer
        p = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
        # we need to remove <html><head/><body>...</body></html>
        return p.parse(content).toxml()[19:-14]

    def set_or_create_content(self, page, language, cnttype, body):
        """
        set or create a content for a particular page and language
        """
        if settings.CMS_SANITIZE_USER_INPUT:
            body = self.sanitize(body)
        try:
            content = self.filter(page=page, language=language,
                                  type=cnttype).latest('creation_date')
            content.body = body
        except self.model.DoesNotExist:
            content = self.model(page=page, language=language, body=body,
                                 type=cnttype)
        content.save()
        return content


    # TODO: probably not used anymore after django-revision integration
    def create_content_if_changed(self, page, language, cnttype, body):
        """
        set or create a content for a particular page and language
        """
        if settings.CMS_SANITIZE_USER_INPUT:
            body = self.sanitize(body)
        try:
            content = self.filter(page=page, language=language,
                                  type=cnttype).latest('creation_date')
            if content.body == body:
                return content
        except self.model.DoesNotExist:
            pass
        content = self.create(page=page, language=language, body=body, type=cnttype)

    def get_content(self, page, language, cnttype, language_fallback=False,
            latest_by='creation_date'):
        """
        Gets the latest content for a particular page and language. Falls back
        to another language if wanted.
        """
        try:
            content = self.filter(language=language, page=page,
                                        type=cnttype).latest(latest_by)
            return content.body
        except self.model.DoesNotExist:
            pass
        if language_fallback:
            try:
                content = self.filter(page=page, type=cnttype).latest(latest_by)
                return content.body
            except self.model.DoesNotExist:
                pass
        return None

    

class PagePermissionManager(models.Manager):
    
    def get_page_id_list(self, user):
        """
        Give a list of page where the user has rights or the string "All" if
        the user has all rights.
        """
        if user.is_superuser:
            return 'All'
        id_list = []
        for perm in self.filter(user=user):
            if perm.type == 0:
                return "All"
            if perm.page.id not in id_list:
                id_list.append(perm.page.id)
            if perm.type == 2:
                for page in perm.page.get_descendants():
                    if page.id not in id_list:
                        id_list.append(page.id)
        return id_list

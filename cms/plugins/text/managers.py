from django.db import models
from cms import settings

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

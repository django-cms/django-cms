from cms.signals import post_publish
from cms.utils.compat.metaclasses import with_metaclass
from django.dispatch import receiver
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import Page


class BasePageExtension(models.base.ModelBase):

    def __new__(cls, *args, **kwargs):
        new_class = super(BasePageExtension, cls).__new__(cls, *args, **kwargs)

        if not getattr(new_class._meta, 'abstract', False):
            page_meta = Page._meta
            if hasattr(page_meta, 'extensions'):
                page_meta.extensions.append(new_class)
            else:
                page_meta.extensions = [new_class]

        return new_class


class PageExtension(with_metaclass(BasePageExtension, models.Model)):
    extended_page = models.OneToOneField(Page, verbose_name=_('Page'), limit_choices_to={'publisher_is_draft': True})

    class Meta:
        abstract = True

    def copy_to_public(self, page):
        cls = type(self)

        try:
            extension = cls.objects.get(extended_page=page)
        except cls.DoesNotExist:
            extension = None
        except cls.MultipleObjectsReturned:
            cls.objects.filter(extended_page=page).delete()
            extension = None

        if extension:
            self.pk = extension.pk
            self.extended_page = page
            self.save()
        else:
            self.pk = None
            self.extended_page = page
            self.save()

    def save(self, *args, **kwargs):
        self.extended_page.save(no_signals=True)  # mark page unpublished
        return super(PageExtension, self).save(*args, **kwargs)


@receiver(post_publish)
def copy_page_extensions(sender, **kwargs):
    draft_page = kwargs.get('instance')
    public_page = draft_page.publisher_public
    for extension in getattr(Page._meta, 'extensions', []):
        for instance in extension.objects.filter(extended_page=draft_page):
            instance.copy_to_public(public_page)

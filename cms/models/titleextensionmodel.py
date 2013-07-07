from cms.signals import post_publish
from cms.utils.compat.metaclasses import with_metaclass
from django.dispatch import receiver
from django.db import models

from . import Title


class BaseTitleExtension(models.base.ModelBase):

    def __new__(cls, *args, **kwargs):
        new_class = super(BaseTitleExtension, cls).__new__(cls, *args, **kwargs)

        if not getattr(new_class._meta, 'abstract', False):
            title_meta = Title._meta
            if hasattr(title_meta, 'extensions'):
                title_meta.extensions.append(new_class)
            else:
                title_meta.extensions = [new_class]

        return new_class


class TitleExtension(with_metaclass(BaseTitleExtension, models.Model)):
    extended_title = models.OneToOneField(Title, limit_choices_to={'page__publisher_is_draft': True})

    class Meta:
        abstract = True

    def copy_to_public(self, title):
        cls = type(self)

        try:
            extension = cls.objects.get(extended_title=title)
        except cls.DoesNotExist:
            extension = None
        except cls.MultipleObjectsReturned:
            cls.objects.filter(extended_title=title).delete()
            extension = None

        if extension:
            self.pk = extension.pk
            self.extended_title = title
            self.save()
        else:
            self.pk = None
            self.extended_title = title
            self.save()

    def save(self, *args, **kwargs):
        self.extended_title.page.save(no_signals=True)  # mark page unpublished
        return super(TitleExtension, self).save(*args, **kwargs)


@receiver(post_publish)
def copy_title_extensions(sender, **kwargs):
    draft_page = kwargs.get('instance')
    public_page = draft_page.publisher_public
    extensions = getattr(Title._meta, 'extensions', [])
    if extensions:
        for draft_title in draft_page.title_set.all():
            public_title = Title.objects.get(language=draft_title.language, page=public_page)
            for extension in extensions:
                for instance in extension.objects.filter(extended_title=draft_title):
                    instance.copy_to_public(public_title)




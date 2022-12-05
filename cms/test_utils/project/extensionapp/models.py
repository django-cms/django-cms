from django.conf import settings
from django.db import models

from cms.extensions import PageContentExtension, PageExtension
from cms.extensions.extension_pool import extension_pool


class MyPageExtension(PageExtension):
    extra = models.CharField(blank=True, default='', max_length=255)
    favorite_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def copy_relations(self, other, language):
        for favorite_user in other.favorite_users.all():
            favorite_user.pk = None
            favorite_user.mypageextension = self
            favorite_user.save()


extension_pool.register(MyPageExtension)


# extension_pool.register can be used also as a decorator
@extension_pool.register
class MyPageContentExtension(PageContentExtension):
    extra_title = models.CharField(blank=True, default='', max_length=255)


class MultiTablePageExtensionParent(models.Model):
    extension_parent_field = models.CharField(blank=True, default='', max_length=255)


class MultiTablePageExtension(MultiTablePageExtensionParent, PageExtension):
    multitable_extra = models.CharField(blank=True, default='', max_length=255)


extension_pool.register(MultiTablePageExtension)


class MultiTableContentExtensionParent(models.Model):
    extension_content_parent_field = models.CharField(blank=True, default='', max_length=255)


class MultiTablePageContentExtension(MultiTableContentExtensionParent, PageContentExtension):
    multitable_extra_content = models.CharField(blank=True, default='', max_length=255)


extension_pool.register(MultiTablePageContentExtension)

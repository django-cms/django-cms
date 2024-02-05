from django.db import models
from django.db.models import ManyToManyField

from cms.models import Page, PageContent


class BaseExtension(models.Model):
    public_extension = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        null=True,
        editable=False,
        related_name='draft_extension',
    )
    extended_object = None

    class Meta:
        abstract = True

    def get_page(self):  # pragma: no cover
        raise NotImplementedError('Function must be overwritten in subclasses and return the extended page object.')

    def copy_relations(self, oldinstance, language):
        """
        Copy relations like many to many or foreign key relations to the public version.
        Similar to the same named cms plugin function.

        :param oldinstance: the draft version of the extension
        """
        pass

    @classmethod
    def _get_related_objects(cls):
        fields = cls._meta._get_fields(
            forward=False, reverse=True,
            include_parents=True,
            include_hidden=False,
        )
        return list(obj for obj in fields if not isinstance(obj.field, ManyToManyField))

    def copy(self, target, language):
        """
        This method copies this extension to an unrelated-target.
        """
        clone = self.__class__.objects.get(pk=self.pk)  # get a copy of this instance
        clone.pk = None
        clone.public_extension = None
        clone.extended_object = target  # set the new public object

        # Nullify all concrete parent primary keys. See issue #5494
        for parent, field in clone._meta.parents.items():
            if field:
                setattr(clone, parent._meta.pk.attname, None)

        clone.save()
        clone.copy_relations(self, language)
        return clone

    def copy_to_public(self, public_object, language):
        """
        .. warning::

            This method used to "publish" this extension as part of the a larger operation on the target.
            Publishing pages has been removed from django CMS core in version 4 onward.

            For publishing functionality see `djangocms-versioning: <https://github.com/django-cms/djangocms-versioning>`_
        """
        import warnings
        warnings.warn('This API function has been removed. For publishing functionality use a package that adds '
                      'publishing, such as: djangocms-versioning.',
                      UserWarning, stacklevel=2)


class PageExtension(BaseExtension):
    extended_object = models.OneToOneField(Page, on_delete=models.CASCADE, editable=False)

    class Meta:
        abstract = True

    def get_page(self):
        return self.extended_object


class PageContentExtension(BaseExtension):
    extended_object = models.OneToOneField(PageContent, on_delete=models.CASCADE, editable=False)

    class Meta:
        abstract = True

    def get_page(self):
        return self.extended_object.page

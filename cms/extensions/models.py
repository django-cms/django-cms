from django.db.models import ManyToManyField

from cms.constants import PUBLISHER_STATE_DIRTY
from django.db import models

from cms.models import Page, Title


class BaseExtension(models.Model):
    public_extension = models.OneToOneField('self', null=True, editable=False, related_name='draft_extension')
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
        This method copies this extension to an unrelated-target. If you intend
        to "publish" this extension to the publisher counterpart of target, then
        use copy_to_publish() instead.
        """
        clone = self.__class__.objects.get(pk=self.pk)  # get a copy of this instance
        clone.pk = None
        clone.public_extension = None
        clone.extended_object = target  # set the new public object

        # Nullify all concrete parent primary keys. See issue #5494
        for parent, field in clone._meta.parents.items():
            if field:
                setattr(clone, parent._meta.pk.attname, None)

        clone.save(mark_page=False)

        # If the target we're copying already has a publisher counterpart, then
        # connect the dots.
        target_prime = getattr(target, 'publisher_public')
        if target_prime:
            related_name = self.__class__.__name__.lower()
            clone_prime = getattr(target_prime, related_name)
            if clone_prime:
                clone.public_extension = clone_prime
            else:
                clone.public_extension = None

        clone.copy_relations(self, language)
        clone.save(force_update=True, mark_page=False)
        return clone

    def copy_to_public(self, public_object, language):
        """
        This method is used to "publish" this extension as part of the a larger
        operation on the target. If you intend to copy this extension to an
        unrelated object, use copy() instead.
        """
        this = self.__class__.objects.get(pk=self.pk)  # get a copy of this instance
        public_extension = self.public_extension  # get the public version of this instance if any

        this.extended_object = public_object  # set the new public object

        if public_extension:
            this.pk = public_extension.pk  # overwrite current public extension
            this.public_extension = None  # remove public extension or it will point to itself and raise duplicate entry

            # Set public_extension concrete parents PKs. See issue #5494
            for parent, field in this._meta.parents.items():
                if field:
                    setattr(this, parent._meta.pk.attname, getattr(public_extension, parent._meta.pk.attname))
        else:
            this.pk = None  # create new public extension

            # Nullify all concrete parent primary keys. See issue #5494
            for parent, field in this._meta.parents.items():
                if field:
                    setattr(this, parent._meta.pk.attname, None)

            this.save(mark_page=False)
            self.public_extension = this
            self.save(mark_page=False)

        this.copy_relations(self, language)
        this.save(force_update=True, mark_page=False)

        return this


class PageExtension(BaseExtension):
    extended_object = models.OneToOneField(Page, editable=False)

    class Meta:
        abstract = True

    def get_page(self):
        return self.extended_object

    def save(self, *args, **kwargs):
        if kwargs.pop('mark_page', True):
            self.get_page().title_set.update(publisher_state=PUBLISHER_STATE_DIRTY)  # mark page dirty
        return super(BaseExtension, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if kwargs.pop('mark_page', True):
            self.get_page().title_set.update(publisher_state=PUBLISHER_STATE_DIRTY)  # mark page dirty
        return super(BaseExtension, self).delete(*args, **kwargs)


class TitleExtension(BaseExtension):
    extended_object = models.OneToOneField(Title, editable=False)

    class Meta:
        abstract = True

    def get_page(self):
        return self.extended_object.page

    def save(self, *args, **kwargs):
        if kwargs.pop('mark_page', True):
            Title.objects.filter(pk=self.extended_object.pk).update(
                publisher_state=PUBLISHER_STATE_DIRTY) # mark title dirty
        return super(BaseExtension, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if kwargs.pop('mark_page', True):
            Title.objects.filter(pk=self.extended_object.pk).update(
                publisher_state=PUBLISHER_STATE_DIRTY) # mark title dirty
        return super(BaseExtension, self).delete(*args, **kwargs)

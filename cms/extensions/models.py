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

    def copy_to_public(self, public_object, language):
        this = self.__class__.objects.get(pk=self.pk)  # get a copy of this instance
        public_extension = self.public_extension  # get the public version of this instance if any

        this.extended_object = public_object  # set the new public object

        if public_extension:
            this.pk = public_extension.pk  # overwrite current public extension
            this.public_extension = None  # remove public extension or it will point to itself and raise duplicate entry
        else:
            this.pk = None  # create new public extension
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




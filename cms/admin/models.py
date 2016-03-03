# -*- coding: utf-8 -*-
from django.forms.models import BaseInlineFormSet

class BaseInlineFormSetWithQuerySet(BaseInlineFormSet):
    """Overriden BaseInlineFormSet, so we can pass queryset to it instead of
    _default_manager, see django bug #11019 for more details.
    """
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None):
        from django.db.models.fields.related import RelatedObject
        if instance is None:
            self.instance = self.model()
        else:
            self.instance = instance
        self.save_as_new = save_as_new
        # is there a better way to get the object descriptor?
        self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
        if hasattr(self, 'use_queryset'):
            qs = self.use_queryset 
        else:
            qs = self.model._default_manager
        qs = qs.filter(**{self.fk.name: self.instance})
        super(BaseInlineFormSet, self).__init__(data, files, prefix=prefix or self.rel_name,
                                                queryset=qs)
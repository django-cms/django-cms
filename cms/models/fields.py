from django.db import models
from cms.models.pagemodel import Page
from cms.forms.fields import PageSelectFormField

class PageField(models.ForeignKey):
    default_form_class = PageSelectFormField
    default_model_class = Page
    def __init__(self, **kwargs):
        # we call ForeignKey.__init__ with the Page model as parameter...
        # a PageField can only be a ForeignKey to a Page
        super(PageField, self).__init__(self.default_model_class, **kwargs)
    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.default_form_class,
        }
        defaults.update(kwargs)
        return super(PageField, self).formfield(**defaults)
    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.related.ForeignKey"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
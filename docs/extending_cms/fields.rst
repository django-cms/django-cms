#####################
Form and model fields
#####################


************
Model fields
************


.. py:class:: cms.models.fields.PageField

    This is a foreign key field to the :class:`cms.models.pagemodel.Page` model
    that defaults to the :class:`cms.forms.fields.PageSelectFormField` form
    field when rendered in forms. It has the same API as the
    :class:`django.db.models.fields.related.ForeignKey` but does not require
    the ``othermodel`` argument.


***********
Form fields
***********


.. py:class:: cms.forms.fields.PageSelectFormField

    Behaves like a :class:`django.forms.models.ModelChoiceField` field for the
    :class:`cms.models.pagemodel.Page` model, but displays itself as a split
    field with a select dropdown for the site and one for the page. It also
    indents the page names based on what level they're on, so that the page
    select dropdown is easier to use. This takes the same arguments as 
    :class:`django.forms.models.ModelChoiceField`.

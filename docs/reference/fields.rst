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
    field with a select drop-down for the site and one for the page. It also
    indents the page names based on what level they're on, so that the page
    select drop-down is easier to use. This takes the same arguments as
    :class:`django.forms.models.ModelChoiceField`.

.. py:class:: cms.forms.fields.PageSmartLinkField

    A field making use of :class:`cms.forms.widgets.PageSmartLinkWidget`.
    This field will offer you a list of matching internal pages as you type.
    You can either pick one or enter an arbitrary URL to create a non existing entry.
    Takes a `placeholder_text` argument to define the text displayed inside the
    input before you type.
    The widget uses an ajax request to try to find pages match. It will try to find
    case insensitive matches amongst public and published pages on the `title`, `path`,
    `page_title`, `menu_title` fields.
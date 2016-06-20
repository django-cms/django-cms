..  module:: cms.models

######
Models
######

..  class:: Page

    A ``Page`` is the basic unit of site structure in django CMS. The CMS uses a hierachical page model: each page
    stands in relation to other pages as parent, child or sibling.


..  class:: Title


..  class:: Placeholder

    ``Placeholders`` can be filled with plugins, which store or generate content.


..  class:: CMSPlugin

    See also: :ref:`storing configuration`

    **Attributes**

    ..  attribute:: translatable_content_excluded_fields

    Default: ``[ ]``

    A list of plugin fields which will not be exported while using :meth:`get_translatable_content`.

    See also: :meth:`get_translatable_content`, :meth:`set_translatable_content`.

    **Methods**

    ..  method:: copy_relations()

        Handle copying of any relations attached to this plugin. Custom plugins have
        to do this themselves.

        ``copy_relations`` takes 1 argument:

        * ``old_instance``: The source plugin instance

        See also: :ref:`Handling-Relations`, :meth:`post_copy`.

    ..  method:: get_translatable_content()

        Get a dictionary of all content fields (field name / field value pairs) from
        the plugin.

        Example::

            from djangocms_text_ckeditor.models import Text

            plugin = Text.objects.get(pk=1).get_plugin_instance()[0]
            plugin.get_translatable_content()
            # returns {'body': u'<p>I am text!</p>\n'}

        See also: :attr:`translatable_content_excluded_fields`, :attr:`set_translatable_content`.


    ..  method:: post_copy()

        Can (should) be overridden to handle the copying of plugins which contain
        children plugins after the original parent has been copied.

        ``post_copy`` takes 2 arguments:

        * ``old_instance``: The old plugin instance instance
        * ``new_old_ziplist``: A list of tuples containing new copies and the old existing child plugins.

        See also: :ref:`Handling-Relations`, :meth:`copy_relations`.


    ..  method:: set_translatable_content()

        Takes a dictionary of plugin fields (field name / field value pairs) and
        overwrites the plugin's fields. Returns ``True`` if all fields have been
        written successfully, and ``False`` otherwise.

        ``set_translatable_content`` takes 1 argument:

        * ``fields``: A dictionary containing the field names and translated content for each.

        * :meth:`get_translatable_content()`

        Example::

            from djangocms_text_ckeditor.models import Text

            plugin = Text.objects.get(pk=1).get_plugin_instance()[0]
            plugin.set_translatable_content({'body': u'<p>This is a different text!</p>\n'})
            # returns True

        See also: :attr:`translatable_content_excluded_fields`, :meth:`get_translatable_content`.


    ..  method:: get_add_url()

        Returns the URL to call to add a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_edit_url()

        Returns the URL to call to edit a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_move_url()

        Returns the URL to call to move a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_delete_url()

        Returns the URL to call to delete a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_copy_url()

        Returns the URL to call to copy a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: add_url()

        Returns the URL to call to add a plugin instance; useful to implement plugin-specific
        logic in a custom view.

        This property is now deprecated. Will be removed in 3.4.
        Use the ``get_add_url`` method instead.

        Default: None (``cms_page_add_plugin`` view is used)


    ..  method:: edit_url()

        Returns the URL to call to edit a plugin instance; useful to implement plugin-specific
        logic in a custom view.

        This property is now deprecated. Will be removed in 3.4.
        Use the ``get_edit_url`` method instead.

        Default: None (``cms_page_edit_plugin`` view is used)


    ..  method:: move_url()

        Returns the URL to call to move a plugin instance; useful to implement plugin-specific
        logic in a custom view.

        This property is now deprecated. Will be removed in 3.4.
        Use the ``get_move_url`` method instead.

        Default: None (``cms_page_move_plugin`` view is used)


    ..  method:: delete_url()

        Returns the URL to call to delete a plugin instance; useful to implement plugin-specific
        logic in a custom view.

        This property is now deprecated. Will be removed in 3.4.
        Use the ``get_delete_url`` method instead.

        Default: None (``cms_page_delete_plugin`` view is used)


    ..  method:: copy_url()

        Returns the URL to call to copy a plugin instance; useful to implement plugin-specific
        logic in a custom view.

        This property is now deprecated. Will be removed in 3.4.
        Use the ``get_copy_url`` method instead.

        Default: None (``cms_page_copy_plugins`` view is used)


..  module:: cms.models.fields

************
Model fields
************


.. py:class:: PageField

    This is a foreign key field to the :class:`cms.models.Page` model
    that defaults to the :class:`cms.forms.fields.PageSelectFormField` form
    field when rendered in forms. It has the same API as the
    :class:`django:django.db.models.ForeignKey` but does not require
    the ``othermodel`` argument.


.. py:class:: PlaceholderField

    A foreign key field to the :class:`cms.models.Placeholder` model.



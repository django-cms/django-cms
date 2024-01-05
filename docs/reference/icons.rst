Icons reusable for plugins
==========================

django CMS comes with a set of icons stored in its own icon font. The icons are based on
FontAwesome4 and Bootstrap Icons.

They are available in the frontend editor (i.e. if the toolbar is available). To use
them on the admin site where all the plugin editing etc. happens, you will have to load
them explicitly.

.. code-block:: python

    from cms.utils.urlutils import static_with_version


    class MyAdmin(admin.Admin):
        class Media:
            css = {"all": (static_with_version("cms/cms.icons.css"),)}

        ...

Icons are used by adding snippets like this to your templates

.. code-block:: html

    <span class="cms-icon cms-icon-<iconname>"></span>

The following icons are available:

- advanced-settings
- alias
- apphook
- archive
- bin
- comment
- compare
- copy
- cut
- edit
- edit-new
- highlight
- home
- info
- lock
- manage-versions
- moderate
- paste
- plugins
- publish
- redo
- rename
- search
- settings
- sitemap
- undo
- unlock
- unpublish
- view

Example:

.. code-block:: html

    <span class="cms-icon cms-icon-edit-new me-2"></span>{% translate "Edit new..." %}

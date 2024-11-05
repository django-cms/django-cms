How to extend Page & PageContent models
=======================================

You can extend the :class:`cms.models.pagemodel.Page` and
:class:`cms.models.contentmodels.PageContent` models with your own fields (e.g. adding
an icon for every page) by using the extension models: ``cms.extensions.PageExtension``
and ``cms.extensions.PageContentExtension``, respectively.

.. note::

    .. versionchanged:: 4.1

        In django CMS the ``PageContent`` model used to be called ``Title``. Since
        django CMS 4.1 a ``TitleExtension`` has become ``PageContentExtension``

PageContent vs Page extensions
------------------------------

The difference between a **page extension** and a **page content extension** is related
to the difference between the :class:`cms.models.pagemodel.Page` and
:class:`cms.models.contentmodels.PageContent` models.

- ``PageExtension``: use to add fields that should have **the same values** for the
  different language versions of a page - for example, an icon.
- ``PageContentExtension``: use to add fields that should have **language-specific
  values** for different language versions of a page - for example, keywords.

Implement a basic extension
---------------------------

Three basic steps are required:

- add the extension *model*
- add the extension *admin*
- add a toolbar menu item for the extension

Page model extension example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The model
+++++++++

To add a field to the Page model, create a class that inherits from
``cms.extensions.PageExtension``. Your class should live in one of your applications'
``models.py`` (or module).

.. note::

    Since ``PageExtension`` (and ``PageContentExtension``) inherit from
    ``django.db.models.Model``, you are free to add any field you want but make sure you
    don't use a unique constraint on any of your added fields because uniqueness
    prevents the copy mechanism of the extension from working correctly. This means that
    you can't use one-to-one relations on the extension model.

Finally, you'll need to register the model using ``extension_pool``.

Here's a simple example which adds an ``icon`` field to the page:

.. code-block::

    from django.db import models
    from cms.extensions import PageExtension
    from cms.extensions.extension_pool import extension_pool


    class IconExtension(PageExtension):
        image = models.ImageField(upload_to='icons')


    extension_pool.register(IconExtension)

Of course, you will need to make and run a migration for this new model.

The admin
+++++++++

To make your extension editable, you must first create an admin class that sub-classes
``cms.extensions.PageExtensionAdmin``. This admin handles page permissions.

Continuing with the example model above, here's a simple corresponding
``PageExtensionAdmin`` class:

.. code-block::

    from django.contrib import admin
    from cms.extensions import PageExtensionAdmin

    from .models import IconExtension


    class IconExtensionAdmin(PageExtensionAdmin):
        pass

    admin.site.register(IconExtension, IconExtensionAdmin)

Since PageExtensionAdmin inherits from ``ModelAdmin``, you'll be able to use the normal
set of Django ``ModelAdmin`` properties appropriate to your needs.

.. note::

    Note that the field that holds the relationship between the extension and a CMS Page
    is non-editable, so it does not appear directly in the Page admin views. This may be
    addressed in a future update, but in the meantime the toolbar provides access to it.

The toolbar item
++++++++++++++++

You'll also want to make your model editable from the cms toolbar in order to associate
each instance of the extension model with a page.

To add toolbar items for your extension create a file named ``cms_toolbars.py`` in one
of your apps, and add the relevant menu entries for the extension on each page.

Here's a simple version for our example. This example adds a node to the existing *Page*
menu, called *Page icon*. When selected, it will open a modal dialog in which the *Page
icon* field can be edited.

.. code-block::

    from cms.toolbar_pool import toolbar_pool
    from cms.extensions.toolbar import ExtensionToolbar
    from django.utils.translation import gettext_lazy as _
    from .models import IconExtension


    @toolbar_pool.register
    class IconExtensionToolbar(ExtensionToolbar):
        # defines the model for the current toolbar
        model = IconExtension

        def populate(self):
            # setup the extension toolbar with permissions and sanity checks
            current_page_menu = self._setup_extension_toolbar()

            # if it's all ok
            if current_page_menu:
                # retrieves the instance of the current extension (if any) and the toolbar item URL
                page_extension, url = self.get_page_extension_admin()
                if url:
                    # adds a toolbar item in position 0 (at the top of the menu)
                    current_page_menu.add_modal_item(_('Page Icon'), url=url,
                        disabled=not self.toolbar.edit_mode_active, position=0)

PageContent model extension example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we'll create a ``Rating`` extension field, that can be applied to each
``PageContent``, in other words, to each language version of each ``Page``.

.. note::

    Please refer to the more detailed discussion above of the Page model extension
    example, and in particular to the special **notes**.

The model
+++++++++

.. code-block::

    from django.db import models
    from cms.extensions import PageContentExtension
    from cms.extensions.extension_pool import extension_pool


    class RatingExtension(PageContentExtension):
        rating = models.IntegerField()


    extension_pool.register(RatingExtension)

The admin
+++++++++

.. code-block::

    from django.contrib import admin
    from cms.extensions import PageContentExtensionAdmin
    from .models import RatingExtension


    class RatingExtensionAdmin(PageContentExtensionAdmin):
        pass


    admin.site.register(RatingExtension, RatingExtensionAdmin)

The toolbar item
++++++++++++++++

In this example, we need to loop over the page contents for the page, and populate the
menu with those.

.. code-block::

    from cms.toolbar_pool import toolbar_pool
    from cms.extensions.toolbar import ExtensionToolbar
    from django.utils.translation import gettext_lazy as _
    from .models import RatingExtension
    from cms.utils import get_language_list  # needed to get the page's languages
    @toolbar_pool.register
    class RatingExtensionToolbar(ExtensionToolbar):
        # defines the model for the current toolbar
        model = RatingExtension

        def populate(self):
            # setup the extension toolbar with permissions and sanity checks
            current_page_menu = self._setup_extension_toolbar()

            # if it's all ok
            if current_page_menu and self.toolbar.edit_mode_active:
                # create a sub menu labelled "Ratings" at position 1 in the menu
                sub_menu = self._get_sub_menu(
                    current_page_menu, 'submenu_label', 'Ratings', position=1
                    )

                # we now need to get the pagecontent_set (i.e. different language page contents)
                # for this page
                page = self._get_page()
                page_contents = page.pagecontent_set(manager="admin_manager").latest_content(language__in=get_language_list(page.node.site_id))

                # create a 3-tuple of (title_extension, url, title)
                nodes = [
                    (*self.get_page_content_extension_admin(page_content), page_content.title)
                    for page_content in page_contents
                ]

                # cycle through the list of nodes
                for title_extension, url, title in nodes:

                    # adds toolbar items
                    sub_menu.add_modal_item(
                        'Rate %s' % title, url=url, disabled=not self.toolbar.edit_mode_active
                        )

Using extensions
----------------

In templates
~~~~~~~~~~~~

To access a page extension in page templates you can simply access the appropriate
related_name field that is now available on the Page object.

Page extensions
+++++++++++++++

As per the normal related_name naming mechanism, the appropriate field to access is the
same as your ``PageExtension`` model name, but lowercased. Assuming your Page Extension
model class is ``IconExtension``, the relationship to the page extension model will be
available on ``page.iconextension``. From there you can access the extra fields you
defined in your extension, so you can use something like:

.. code-block::

    {% load static %}

    {# rest of template omitted ... #}

    {% if request.current_page.iconextension %}
        <img src="{% static request.current_page.iconextension.image.url %}">
    {% endif %}

where ``request.current_page`` is the normal way to access the current page that is
rendering the template.

It is important to remember that unless the operator has already assigned a page
extension to every page, a page may not have the ``iconextension`` relationship
available, hence the use of the ``{% if ... %}...{% endif %}`` above.

PageContent extensions
++++++++++++++++++++++

In order to retrieve a page content extension within a template, get the ``PageContent``
object using ``request.current_page.get_content_obj``. Using the example above, we
could use:

.. code-block::

    {{ request.current_page.get_content_obj.ratingextension.rating }}

With menus
~~~~~~~~~~

Like most other Page attributes, extensions are not represented in the menu
``NavigationNodes``, and therefore menu templates will not have access to them by
default.

In order to make the extension accessible, you'll need to create a :ref:`menu modifier
<integration_modifiers>` (see the example provided) that does this.

Each page extension instance has a one-to-one relationship with its page. Get the
extension by using the reverse relation, along the lines of ``extension =
page.yourextensionlowercased``, and place this attribute of ``page`` on the node - as
(for example) ``node.extension``.

In the menu template the icon extension we created above would therefore be available as
``child.extension.icon``.

Handling relations
~~~~~~~~~~~~~~~~~~

If your ``PageExtension`` or ``PageContentExtension`` includes a ForeignKey *from*
another model or includes a ManyToManyField, you should also override the method
``copy_relations(self, oldinstance, language)`` so that these fields are copied
appropriately when the CMS makes a copy of your extension to support versioning, etc.

Here's an example that uses a ``ManyToManyField``

.. code-block::

    from django.db import models
    from cms.extensions import PageExtension
    from cms.extensions.extension_pool import extension_pool


    class MyPageExtension(PageExtension):

        page_categories = models.ManyToManyField(Category, blank=True)

        def copy_relations(self, oldinstance, language):
            for page_category in oldinstance.page_categories.all():
                page_category.pk = None
                page_category.mypageextension = self
                page_category.save()

    extension_pool.register(MyPageExtension)

Complete toolbar API
--------------------

The example above uses the :ref:`simplified_extension_toolbar`.

.. _complete_toolbar_api:

If you need complete control over the layout of your extension toolbar items you can
still use the low-level API to edit the toolbar according to your needs:

.. code-block::

    from cms.api import get_page_draft
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar
    from cms.utils import get_cms_setting
    from cms.utils.page_permissions import user_can_change_page
    from django.urls import reverse, NoReverseMatch
    from django.utils.translation import gettext_lazy as _
    from .models import IconExtension


    @toolbar_pool.register
    class IconExtensionToolbar(CMSToolbar):
        def populate(self):
            # always use draft if we have a page
            self.page = get_page_draft(self.request.current_page)

            if not self.page:
                # Nothing to do
                return

            if user_can_change_page(user=self.request.user, page=self.page):
                try:
                    icon_extension = IconExtension.objects.get(extended_object_id=self.page.id)
                except IconExtension.DoesNotExist:
                    icon_extension = None
                try:
                    if icon_extension:
                        url = reverse('admin:myapp_iconextension_change', args=(icon_extension.pk,))
                    else:
                        url = reverse('admin:myapp_iconextension_add') + '?extended_object=%s' % self.page.pk
                except NoReverseMatch:
                    # not in urls
                    pass
                else:
                    not_edit_mode = not self.toolbar.edit_mode_active
                    current_page_menu = self.toolbar.get_or_create_menu('page')
                    current_page_menu.add_modal_item(_('Page Icon'), url=url, disabled=not_edit_mode)

Now when the operator invokes "Edit this page..." from the toolbar, there will be an
additional menu item ``Page Icon ...`` (in this case), which can be used to open a modal
dialog where the operator can affect the new ``icon`` field.

Note that when the extension is saved, the corresponding page is marked as having
unpublished changes. To see the new extension values publish the page.

.. _simplified_extension_toolbar:

Simplified Toolbar API
~~~~~~~~~~~~~~~~~~~~~~

The simplified Toolbar API works by deriving your toolbar class from
``ExtensionToolbar`` which provides the following API:

- ``ExtensionToolbar.get_page_extension_admin()``: for page extensions, retrieves the
  correct admin URL for the related toolbar item; returns the extension instance (or
  ``None`` if none exists) and the admin URL for the toolbar item
- ``ExtensionToolbar.get_page_content_extension_admin(page_content=None)``: for page
  content extensions, retrieves the correct admin URL for the related toolbar item;
  returns a tuple of the extension instance (or ``None`` if none exists) and the admin
  URL for the current page content (if the argument is None or omitted) or the page
  content object passed.

  Typically, ``ExtensionToolbar.get_page_content_extension_admin`` is used without the
  argument to modify the toolbar for the currently visible page content object.

.. warning::

    The ``ExtensionToolbar.get_title_extension_admin(language=None)`` from django CMS
    versions before 4.1 still exists but is deprecated.

#################################
Extending the page & title models
#################################

.. versionadded:: 3.0

You can extend the page and title models with your own fields (e.g. adding
an icon for every page) by using the extension models:
``cms.extensions.PageExtension`` and ``cms.extensions.TitleExtension``,
respectively.


************************
Title vs Page extensions
************************

The difference between a **page extension** and a **title extension** is related to the difference
between the ``Page`` and ``Title`` models.

Titles support pages by providing a storage mechanism, amongst other things, for language-specific
properties of ``Pages``. So, if you find that you need to extend the page model in a
language-specific manner - for example, if you need to create language-specific keywords for each
language of your pages - then you may need to use a ``TitleExtension``.

On the other hand if the extension you'd like to create is the same for all of the different
languages of the page, then you may be fine using a ``PageExtension``.

***************************
Implement a basic extension
***************************

Three basic steps are required:

* add the extension *model*
* add the extension *admin*
* add a toolbar menu item for the extension

The model
=========

To add a field to the page model, create a class that inherits from
``cms.extensions.PageExtension``. Make sure to import the
``cms.extensions.PageExtension`` model. Your class should live in one of your
apps' ``models.py`` (or module).

.. note::

    Since ``PageExtension`` (and ``TitleExtension``) inherit from ``django.db.models.Model``, you
    are free to add any field you want but make sure you don't use a unique constraint on any of
    your added fields because uniqueness prevents the copy mechanism of the extension from working
    correctly. This means that you can't use one-to-one relations on the extension model.

Finally, you'll need to register the model using ``extension_pool``.

Here's a simple example which adds an ``icon`` field to the page::

    from django.db import models

    from cms.extensions import PageExtension
    from cms.extensions.extension_pool import extension_pool


    class IconExtension(PageExtension):
        image = models.ImageField(upload_to='icons')

    extension_pool.register(IconExtension)

Of course, you will need to make and run a migration for this new model.


The admin
=========

To make your extension editable, you must first create an admin class that
sub-classes ``cms.extensions.PageExtensionAdmin``. This admin handles page
permissions.

.. note::

    If you want to use your own admin class, make sure to exclude the live versions of the
    extensions by using ``filter(extended_page__publisher_is_draft=True)`` on the queryset.

Continuing with the example model above, here's a simple corresponding
``PageExtensionAdmin`` class::

    from django.contrib import admin
    from cms.extensions import PageExtensionAdmin

    from .models import IconExtension


    class IconExtensionAdmin(PageExtensionAdmin):
        pass

    admin.site.register(IconExtension, IconExtensionAdmin)


Since PageExtensionAdmin inherits from ``ModelAdmin``, you'll be able to use the
normal set of Django ``ModelAdmin`` properties appropriate to your
needs.

Once you've registered your admin class, a new model will appear in the top-
level admin list.

.. note::

    Note that the field that holds the relationship between the extension and a
    CMS Page is non-editable, so it does not appear directly in the Page admin views. This may be
    addressed in a future update, but in the meantime the toolbar provides access to it.


The toolbar item
================

You'll also want to make your model editable from the cms toolbar in order to
associate each instance of the extension model with a page.

To add toolbar items for your extension create a file named ``cms_toolbars.py``
in one of your apps, and add the relevant menu entries for the extension on each page.

Here's a simple version for our example::

    from cms.toolbar_pool import toolbar_pool
    from cms.extensions.toolbar import ExtensionToolbar
    from django.utils.translation import ugettext_lazy as _
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
                    # adds a toolbar item
                    current_page_menu.add_modal_item(_('Page Icon'), url=url,
                        disabled=not self.toolbar.edit_mode)

.. note::

    For a title extension, the ``populate()`` method above would need to loop over the titles for
    the page::

        def populate(self):
            # setup the extension toolbar with permissions and sanity checks
            current_page_menu = self._setup_extension_toolbar()
            # if it's all ok
            if current_page_menu and self.toolbar.edit_mode:
                # create a sub menu
                position = 0
                sub_menu = self._get_sub_menu(current_page_menu, 'submenu_label', 'Submenu', position)
                # retrieves the instances of the current title extension (if any) and the toolbar item URL
                urls = self.get_title_extension_admin()
                # cycle through the title list
                for title_extension, url in urls:
                    # adds toolbar items
                    sub_menu.add_modal_item('icon for title %s' % self._get_page().get_title(),
                                            url=url, disabled=not self.toolbar.edit_mode)

    Otherwise, the implementation is similar.


****************
Using extensions
****************

In templates
============

To access a page extension in page templates you can simply access the
appropriate related_name field that is now available on the Page object.

As per the normal related_name naming mechanism, the appropriate field to
access is the same as your ``PageExtension`` model name, but lowercased. Assuming
your Page Extension model class is ``IconExtension``, the relationship to the
page extension model will be available on ``page.iconextension``. From there
you can access the extra fields you defined in your extension, so you can use
something like::

    {% load staticfiles %}

    {# rest of template omitted ... #}

    {% if request.current_page.iconextension %}
        <img src="{% static request.current_page.iconextension.image.url %}">
    {% endif %}

where ``request.current_page`` is the normal way to access the current page
that is rendering the template.

It is important to remember that unless the operator has already assigned a
page extension to every page, a page may not have the ``iconextension``
relationship available, hence the use of the ``{% if ... %}...{% endif %}``
above.


With menus
==========

Like most other Page attributes, extensions are not represented in the menu ``NavigationNodes``,
and therefore menu templates will not have access to them by default.

In order to make the extension accessible, you'll need to create a :ref:`menu modifier
<integration_modifiers>` (see the example provided) that does this.

Each page extension instance has a one-to-one relationship with its page. Get the extension by
using the reverse relation, along the lines of ``extension = page.yourextensionlowercased``, and
place this attribute of ``page`` on the node - as (for example) ``node.extension``.

In the menu template the icon extension we created above would therefore be available as
``child.extension.icon``.


Handling relations
==================

If your ``PageExtension`` or ``TitleExtension`` includes a ForeignKey *from* another
model or includes a ManyToMany field, you should also override the method
``copy_relations(self, oldinstance, language)`` so that these fields are
copied appropriately when the CMS makes a copy of your extension to support
versioning, etc.


Here's an example that uses a ``ManyToMany``` field::

    from django.db import models
    from cms.extensions import PageExtension
    from cms.extensions.extension_pool import extension_pool


    class MyPageExtension(PageExtension):

        page_categories = models.ManyToMany('categories.Category', blank=True, null=True)

        def copy_relations(self, oldinstance, language):
            for page_category in oldinstance.page_categories.all():
                page_category.pk = None
                page_category.mypageextension = self
                page_category.save()

    extension_pool.register(MyPageExtension)



********************
Complete toolbar API
********************

The example above uses the :ref:`simplified_extension_toolbar`.

If you need complete control over the layout of your extension toolbar items you can still use the
low-level API to edit the toolbar according to your needs::

    from cms.api import get_page_draft
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar
    from cms.utils import get_cms_setting
    from cms.utils.permissions import has_page_change_permission
    from django.core.urlresolvers import reverse, NoReverseMatch
    from django.utils.translation import ugettext_lazy as _
    from .models import IconExtension


    @toolbar_pool.register
    class IconExtensionToolbar(CMSToolbar):
        def populate(self):
            # always use draft if we have a page
            self.page = get_page_draft(self.request.current_page)

            if not self.page:
                # Nothing to do
                return

            # check global permissions if CMS_PERMISSION is active
            if get_cms_setting('PERMISSION'):
                has_global_current_page_change_permission = has_page_change_permission(self.request)
            else:
                has_global_current_page_change_permission = False
                # check if user has page edit permission
            can_change = self.request.current_page and self.request.current_page.has_change_permission(self.request)
            if has_global_current_page_change_permission or can_change:
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
                    not_edit_mode = not self.toolbar.edit_mode
                    current_page_menu = self.toolbar.get_or_create_menu('page')
                    current_page_menu.add_modal_item(_('Page Icon'), url=url, disabled=not_edit_mode)


Now when the operator invokes "Edit this page..." from the toolbar, there will
be an additional menu item ``Page Icon ...`` (in this case), which can be used
to open a modal dialog where the operator can affect the new ``icon`` field.

Note that when the extension is saved, the corresponding page is marked as
having unpublished changes. To see the new extension values publish the page.


.. _simplified_extension_toolbar:

Simplified Toolbar API
======================

The simplified Toolbar API works by deriving your toolbar class from ``ExtensionToolbar``
which provides the following API:


* :py:meth:`cms.extensions.toolbar.ExtensionToolbar._setup_extension_toolbar`: this must be called first to setup
  the environment and do the permission checking;
* :py:meth:`cms.extensions.toolbar.ExtensionToolbar.get_page_extension_admin`: for page extensions, retrieves the
  correct admin URL for the related toolbar item; returns the extension instance (or `None` if not exists)
  and the admin URL for the toolbar item;
* :py:meth:`cms.extensions.toolbar.ExtensionToolbar.get_title_extension_admin`: for title extensions, retrieves the
  correct admin URL for the related toolbar item; returns a list of the extension instances
  (or `None` if not exists) and the admin urls for each title of the current page;

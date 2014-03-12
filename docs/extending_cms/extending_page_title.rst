#################################
Extending the page & title models
#################################

.. versionadded:: 3.0

You can extend the page and title models with your own fields (e.g. adding
an icon for every page) by using the extension models:
``cms.extensions.PageExtension`` and ``cms.extensions.TitleExtension``,
respectively.

******
How To
******

To add a field to the page model, subclass a class that inherits from
``cms.extensions.PageExtension``. Make sure to import the ``PageExtension``
model from the given path. It isn't importable from ``cms.models``. Your class
should live in one of your apps' ``models.py``. You are free to add any field
you want but make sure you don't use a unique constraint on any of your added
fields because uniqueness prevents the copy mechanism of the extension from
working correctly. This means that you can't use one-to-one relations on the
extension model. Finally, you'll need to register the model with the
``extension_pool``.

Here's a complete example::

    from django.db import models

    from cms.extensions import PageExtension
    from cms.extensions.extension_pool import extension_pool


    class IconExtension(PageExtension):
        image = models.ImageField(upload_to='icons')

    extension_pool.register(IconExtension)

***************************************
Hooking the extension to the admin site
***************************************

To make your extension editable, create an admin that subclasses
``cms.extensions.PageExtensionAdmin``. This admin handles page permissions. If
you want to use your own admin class, make sure to exclude the live versions of
the extensions by using ``filter(extended_page__publisher_is_draft=True)`` on
the queryset.

If you save an extension, the corresponding page is marked as having
unpublished changes. To see your extension live make sure to publish the page.

You'll also want to make your model editable from the cms toolbar in order to
associate each instance of the extension model with a page. (Page isn't an
editable attribute in the default admin interface.) The following example,
which should live in a file named ``cms_toolbar.py`` in one of your apps, adds
a menu entry for the extension on each page::

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

            # check global permissions if CMS_PERMISSIONS is active
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

***************************
Using extensions with menus
***************************

If you want the extension to show up in the menu (e.g. if you had created an
extension that added an icon to the page) use menu modifiers. Every ``node.id``
corresponds to their related ``page.id``. ``Page.objects.get(pk=node.id)`` is
the way to get the page object. Every page extension has a one-to-one
relationship with the page so you can access it by using the reverse relation,
e.g. ``extension = page.yourextensionlowercased``. Now you can hook this
extension by storing it on the node: ``node.extension = extension``. In the
menu template you can access your icon on the child object:
``child.extension.icon``.

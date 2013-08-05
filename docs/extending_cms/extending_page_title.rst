################################
Extending the page & title model
################################

If you want to extend the page or title model with your own fields e.g. adding
an icon for every page the extension models are the way to go.

*****
HowTo
*****

To add a field to the page model subclass a class that inherits from
``cms.extensions.PageExtension``. Make sure to import the PageExtension model
straight from the given path. It isn't importable from cms.models.
Your class should live in one of your apps ``models.py``. You are free to add
every field you want but make sure you doesn't use a unique constraint on any
of your added fields because uniqueness prevents the copy mechanism of the
extension. This forbids the use of OneToOne relations on the ExtensionModel.


***************************************
Hooking the extension to the admin site
***************************************

To make your created extension editable, create an admin that subclasses
``cms.admin.pageextensionadmin.PageExtensionAdmin``. This admin handles
Permissions and if you want to use your own admin class make sure to exclude
the live versions of the extensions by using
``filter(extended_page__publisher_is_draft=True)`` on the queryset.

If you save an extension, the corresponding page is marked as having
unpublished changes. To see your extension live make sure to publish the page.

To make your model editable from the cms toolbar, add a menu entry as in the
example below::

    from cms.api import get_page_draft
    from myapp.models import MyPageExtension
    from cms.utils import get_cms_setting
    from cms.utils.permissions import has_page_change_permission
    from django.core.urlresolvers import reverse, NoReverseMatch
    from django.utils.translation import ugettext_lazy as _

    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class MyPageExtensionToolbar(CMSToolbar):
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
                    mypageextension = MyPageExtension.objects.get(extended_object_id=self.page.id)
                except MyPageExtension.DoesNotExist:
                    mypageextension = None
                try:
                    if mypageextension:
                        url = reverse('admin:myapp_mypageextension_change', args=(mypageextension.pk,))
                    else:
                        url = reverse('admin:myapp_mypageextension_add') + '?extended_object=%s' % self.page.pk
                except NoReverseMatch:
                    # not in urls
                    pass
                else:
                    not_edit_mode = not self.toolbar.edit_mode
                    current_page_menu = self.toolbar.get_or_create_menu('page')
                    current_page_menu.add_modal_item(_('Title Extension'), url=url, disabled=not_edit_mode)

*******
Advices
*******


If you want the extension to show up in the menu e.g. if you had created an extension that added an icon to the page use MenuModifiers. Every node.id corresponds to their related page.id. ``Page.objects.get(pk=node.id)`` is the way to get the page object. Every page extension has a OneToOne relationship with the page so you can access it by using the reverse relation e.g. ``extension = page.yourextensionlowercased``. Now you can hook this extension by storing it on the node: ``node.extension = extension``. In the menu template you can access your icon on the child object: ``child.extension.icon``. 

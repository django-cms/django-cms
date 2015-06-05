# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.test_utils.testcases import CMSTestCase


class CustomModelTestCaseBase(CMSTestCase):
    def setUp(self):
        """
        Setups contents for testing functionnalities related to Custom Models administration:
        * create a "DVD" Page and register the related auto build AppHook
        * create 15 DVDs: 14 active, 1 inactive
        * create 30 books's instances: 
            * 15 in public domain (with 1 inactive) 
            * 15 not in public domain  (with 1 inactive)
        * create 5 publishers: 4 active, 1 inactive
        * create 5 authors: 4 active, 1 inactive
        """
        # TODO


class CustomModelAdminTestCase(CustomModelTestCaseBase):

    def test_modeladmin_autocreated_and_registrated(self):
        """
        Checks the auto-creation of ModelAdmins is okay:
        * DVD and Publisher must have ModelAdmin registered inheriting from `GenericModelAdmin`
          and must be defined outside the `custommodel_app.admin` module.
        * Book, PublicBook and Author must have a ModelAdmin inheriting from `GenericModelAdmin` 
          and must be defined inside the `custommodel_app.admin` module.
        """
        # TODO

    def test_front_and_back_edit_links(self):
        """
        Checks that the dynamic frontend mixin add a valid front and back edit links:
        * DVD Admin must have frontend and backend edit links (use lxml)
        """
        # TODO

    def test_front_only_edit_links(self):
        """
        Checks that the dynamic frontend mixin only add a front edit link when no change perm:
        * With a less permissive user, checks that DVD Admin only have the frontend link but not
          the backend edit link.
        """
        # TODO

    def test_back_only_edit_links(self):
        """
        Checks that the dynamic frontend mixin only add a front edit link when no change perm:
        * Author must only have a backend link only (this model doesn't have a detail view)
        """
        # TODO

    def test_switch_links_enabled(self):
        """
        Checks that the auto-generated boolean fields switchers for ModelAdmins are set and usable:
        * DVD Admin list must have links for each boolean fields.
        * Get the link URL updates the related field and redirect to the list view
        * Get the link URL updates again (instance's attribute is back to its initial value)
        """
        # TODO

    def test_switch_links_according_to_perms(self):
        """
        Checks that switchers are not set when a user does not have change_permission on a object
        * DVD Admin list must not have switcher links for published objects
        * DVD Admin list must have switcher links for unpublished objects
        * Get the link URL on a published object must raise a PermissionDenied
        * Get the link URL on a not published object updates the related field and redirect to 
          the list view.
        """
        # TODO

    def test_switch_links_ajaxable(self):
        """
        Checks with that switch links work with ajax to avoid page reloading:
        * Click on the link:
          * update the related field
          * doesn't redirect/reload the page
          * update the icon and title of the link
        * Another click on the link:
          * update the related field (instance's attribute is back to its initial value)
          * link is now the identic to the initial link (class, title etc.)
        """
        # TODO

    def test_toolbar_registration(self):
        """
        Checks that DVD, Publisher, Book and Author are in the toolbar, 
        except PublicBookProxy
        """
        # TODO

    def test_best_autocreated_modeladmin(self):
        """
        Checks that autocreated ModelAdmins are the "best" (dans le meilleur des mondes possibles):
        * DVD ModelAdmin must:
          * be filterable on BooleanField subclasses (is_active, still_published and public_domain)
          * be filterable on "Choice" fields (language)
          * be "date hierarchized" on the first DateField instance (publication_date)
          * be searchable on (Char|Text)Field subclasses without choices (title, summary)
          * be in list display for Char|Text|Integer|Boolean subclasses or ForeignKey instances
          * be editable for all fields except Placeholder subclasses.
          * `slug` field must be in `prepopulated_fields` via the `title` field
        """
        # TODO


class CustomModelPluginTestCase(CustomModelTestCaseBase):

    def test_cmslistplugin_autocreated_and_registrated(self):
        """
        Checks the auto-creation of CMSPlugin is okay:
        * DVD must have an auto registered CMSPlugin
        """
        # TODO

    def test_best_autocreated_cmslistplugin(self):
        """
        Checks that autocreated CMSPlugins are the "best" (dans le meilleur des mondes possibles):
        * DVD CMSPlugin must:
          * TODO : write the doc first !
          * TODO : describe the test.
        """
        # TODO

    def test_cmslistplugin_static_options(self):
        """
        Checks that autocreated CMSPlugin change form does not allow to update static options:
        * Author CMSPlugin should have all options set to static: checks these are not editable
        * Book CMSPlugin should have all options enabled: checks these are editable
        * Publisher CMSPlugin should have all options disabled
        """
        # TODO

    def test_cmslistplugin_feature_paginator(self):
        """
        Checks that CMSListPluginBase subclasses well render the paginator setting:
        * checks that pager is present if wanted and needed
        * checks that pager is not present if not wanted
        * checks that pager is not present if not needed
        """
        # TODO

    def test_cmslistplugin_feature_title(self):
        """
        Checks that CMSListPluginBase subclasses well render the title setting:
        * checks that title is not displayed when set as static and show_title is `False`
        * checks that title is displayed when set as static, 
          `show_title` is `True` and `value` is set
        * checks that title is not displayed when NOT set as static and `show_title` is set to 
          `False` by the user.
        * checks that title is displayed when NOT set as static and `show_title` is set to 
          `True` by the user and `value` is set by the user.
        * checks that title is displayed with its default value when `value` is empty and 
          `show_title` is `True`
        """
        # TODO

    def test_cmslistplugin_feature_subsets(self):
        """
        Checks that CMSListPluginBase subclasses well render the subsets setting:
        * checks that used queryset is the default one if this is not configured
        * checks that used queryset is the static configured one
        * checks that used queryset is the user configured one
        """
        # TODO

    def test_cmslistplugin_feature_search(self):
        """
        Checks that CMSListPluginBase subclasses well render the search setting:
        * TODO
        """
        # FIXME: do we really need this feature in Plugins ? If no : remove it from doc too !

    def test_cmslistplugin_feature_sort(self):
        """
        Checks that CMSListPluginBase subclasses well render the sort setting:
        * TODO
        """
        # FIXME: do we really need this feature in Plugins ? If no : remove it from doc too !


class CustomModelAppTestCase(CustomModelTestCaseBase):

    def test_apphook_autocreated_and_registrated(self):
        """
        Checks the auto-creation of AppHook is okay:
        * DVD must have an auto registered AppHook
        * Book must have an AppHook defined and registered in `custommodel_app.cms_app` module
        """
        # TODO
    
    def test_best_autocreated_apphook(self):
        """
        Checks that autocreated AppHooks are the "best" (dans le meilleur des mondes possibles):
        * DVD AppHook must have a detail view and a list view configured in urls:
          * detail url should be linked to a CMSDetailView
          * list url should be linked to a CMSListView
        (views are tested in CMSDetailViewTestCase and CMSListViewTestCase)
        """
        # TODO


class CustomModelPublisherTestCase(CustomModelTestCaseBase):
    #TODO: write tests specs.
    pass


class CMSCustomModelToolbarTestCase(CustomModelTestCaseBase):
    """
    When we are in a CustomModel View (Detail or List), those updates are done on the toolbar:
    * A new menu named with the current Model Name (e.g: Book, Author...) is added 
      (like the "Page" Menu) with those subentries:
      * Add a new "Book"
      * Edit current "Book" properties (only on the DetailView)
      * Delete the current "Book" (only on the DetailView)
      * (Un)Publish the current "Book" (only on the DetailView of a CustomModelPublisher)
    * When draft page is edited, "Publish modifications" is renamed to 
      "Publish Page modifications".
    * When a CustomModelPublisher instance is edited, a button "Publish « Book » modifications"
      is added (like the "Publish Page modifications" button for Pages)
    """

    def test_cmstoolbar_custommodel_menu_add(self):
        """
        Checks that toolbar has a "Add a new « ModelName » item" link in the CustomModel menu 
        which opens admin panel with the admin's add view.
        * Test with a CMSDetailView : add link present
        * Test with a CMSListView : add link present
        """
        # TODO

    def test_cmstoolbar_custommodel_menu_edit(self):
        """
        Checks that toolbar has a "Edit current « ModelName » item" link in the CustomModel menu 
        which opens admin panel with the admin's change view
        * Test with a CMSDetailView : edit link present
        * Test with a CMSListView : edit link NOT present
        """
        # TODO

    def test_cmstoolbar_custommodel_menu_delete(self):
        """
        Checks that toolbar has a "Delete current « ModelName » item" link in the CustomModel menu 
        which opens admin panel with the admin's delete view
        * Test with a CMSDetailView : delete link present
        * Test with a CMSListView : delete link NOT present
        """
        # TODO

    def test_cmstoolbar_custommodel_publish_page(self):
        """
        Checks that "publish modifications" button is renamed to avoid confusion:
        * Edits a page and checks that "Publish modifications" button is renamed as 
          "Publish Page modifications"
        """
        # TODO

    def test_cmstoolbar_custommodelpublisher_publish_buttons(self):
        """
        Checks "publish modifications" buttons are okay:
        * Edits a page and checks that "Publish modifications" button is renamed as 
          "Publish Page modifications" and there is not "Publish « Book » modifications" button.
        * Edits the current CustomModelPublisher instance and checks that 
          "Publish Page modifications" button is still there and a new 
          "Publish « Book » modifications" button has been added.
        * Clicks on "Publish « Book » modifications" and checks:
          * Book's instance public version has been updated
          * Page modifications remained not publicated.
          * Only the "Publish Page modifications" button remains
        * Edit current CustomModelPublisher instances, then click on "Publish Page modifications" 
          and checks that current page has been updated and only the 
          "Publish « Book » modifications" button remains
        """
        # TODO


class CMSDetailViewTestCase(CustomModelTestCaseBase):

    def test_raise_has_view_permission(self):
        """
        Checks that when `object.has_view_permission` return `False`, the DetailView raise a 403
        Checks that when returning `True`, a 200 is returned
        """
        # TODO
    
    def test_get_queryset(self):
        """
        Checks that this View use the \"all_can_view\" method of the Manager:
        Raises a 404 if wanted instance is not in the `all_can_view` queryset
        """
        # TODO
    
    def test_custommodelpublisher_draft_and_public(self):
        """
        Checks that in "public" mode, this is the "public" version of the instance which is used
        and in "edit" mode, this is the "draft" version.
        """
        # TODO


class CMSListViewTestCase(CustomModelTestCaseBase):

    def test_get_queryset(self):
        """Checks that this View use the \"all_can_view\" method of the Manager"""
        # TODO
    
    def test_custommodelpublisher_get_queryset(self):
        """
        Checks that, when using with a CustomModelPublisher, a filter is added on the queryset
        to limit results to public version only : even in edit mode
        (there is no needs to see draft versions in frontend ListView : admin is here for that)
        """
        # TODO

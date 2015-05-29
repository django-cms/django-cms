.. _custom-models:

#############
Custom Models
#############

We often need other editable contents than pages. Django allows you to create
as many models as you need. Most of the time, those models have common
behaviours: list view, detail view, permissions checking, cms toolbar integration,
etc. Django CMS provides some abstract classes and factory functions to simplify all 
of this and allows you to focus only on specific behaviours and rules.
Before reading this documentation's part, be sure you understood concepts 
exposed in :doc:`frontend_models`

.. _cms-models-class:

**********************
Create your cms models
**********************

CMSModelBase
============

This base class will register your Model as a "cms model" and will add
it to the cms-toolbar.

Methods
-------

``has_view_permission(self, request)``:
***************************************

Check if the user can display the current instance. Return ``True`` or ``False``.
Default behaviour is to test the default permission for this model.

.. _has_change_permission:

``has_change_permission(self, request)``:
*****************************************

Check if the user can edit the current instance. Return ``True`` or ``False``.
Default behaviour is to test the default permission for this model.

``has_delete_permission(self, request)``:
*****************************************

Check if the user can delete the current instance. Return ``True`` or ``False``.
Default behaviour is to test the default permission for this model.

``get_absolute_url(self, *args, **kwargs)``:
********************************************

It gets the absolute URL for the current instance. Default behaviour is to build an
url with "detail_url_name" and the slug field of the instance if exists, else
with the pk.
**If ``cms_detail_view`` meta option is disabled, this method will not be created**.

``get_slug(self, *args, **kwargs)``:
************************************

Get the value of slug field of the instance if exists, else return pk.

Meta options
------------

Those options may be set in ``class Meta`` of your model. When the class is 
created, you can access these if needed via 
MyCustomModel._cms_meta['name_without_cms_prefix']. ex::

    url_name = MyCustomModel._cms_meta['detail_url_name']

``cms_create_admin_model``:
***************************

If ``True``, the ModelAdmin is auto created and registered via ``modeladmin_cls_factory`` function
If ``False``, you may need to register your own admin model.
Default is ``False``.

If you are happy from 80% of what is automatically configured in the genereic ModelAdmin class
but want to add or change something, you can disable ``cms_create_admin_model``, manually call
the ``modeladmin_cls_factory`` function then modify (or extend) the class. 
See `CMSModels and django admin`_

``cms_create_plugin``:
**********************

If ``True``, a plugin is created and use cms.models.generic.GenericPluginModel.

Default is ``False``.

``cms_add_to_cms_toolbar``:
***************************

If ``True``, instances of this model are accessible from the cms-toolbar. 
You must have an AdminModel registered for your CMSModel if you set 
this option to ``True``.

Default is ``False``.

``cms_detail_view``:
********************

Can be a boolean or a view.
If ``True``, the detail view will be created using django ``cms.views.CMSModelDetailView``.
If ``str`` or view class, the detail view will not be created and the provided one will be used.
If ``False``, the detail view is neither created nor handled by django-cms.

Default is ``False``.

``cms_detail_view_url_name``:
*****************************

Configure the name of the detail view URL. 

Default is `None`.

.. _cms_create_app:

``cms_create_app``:
*******************

If ``True``, a cms app will be created.
If ``False``, no cms app is created.

Default is ``False``.

``cms_slug_field_name``:
************************

Specify the field used to build url.

Default is the first SlugField (or subclass) found in your model or `'pk'`.

.. _cms-models-list:


CMSPublisherModelBase
=====================

This base Class inherit from CMSModelBase_ and will allow you to have a model that has the 
same publishing workflow than pages:

* a "draft" and "published" version
* having "publish" and "modify" button in the toolbar when an instance's detail of your model 
  is displayed
* allow users to undo/redo their modifications

Model fields
------------

``publisher_is_draft``:
***********************

Defined as ``BooleanField`` and used to know if this is the "draft" (future) version or 
the "public" (current) version.

``publisher_related_version``:
******************************

Defined as ``OneToOneField`` and used to link the "draft version" to its "public version" 
and vice versa.

Methods
-------

``get_public_url(self)``
************************

Call a ``get_absolute_url`` on public object returned by ``self.get_public_object``

``get_draft_url(self)``
***********************

Call a ``get_absolute_url`` on public object returned by ``self.get_draft_object``

``get_public_object(self)``
***************************

Return the related "public version" of the current instance or it-self if the current instance is 
the "public version".

``get_draft_object(self)``
**************************

Return the related "draft version" of the current instance or it-self if the current instance is 
the "draft version".

``publish(self)``
******************

Publish the current "draft version" (become the new "public version") and update the old 
"public version" as the "new draft". Raises a ``PublicIsUnmodifiable`` exception if this 
method is called on the "public version".

``has_publish_permission(self, request, user=None)``
****************************************************

Default behaviour is a fallback on has_change_permission_ from CMSModelBase_.

CMSModelManager
==================



**********************************
Displaying your CMSModel instances
**********************************

Displaying lists and details of cms model's instances is often needed (e.g: last news or 
next events on the home page, last active topics in the sidebar, a page with all published news, 
a page with the detail of the news etc.) and the way to do it depend on your needs:

* You shoud use a subclass of CMSListPluginBase_ for displaying simple lists in 
  (static)placeholders. 
* For "real listing page", the prefered way is to use a subclass of CMSModelListView_
* To display a "detail page", you should use a subclass of CMSModelDetailView_

To link a page with some views, you need a simple CMSApp subclass (see :doc:`/how_to/apphooks`).
If your cms model has only a detail view and/or a list view, Django-CMS provides a factory 
to auto-generate this class and register it : cmsapp_cls_factory_ (this factory is used when you 
set the cms meta option cms_create_app_ is set to ``True``).

CMSListPluginBase
=================

This plugin can manage a list with a search form, a pager, a "see all" link etc. but is designed 
to add short lists in placeholders. If your page **must** display a list of items, you may 
better use a view which extends CMSModelListView_.

The minimal setup is::

    #file cms_plugins.py
    from cms.plugins.generic import CMSListPluginBase
    from .models import MyModel

    class MyPlugin(CMSListPluginBase):
        cms_model = MyModel

An extended setup can be::

    #file cms_plugins.py
    from cms.plugins.generic import CMSListPluginBase
    from .models import MyModel

    class MyPlugin(CMSListPluginBase):
        cms_model = MyModel
        features = {
            'title': {
                'static': True,
                'value': (
                    u'My custom list'
                    u' in which we can enable search form'
                    u' but not change this very long title'
                ),
            },
            'search': {
                'static': False,
                'enabled': True,
                'search_field': ['any_field'],
            }
            …
        }

Available settings
------------------

* ``cms_model``
    The only required parameter. A string with the complexe path to your model.
    ex: ``'myapp.models.MyModel'``

* ``features``
    This dictionnary describe features available for plugin configuration.
    Each feature can be either configured in python code or enabled for
    configuration in plugin Form depending on which functionalities you want to
    be dynamic (and stored in database). Each feature has it's own dictionary
    containing the following options:

    **Common options:**
  
    * ``static``: If ``False``, feature can be enabled and configured in the
      plugin form at runtime and configuration is stored in database.  If
      ``True``, feature is configured in python code.
  
      If ``static`` is ``True``, the other options describe the feature
      configuration. Otherwise, they describe the default configuration to
      initialise plugin form.
  
      Default value depends on each feature (See below).    
      

    **The features:**
  
    * ``title``: Allow to configure the title displayed at the top of the list.
          
      Options:
  
      * ``static``: Default is False.
      * ``show_title``: True or False. Default is True.
      * ``value``: The displaid string. If None or empty the model plural
        verbose name will be used. Default is None.
  
    * ``paginator``: Allow to enable a pager and limit the number of displaid
      list items at once. Both options are be configurable in plugin form.

      Options:

      * ``static``: Default is False.
      * ``show_paginator``: True or False.
      * ``paginate_by``: maximum number of displaid items,

    * ``search``: Allow to configure a search form.
      
      The plugin form only permit to enable or disable search form.
      __FIXME__: do we really need it in Plugin ?
    
      Options:
  
      * ``static``: Default is True.
      * ``enabled``: if True, a search form is displaid.
      * ``search_fields``: A list of field to search into. If empty or
        None, all compatible model fields will be used.
  
    * ``sort``: Allow to configure sorting. 
      __FIXME__: do we really need it in Plugin ?
     
      Options:
  
      * ``static``: Default is True.
      * ``enabled``: if True, a sort form a the top of the list will be
        displaid.
      * ``sort_fields``: A list of field to sort the list with. If empty or
        None, all compatible model fields will be used.

    * ``subsets``: Allow to chose a predefined subsets in plugin form.
          
      Options:
  
      * ``static``: Default is True.
      * ``available_querysets``: a dictionary of tulpes (label, queryset) in
        which queryset can be either a queryset or a collable returning a
        queryset.
      * ``queryset``: a key of available_querysets dictionary, or a queryset
        or a collable returning a queryset. If None, super self.get_queryset is used.
    
* ``new_link``
    If ``True``, add a creation link when plugin is rendered.
  
* ``template``
    Template to render the view. Default is '%(app_name)/plugins/%(PluginClassName)s.html'

Usefull methods
---------------

* ``get_queryset``
    This method get the base query_set of your cms model. Its default is::

        def get_queryset(self)
            return self.cms_model.objects.all()

    You can overwrite it to use your specific manager. ex::

        def get_queryset(self)
            return self.cms_model.objects.published()

* ``get_search_and_sort_form``
    Allow you to have specific code for search and/or sort form.

* ``get_search_query_set``
    Allow you to build complex queryset instead of standard search process.

* ``get_template``
    If the template to use is different from a contex to an other, you can add your
    logic choice here.

* ``get_pager``
    Get the pager if enabled.

Usefull attributes
------------------

* ``request``
    As Django's Generic Views, the current request will be available as an
    attribute, allowing you to use it in all methods.


CMSModelDetailView
=====================

This subclass of Django's DetailView_ allow you to display a page detail of an instance of 
your cms model. Staff users will have a management menu in the toolbar (as the "page" menu, 
to manage all fields (visible and hidden in the detail page)) and publish actions if your model 
extends CMSPublisherModelBase_.

Some methods are overridden:

* ``get_object``
    to check ``has_detail_permission`` from our cms models 
    and raise a PermissionDenied if user has not enough rights.
* ``get_queryset``
    Retrieve the queryset from the super and chain it with ``all_can_view`` if available. 
    (see CMSModelManager_ for explanations about ``all_can_view``)


See DetailView_'s documentation for more details on what you can overwrite.

.. _DetailView: https://docs.djangoproject.com/en/dev/ref/class-based-views/generic-display/#detailview



CMSModelListView
===================

TODO

See ListView_'s documentation for more details on what you can overwrite.

.. _ListView: https://docs.djangoproject.com/en/dev/ref/class-based-views/generic-list/#listview

.. _cms-models-admin:

**************************
CMSModels and django admin
**************************

It's important for your users to find a homogeneity when they manage pages or 
your CMSModels.

``modeladmin_cls_factory``
==========================

This generic ModelAdmin factory will create an auto-configured Django-CMS ModelAdmin for your 
CMSModel.

The created admin model is named "Generic%(AppLabel)%(ModelName)sAdmin". If your model 
is "Author" from "library" app, then his modelAdmin will be "GenericLibraryAuthorAdmin".

Auto-configuration of those modelAdmins use these rules :

* ``list_display``:
    All instances (or subclass) of BooleanField, IntegerField, DateField,
    ForeignKey (but PlaceholderField) or CharField with a max_length lesser 
    than 255. Boolean fields are not "only" displaid : we create a link 
    allowing the user to change the field's value of the instance.
* ``search_fields``:
    All instances (or subclass) of CharFields or TextField
* ``list_filter``:
    All instances (or subclass) of BooleanField or CharField
    with "choices".
* ``fields``:
    All fields but PlaceholderField
* ``ordering``:
    Get default model ordering from meta options.
* ``prepopulated_fields``:
    If you have a slug field configured with ``cms_slug_field_name`` 
    (see below), check if you have a CharField named "title" or "name" and 
    use it to prepopulate the slug.

Some methods are also automatically created :

* ``get_urls``: 
    Only created if your model have some BooleanFields. Return urls of change
    boolean fields views.
* ``change_%(field_name)s``:
    For each boolean fields, a method is created to switch the field's value.
    This method is called as a view when the user click on the link we add when
    displaying a boolean field in list view.

When using or subclassing the resulting class, you'll get a link in change_list to load the
detail view of your model instance in the main frame of the website. 
(this link replace the standard "admin" link which display the admin form)

Each lines in change list will also have an edit icon to edit the 
instance properties (all fields but placeholders) : this is the standard "admin" link

Templates used to display the list are responsive (as templates for pages 
management) to display usefull informations depending on the width of the 
admin's frame.

Usage Ex::

    # -*- coding: utf-8 -*-

    from django.contrib import admin
    from .models import Author, Book, PublicBookProxy, Publisher
    from cms.utils.generic import modeladmin_cls_factory, modeladmin_bool_field_link_factory

    """Exemple of using the full GenericModelAdmin class generated"""
    PublisherAdmin = modeladmin_cls_factory(model=Publisher, auto_register=True)

    """Exemple of changing some GenericModelAdmin class properties"""
    AuthorAdmin = modeladmin_cls_factory(model=Author)
    AuthorAdmin.list_display = [
        'first_name', 'last_name', 'email',
        modeladmin_bool_field_link_factory('published', 'Published'), 
        modeladmin_bool_field_link_factory('is_alive', 'Still alive'),]
    admin.site.register(Author, AuthorAdmin)


    """Exemple of extending some GenericModelAdmin class"""
    BookModelAdminBase =  modeladmin_cls_factory(model=Book)

    class BookModelAdmin(BookModelAdminBase):
        pass

    admin.site.register(Book, BookModelAdmin)


    class PublicBookModelAdmin(BookModelAdminBase):
        list_display = list(set(BookModelAdminBase.list_display) - set(('public_domain',)))

        def queryset(self, request):
            queryset = super(PublicBookModelAdmin, self).queryset(request)
            return qs.filter(public_domain=True)

    admin.site.register(PublicBookProxy, PublicBookModelAdmin)

    """
    We do not need to create or register a DVDModelAdmin because we set it to be fully aut-configured 
    via the cms_meta options.
    """

*******
Helpers
*******

Django-CMS use some factory to create default classes used for CMSModels : AppHook subclass, 
ModelAdmin subclass, CMSPlugin subclass... Some of these classes need methods which are 
auto-generated too. Used factory functions are public and you are encouraged to use it when 
needed instead of redo the wheel.

.. _cmsapp_cls_factory:

cmsapp_cls_factory(model, app_name=None, auto_register=False)
=============================================================

Builds the "best" default ``AppHook`` subclass for the current model and auto register it via 
``apphook_pool.register`` if wanted.

Returned class will be named ``Generic{AppLabel}{ModelName}App``. e.g for a model ``Book`` from 
``library.models.py``, the generated app name will be ``GenericLibraryBookApp``.


.. _cmsplugin_cls_factory:

cmsplugin_cls_factory(model, auto_register=False)
=================================================

Builds the "best" default ``CMSPlugin`` subclass for the given CMSModel to display a list of 
its instances and auto register it via ``apphook_pool.register`` if wanted.

Returned class will be named ``Generic{AppLabel}{ModelName}ListPlugin``. e.g for a model ``Book`` 
from ``library.models.py``, the generated app name will be ``GenericLibraryBookListPlugin``.


.. _cmsattachmenu_cls_factory:

cmsattachmenu_cls_factory(model, auto_register=False)
=====================================================

Builds the "best" default ``CMSAttachMenu`` subclass for the given CMSModel to have a 
submenu with all instances detail link and auto register it via ``menu_pool.register_menu`` 
if wanted.

Returned class will be named ``Generic{AppLabel}{ModelName}Menu``. e.g for a model ``Book`` 
from ``library.models.py``, the generated app name will be ``GenericLibraryBookMenu``.

.. _modeladmin_cls_factory:

modeladmin_cls_factory(model, auto_register=False)
==================================================

Builds the "best" default ``ModelAdmin`` to manage the given CMSModel and auto register it 
if wanted via ``admin.site.register``.
    
Returned class will be named ``Generic{AppLabel}{ModelName}Admin``. e.g for a model ``Book`` from 
``library.models.py``, the generated app name will be ``GenericLibraryBookAdmin``.


.. _modeladmin_switch_bool_field_func_factory:

modeladmin_switch_bool_field_func_factory(field_name)
=====================================================

Creates and returns a ModelAdmin view method to switch the value of a boolean field.
Returned method view raises a 404 if object is not found, else it swiches the value of the related 
field, then redirect to the list (related url path MUST looks like `^([0-9]+)/whatever/$`) or,
if ajax, returns a dict with keys `obj_title` and `new_value`.
e.g: with `field_name` = 'published', returned method will be equivalent to::

    def switch_published(self, request, obj_id):
        """switches the "published" boolean field from True to False or vice versa"""
        obj = get_object_or_404(self.model, pk=obj_id)
        new_value = not obj.published
        obj.published = new_value
        obj.save()
        if request.is_ajax():
            return json.dumps({'obj_title': '%s' % obj, 'new_value': new_value,})
        else:
            return HttpResponseRedirect('../../')

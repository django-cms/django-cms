##############
API References
##############


***************
cms.plugin_base
***************

.. module:: cms.plugin_base

.. class:: CMSPluginBase

    Inherits ``django.contrib.admin.options.ModelAdmin``.
        
    .. attribute:: admin_preview
    
        Defaults to ``True``, if ``False`` no preview is done in the admin.
        
    .. attribute:: change_form_template

        Custom template to use to render the form to edit this plugin.    
    
    .. attribute:: form
    
        Custom form class to be used to edit this plugin.

    .. attribute:: model

        Is the CMSPlugin model we created earlier. If you don't need a model
        because you just want to display some template logic, use CMSPlugin from
        ``cms.models`` as the model instead.
        
    .. attribute:: module

        Will be group the plugin in the plugin editor. If module is None,
        plugin is grouped "Generic" group.
    
    .. attribute:: name
        
        Will be displayed in the plugin editor.
        
    .. attribute:: render_plugin
    
        If set to ``False``, this plugin will not be rendered at all.
        
    .. attribute:: render_template
    
        Will be rendered with the context returned by the render function.
        
    .. attribute:: text_enabled
    
        Whether this plugin can be used in text plugins or not.
        
    .. method:: icon_alt(instance)
        
        Returns the alt text for the icon used in text plugins, see
        :meth:`icon_src`. 
        
    .. method:: icon_src(instance)
    
        Returns the url to the icon to be used for the given instance when that
        instance is used inside a text plugin.
        
    .. method:: render(context, instance, placeholder)
    
        This method returns the context to be used to render the template
        specified in :attr:`render_template`.
        
        :param context: Current template context.
        :param instance: Plugin instance that is being rendered.
        :param placeholder: Name of the placeholder the plugin is in.
        :rtype: ``dict``
        
    .. class:: PluginMedia
        
        Defines media which is required to render this plugin.
        
        .. attribute:: css
            
            The CSS files required to render this plugin as a dictionary with
            the display type as keys and a sequence of strings as values.
            
        .. attribute:: js
            
            The Javascript files required to render this plugin as a sequence
            of strings.


**********
menus.base
**********

.. module:: menus.base

.. class:: NavigationNode(title, url, id[, parent_id=None][, parent_namespace=None][, attr=None][, visible=True])

    A navigation node in a menu tree.
        
    :param string title: The title to display this menu item with.
    :param string url: The URL associated with this menu item.
    :param id: Unique (for the current tree) ID of this item.
    :param parent_id: Optional, ID of the parent item.
    :param parent_namespace: Optional, namespace of the parent.
    :param dict attr: Optional, dictionary of additional information to store on
                      this node.
    :param bool visible: Optional, defaults to ``True``, whether this item is
                         visible or not.
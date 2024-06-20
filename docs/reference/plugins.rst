#######
Plugins
#######

.. autoclass:: cms.plugin_base.CMSPluginBase
  :members:

  ..  method:: get_render_template(self, context, instance, placeholder)

        If you need to determine the plugin render model at render time
        you can implement the :meth:`get_render_template` method on the plugin
        class; this method takes the same arguments as ``render``.

        The method **must** return a valid template file path.

        Example::

            def get_render_template(self, context, instance, placeholder):
                if instance.attr = 'one':
                    return 'template1.html'
                else:
                    return 'template2.html'

        See also: :meth:`render_plugin` , :meth:`render_template`


.. autoclass:: cms.plugin_base.PluginMenuItem

.. autoclass:: cms.models.pluginmodel.CMSPlugin
  :members:

.. autoclass:: cms.plugin_pool.PluginPool
  :members:


******************************************
Plugin utility functions
******************************************

.. autofunction:: cms.utils.plugins.assign_plugins

.. autofunction:: cms.utils.plugins.copy_plugins_to_placeholder

.. autofunction:: cms.utils.plugins.downcast_plugins

.. autofunction:: cms.utils.plugins.get_bound_plugins

.. autofunction:: cms.utils.plugins.get_plugin_class

.. autofunction:: cms.utils.plugins.get_plugin_model

.. autofunction:: cms.utils.plugins.get_plugin_restrictions

.. autofunction:: cms.utils.plugins.get_plugins

.. autofunction:: cms.utils.plugins.get_plugins_as_layered_tree

.. autofunction:: cms.utils.plugins.has_reached_plugin_limit


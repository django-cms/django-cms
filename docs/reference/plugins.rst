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

  .. attribute:: allowed_models

        A list of model identifiers (in the format ``"app_label.modelname"``) that
        restricts where this plugin can be used. If ``None`` (default), the plugin
        is available for all models with placeholders.

        See :ref:`plugin-model-restrictions` for details.


.. autoclass:: cms.plugin_base.PluginMenuItem

.. autoclass:: cms.models.pluginmodel.CMSPlugin
  :members:

  .. method:: add_structureboard_classes(self)

        Optional method on a :class:`~cms.models.pluginmodel.CMSPlugin` subclass. If
        defined, its return value is added as CSS classes to the ``cms-draggable``
        container in the structure board. This can be used together with custom CSS to
        visually style a plugin or its children — for example, to mark deactivated
        plugins.

        :rtype: str

        See :ref:`custom-plugins` for a full example.

.. autoclass:: cms.plugin_pool.PluginPool
  :members:


************************
Plugin utility functions
************************

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


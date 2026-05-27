.. _utility_functions:

#################
Utility functions
#################

Utility functions provide functionality that is regularly used within the django CMS core and are also available to
third party packages.

*************
Model admin
*************

.. module:: cms.admin.utils

Action buttons
**************

.. autoclass:: ChangeListActionsMixin
    :members:
    :show-inheritance:

Grouper admin
*************

.. autoclass:: GrouperModelAdmin
    :members:
    :show-inheritance:


************
Placeholders
************

.. module:: cms.utils.placeholder

.. autofunction:: get_placeholder_from_slot

.. autofunction:: get_declared_placeholders_for_obj


*******
Plugins
*******

.. module:: cms.utils.plugins
   :no-index:

.. autofunction:: get_plugins
   :no-index:

.. autofunction:: assign_plugins
   :no-index:

.. autofunction:: has_reached_plugin_limit
   :no-index:

.. autofunction:: get_plugin_class
   :no-index:

.. autofunction:: get_plugin_model
   :no-index:

.. autofunction:: get_plugins_as_layered_tree
   :no-index:

.. autofunction:: copy_plugins_to_placeholder
   :no-index:

.. autofunction:: downcast_plugins
   :no-index:

.. autofunction:: get_bound_plugins
   :no-index:

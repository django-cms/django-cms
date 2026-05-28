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
   :noindex:

.. autofunction:: get_plugins
   :noindex:

.. autofunction:: assign_plugins
   :noindex:

.. autofunction:: has_reached_plugin_limit
   :noindex:

.. autofunction:: get_plugin_class
   :noindex:

.. autofunction:: get_plugin_model
   :noindex:

.. autofunction:: get_plugins_as_layered_tree
   :noindex:

.. autofunction:: copy_plugins_to_placeholder
   :noindex:

.. autofunction:: downcast_plugins
   :noindex:

.. autofunction:: get_bound_plugins
   :noindex:

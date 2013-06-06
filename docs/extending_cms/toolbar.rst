#####################
Extending the Toolbar
#####################

.. versionadded:: 3.0

You can add and remove items to the toolbar. This allows you to integrate your
application in the frontend editing mode of django CMS and provide your users
with a streamlined editing experience.

For the toolbar API reference, please refer to :ref:`toolbar-api-reference`.


***********
Registering
***********

There's two ways to control what items are shown in the toolbar or not. One is
the :setting:`CMS_TOOLBARS` that gives you full control over what modifiers are
loaded, but requires you to specify them all manually. The other is to create
``cms_toolbar.py`` files in your apps which will be automatically loaded if
:setting:`CMS_TOOLBARS` is not set (or set to ``None``).

If you use the automated way, your ``cms_toolbar.py`` file should contain
functions that modify the toolbar using :meth:`toolbar_pool.register`. These
functions must accept four parameters: The toolbar object, the current request,
a flag indicating whether the current request is handled by the same app as the
function is in and the name of the app used for the current request. Modifier
functions have no return value. The register function can be used as a
decorator.

A simple example that registers a modifier that does nothing::

    from cms.toolbar_pool import toolbar_pool

    @toolbar_pool.register
    def noop_modifier(toolbar, request, is_current_app, app_name):
        pass


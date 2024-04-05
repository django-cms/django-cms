.. _upgrade_custom-plugins:

How to upgrade custom plugins for django CMS v4+
================================================

Difference between django CMS v3 and v4 plugins
-----------------------------------------------

The main difference between plugins of django CMS version 3 and django CMS v4 is how the
tree is stored in the database. Up to django CMS version 3, the plugin model
:class:`~cms.models.pluginmodel.CMSPlugin` inherited from a tree model ``MP_Node``
declared in `the django-treebeard library
<https://github.com/django-treebeard/django-treebeard>`_.

As of django CMS version 4, :class:`~cms.models.pluginmodel.CMSPlugin` inherits directly
from :class:`django.db.models.Model` and manages the tree structure with the two fields
:attr:`~cms.models.pluginmodel.CMSPlugin.parent` and
:attr:`~cms.models.pluginmodel.CMSPlugin.position` using SQL Common Table Expressions
(CTE) which allow recursive SQL statements. Consequently all model fields originating
with treebeard are not available in django CMS v4+.

.. warning::

    Django CMS 4 removes the following fields form
    :class:`~cms.models.pluginmodel.CMSPlugin`:

    - ``depth``
    - ``numchild``
    - ``path``

Also, the meaning of the :attr:`~cms.models.pluginmodel.CMSPlugin.position` field has
changed. Im django CMS v3 it was unique for each
:attr:`~cms.models.pluginmodel.CMSPlugin.parent` value (including ``None`` for plugins
at root level). From django CMS v4 on, it is unique for each
:attr:`~cms.models.pluginmodel.CMSPlugin.placeholder` and
:attr:`~cms.models.pluginmodel.CMSPlugin.language` entry. Also, positions are counted
from 1 to *n* for all *n* plugins of a placeholder language combination. There must not
be gaps in the position field (i.e., a missing position value).

.. warning::

    Since the management of the plugin tree happens within the CMS it is important to
    use the new placeholder API described in the section :ref:`placeholder-plugin-api`
    to create and delete plugins.

What to change
--------------

The good news is that most custom plugins will *not* require any changes. This is unless
they either directly **access one of the django-treebeard fields** or they **create or
delete plugins programmatically**.

Replacing access to django-treebeard fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your custom plugin accesses django-treebeard field directly, you will have to change
your code. How to do this obviously depends on what your code needs to achieve. Here are
some examples:

``path``
++++++++

To order a queryset of plugins replace ``qs.orderby("path")`` by
``qs.orderby("position")``.

``depth``
+++++++++

There is no correspondence to the ``depth`` field. If needed, it has to be computed:

.. code-block::

    @property
    def depth(self):
        if self.parent is None:
            return 1
        return self.parent.depth + 1

``position``
++++++++++++

Often changes are made at the leaves of the tree. If you happen to know that the parent
plugin does not have grant-children, the quick way to get a django CMS 3 position value
is:

.. code-block::

    plugin.position - plugin.parent.position if plugin.parent else plugin.position

To calculate the ``position`` field valid for all cases, you can use this code bit:

.. code-block::

    @property
    def v3position(self):
        siblings = CMSPlugin.objects.filter(parent=self.parent).orderby("position")
        pos = 1
        for plugin in siblings:
            if plugin == self:
                return pos
            pos += 1

Creating or deleting plugins programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a plugin, first build an instance, then add it to its placeholder:

.. code-block::

    my_new_plugin = MyPluginModel(parent=None, position=1, my_config="whatever", placeholder=my_placholder)
    my_placeholder.add_plugin(my_new_plugin)

This example puts the plugin at the first position if the placeholder. Those shortcuts
might help:

==================================================================== =========================
Position                                                             Meaning
==================================================================== =========================
``position=parent.position + 1``                                     First child of ``parent``
``position=parent.position + n``                                     *n* th child of
                                                                     ``parent`` if parent does
                                                                     **not** have
                                                                     grand-children
``position=placeholder.get_last_plugin_position(language="en") + 1`` Last plugin in
                                                                     placeholder
==================================================================== =========================

.. warning::

    Do **not** use ``MyPluginModel.objects.create()``. It will almost certainly throw a
    database integrity exception.

Creating "universal" plugins
----------------------------

Some packages introduce universal plugins which can be used both on django CMS 3 and
django CMS 4 alike. Examples include `djangocms-text-ckeditor
<https://github.com/django-cms/djangocms-text-ckeditor>`_ or `djangocms-frontend
<https://github.com/django-cms/djangocms-frontend>`_.

Here is an excerpt from djangocms-text-ckeditor which needs to be able to create and
delete child plugins for text fields. It adds private static methods to

.. code-block::

    @staticmethod
    def _create_ghost_plugin(placeholder, plugin):
        """CMS version-save function to add a plugin to a placeholder"""
        if hasattr(placeholder, "add_plugin"):  # available as of CMS v4
            placeholder.add_plugin(plugin)
        else:  # CMS < v4
            plugin.save()  # Plugin is created upon save

Similarly, it deletes plugins:

.. code-block::

    @staticmethod
    def _delete_plugin(plugin):
        """Version-safe plugin delete method"""
        placeholder = plugin.placeholder
        if hasattr(placeholder, 'delete_plugin'):  # since CMS v4
            return placeholder.delete_plugin(plugin)
        else:
            return plugin.delete()

.. note::

    Please consider the different counting schemes for the
    :attr:`~cms.models.pluginmodel.CMSPlugin.position` field.

Adapting your test suite
------------------------

Test suites often create pages, add plugins that are to be tested, and publish the
pages. Since publishing in django CMS 4 is not part of the core any more, a way updating
the test suites is to add a test fixture to your tests that provide publish and
unpublish functionality.

In the tests themselves all ``page.publish()`` calls then need to be replaced by
``self.publis(page)`` calls to the fixture.

Here's an example of test fixture (from djangocms-frontend)

.. code-block::

    from packaging.version import Version

    from cms import __version__

    DJANGO_CMS4 = Version(__version__) >= Version("4")


    class TestFixture:
        """Sets up generic setUp and tearDown methods for tests."""

        if DJANGO_CMS4:  # CMS V4
            def _get_version(self, grouper, version_state, language=None):
                language = language or self.language

                from djangocms_versioning.models import Version

                versions = Version.objects.filter_by_grouper(grouper).filter(
                    state=version_state
                )
                for version in versions:
                    if (
                        hasattr(version.content, "language")
                        and version.content.language == language
                    ):
                        return version

            def publish(self, grouper, language=None):
                from djangocms_versioning.constants import DRAFT

                version = self._get_version(grouper, DRAFT, language)
                if version is not None:
                    version.publish(self.superuser)

            def unpublish(self, grouper, language=None):
                from djangocms_versioning.constants import PUBLISHED

                version = self._get_version(grouper, PUBLISHED, language)
                if version is not None:
                    version.unpublish(self.superuser)

            def create_page(self, title, **kwargs):
                kwargs.setdefault("language", self.language)
                kwargs.setdefault("created_by", self.superuser)
                kwargs.setdefault("in_navigation", True)
                kwargs.setdefault("limit_visibility_in_menu", None)
                kwargs.setdefault("menu_title", title)
                return create_page(title=title, **kwargs)

            def get_placeholders(self, page):
                return page.get_placeholders(self.language)

        else:  # CMS V3
            def publish(self, page, language=None):
                page.publish(language)

            def unpublish(self, page, language=None):
                page.unpublish(language)

            def create_page(self, title, **kwargs):
                kwargs.setdefault("language", self.language)
                kwargs.setdefault("menu_title", title)
                return create_page(title=title, **kwargs)

            def get_placeholders(self, page):
                return page.get_placeholders()

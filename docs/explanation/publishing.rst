.. _publishing:

Publishing
==========

Publishing in django CMS controls when content becomes visible to site visitors.
Separating editing from publishing is fundamental to professional content management
workflows, allowing editors to prepare, review, and approve content before it goes live.

.. note::

    Publishing and versioning capabilities are provided by **separate packages**, not by
    django CMS core. This modular design allows projects to choose the versioning
    strategy that best fits their needs—though most sites use the standard
    djangocms-versioning package described below.

Default behavior
----------------

Without a versioning package installed, django CMS pages are published immediately upon
saving. Every change is visible to the public the moment you save it. This simple model
works well for small sites or development environments where immediate visibility is
acceptable.

djangocms-versioning
--------------------

`djangocms-versioning <https://github.com/django-cms/djangocms-versioning>`_ is the
standard versioning package endorsed by the django CMS Association. It provides a
full-featured versioning system with multiple states: **draft**, **published**,
**unpublished**, and **archived**.

This package is recommended for most production sites requiring editorial workflows,
content approval processes, or the ability to prepare content in advance.

For complex editorial requirements, djangocms-versioning can be extended with
`djangocms-moderation <https://github.com/django-cms/djangocms-moderation>`_, which
adds custom moderation workflows. This allows you to define approval chains where
content must pass through multiple review stages before publication—useful for
organisations with formal content governance processes.

.. _version_states:

Version states
~~~~~~~~~~~~~~

Each :class:`~cms.models.pagemodel.Page` object can have multiple
:class:`~cms.models.contentmodels.PageContent` objects, each carrying a version number
and state. The states are:

**draft**
    The version currently being edited. Only draft versions can be modified, and only
    one draft per language is allowed. Changes to drafts are not visible to the public.

**published**
    The version currently visible on the website. Only one published version per
    language can exist. Published versions cannot be edited directly—to make changes,
    you create a new draft based on the published version.

**unpublished**
    A version that was previously published but has been taken offline. Multiple
    unpublished versions can exist, preserving the history of what was once live.

**archived**
    A version that was never published. Archived versions preserve work that may be
    useful later and can be reverted to draft state when needed.

Each new draft generates a new version number, providing a complete history of changes.

.. image:: /images/version-states.png
    :align: center
    :alt: Version states

When a page is published, it becomes publicly visible even if its parent pages are not
published.

Scope of versioning
~~~~~~~~~~~~~~~~~~~

While this section focuses on pages, djangocms-versioning can version other content
types as well. For example, `djangocms-alias <https://github.com/django-cms/
djangocms-alias>`_ uses djangocms-versioning to provide versioned aliases—reusable
content blocks that can be managed with the same editorial workflow as pages.

Working with PageContent in code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When querying :class:`~cms.models.contentmodels.PageContent` objects, the default
manager only returns published content:

.. code-block:: python

    PageContent.objects.filter(language="en")  # Returns only published English content

This default behavior ensures that draft or unpublished content never accidentally
leaks to the public.

For admin interfaces and editorial views where you need access to all versions,
djangocms-versioning provides an ``admin_manager``. **Use this manager only in admin
contexts**:

.. code-block:: python

    PageContent.admin_manager.filter(page=my_page, language="en")  # All versions

To retrieve a specific draft version:

.. code-block:: python

    from djangocms_versioning.constants import DRAFT
    from djangocms_versioning.models import Version

    version = Version.objects.get(
        content__page=my_page,
        content__language="en",
        state=DRAFT
    )
    draft_content = version.content

To access the "current" version (draft if one exists, otherwise published):

.. code-block:: python

    from djangocms_versioning.constants import DRAFT

    for content in PageContent.admin_manager.filter(page=my_page).current_content():
        if content.versions.first().state == DRAFT:
            # Handle draft version
            pass

For comprehensive details, see the `djangocms-versioning documentation
<https://djangocms-versioning.readthedocs.io>`_.

Alternative versioning packages
-------------------------------

Django CMS uses a contract-based approach (the ``CMSAppExtension`` interface) that
allows alternative versioning implementations. While djangocms-versioning is the
endorsed standard, you can use or create alternatives when your requirements differ.

An example is `djangocms-no-versioning
<https://github.com/benzkji/djangocms-no-versioning>`_, which provides simplified
publish/unpublish toggling without maintaining a full version history—suitable when
you need basic visibility control but not complete version tracking.

This flexibility allows you to:

- Use the endorsed djangocms-versioning for full version control
- Use a lighter-weight alternative when simpler workflows suffice
- Create a custom versioning package tailored to your specific requirements

Considerations when choosing or switching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Different versioning packages may have fundamentally different model structures and
approaches to managing content states. This has important implications:

**Switching versioning packages on an existing project is difficult.** While possible,
the process typically requires uninstalling the current package (leaving an unversioned
django CMS installation), then installing the new package and creating its required
data structures. This migration may result in data loss—for example, archived versions
or version history would not transfer between incompatible systems.

**The versioning package affects all content types using the contract.** Packages like
`djangocms-alias <https://github.com/django-cms/djangocms-alias>`_ consume the
versioning contract, meaning your choice of versioning package determines how *all*
versioned content behaves across your site—not just pages.

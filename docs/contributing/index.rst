#######################
Development & community
#######################

django CMS is an open-source project, and relies on its community of users to
keep getting better.

.. toctree::
    :maxdepth: 1

    development
    code
    documentation
    translations
    management
    testing
    code_of_conduct


..  _community-resources:


*********
Community
*********

You can join us online:

* in our IRC channel, #django-cms, on ``irc.freenode.net``. If you don't have an IRC client, you can
  `join our IRC channel using the KiwiIRC web client
  <https://kiwiirc.com/client/irc.freenode.net/django-cms>`_, which works pretty well.
* on our `django CMS users email list <https://groups.google.com/forum/#!forum/django-cms>`_ for
  **general** django CMS questions and discussion
* on our `django CMS developers email list
  <https://groups.google.com/forum/#!forum/django-cms-developers>`_ for discussions about the
  **development of django CMS**

You can also follow:

* the `Travis Continuous Integration build reports <https://travis-ci.org/divio/django-cms>`_
* the `@djangocms`_ Twitter account for general announcements

You don't need to be an expert developer to make a valuable contribution - all
you need is a little knowledge of the system, and a willingness to follow the
contribution guidelines.

Remember that contributions to the documentation are highly prized, and key to
the success of the django CMS project.

Development is led by a team of **core developers**, and under the overall
guidance of a **technical board**.

All activity in the community is governed by our :doc:`code_of_conduct`.


***************
Security issues
***************

.. ATTENTION::

    If you think you have discovered a security issue in our code, please report
    it **privately**, by emailing us at `security@django-cms.org`_.

        Please **do not** raise it on:

        * IRC
        * GitHub
        * either of our email lists

        or in any other public forum until we have had a chance to deal with it.


.. _development_policies:

********************
Development policies
********************

Release schedule & policy
=========================

The `roadmap <https://github.com/divio/django-cms/wiki/Roadmap>`_ can be found on our GitHub wiki
page.

We are planning releases according to **key principles and aims**. Issues within milestones are
therefore subject to change.

The `django-cms-developers`_ group serves as gathering point for developers. We submit
ideas and proposals prior to the roadmap goals.

We officially support the **current** and **previous** released versions of django CMS. Older
versions are maintained through the community. Divio provides long term support (LTS) through
`commercial support <http://divio.ch/en/commercial-support/>`_.


.. _branch_policy:

Branch policy
=============

.. versionchanged:: 3.3

We maintain a number of branches on `our GitHub repository <https://github.com/divio/django-cms>`_.

the latest (highest-numbered) ``release/x.y.z``
    This is the branch that will become the next release on PyPI.

    **Fixes and backwards-compatible improvements** (i.e. most pull requests) will be made against
    this branch.

``develop``
    This is the branch that will become the next release that increments the ``x`` or ``y`` of the latest
    ``release/x.y.z``.

    This branch is for **new features and backwards-incompatible changes**. By their nature, these will require more
    substantial team co-ordination.

Older ``release/x.y.z`` branches
     These represent the final point of development (the highest ``y`` of older versions). Releases in the full set of
     older versions have been tagged (use Git Tags to retrieve them).

     These branches will only rarely be patched, with security fixes representing the main reason for a patch.

Commits in ``release/x.y.z`` will be merged forward into ``develop`` periodically by the core developers.

If in doubt about which branch to work from, ask on the #django-cms IRC channel on `freenode`_ or the
`django-cms-developers`_ email list!


.. _commit_policy:

Commit policy
=============

.. versionadded:: 3.3

Commit messages
---------------

Commit messages and their subject lines should be written in the past tense, not present tense, for example:

    Updated contribution policies.

    * Updated branch policy to clarify purpose of develop/release branches
    * Added commit policy.
    * Added changelog policy.

Keep lines short, and within 72 characters as far as possible.


Squashing commits
-----------------

In order to make our Git history more useful, and to make life easier for the core developers, please rebase and
squash your commit history into a single commit representing a single coherent piece of work.

For example, we don't really need or want a commit history, for what ought to be a single commit, that looks like
(newest last)::

    2dceb83 Updated contribution policies.
    ffe5f2c Fixed spelling mistake in contribution policies.
    29168da Fixed typo.
    85d925c Updated commit policy based on feedback.

The bottom three commits are just noise. They don't represent development of the code base. The four commits
should be squashed into a single, meaningful, commit::

    85d925c Updated commit policy based on feedback.


How to squash commits
^^^^^^^^^^^^^^^^^^^^^

In this example above, you'd use ``git rebase -i HEAD~4`` (the ``4`` refers to the number of commits being squashed -
adjust it as required).

This will open a ``git-rebase-todo`` file (showing commits with the newest last)::

    pick 2dceb83 Updated contribution policies.
    pick ffe5f2c Fixed spelling mistake in contribution policies.
    pick 29168da Fixed typo.
    pick 85d925c Updated commit policy based on feedback.

"Fixup" the last three commits, using ``f`` so that they are squashed into the first, and their commit messages
discarded::

    pick 2dceb83 Updated contribution policies.
    f ffe5f2c Fixed spelling mistake in contribution policies.
    f 29168da Fixed typo.
    f 85d925c Updated commit policy based on feedback.

Save - and this will leave you with a single commit containing all of the changes::

    85d925c Updated commit policy based on feedback.

Ask for help if you run into trouble!


.. _changelog_policy:

Changelog policy
================

.. versionadded:: 3.3

**Every new feature, bugfix or other change of substance** must be represented in the `CHANGELOG
<https://github.com/divio/django-cms/blob/develop/CHANGELOG.txt>`_. This includes documentation, but **doesn't** extend
to things like reformatting code, tidying-up, correcting typos and so on.

Each line in the changelog should begin with a verb in the past tense, for example::

    * Added CMS_WIZARD_CONTENT_PLACEHOLDER setting
    * Renamed the CMS_WIZARD_* settings to CMS_PAGE_WIZARD_*
    * Deprecated the old-style wizard-related settings
    * Improved handling of uninstalled apphooks
    * Fixed an issue which could lead to an apphook without a slug
    * Updated contribution policies documentation

New lines should be added to the top of the list.


.. _security@django-cms.org: mailto:security@django-cms.org
.. _django-cms-developers: http://groups.google.com/group/django-cms-developers
.. _freenode: http://freenode.net/
.. _@djangocms: https://twitter.com/djangocms


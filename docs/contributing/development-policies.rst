.. _development_policies:

####################
Development policies
####################

.. _reporting_security_issues:

*************************
Reporting security issues
*************************

.. ATTENTION::

    If you think you have discovered a security issue in our code, please report
    it **privately**, by emailing us at `security@django-cms.org`_.

        Please **do not** raise it on:

        * IRC
        * GitHub
        * either of our email lists

        or in any other public forum until we have had a chance to deal with it.


******
Review
******

All patches should be made as pull requests to `the GitHub repository <https://github.com/divio/django-cms>`_. Patches
should never be pushed directly.

**Nothing** may enter the code-base, *including the documentation*, without proper review and formal approval from the
core team.

Reviews are welcomed by all members of the community. You don't need to be a core developer, or even an experienced
programmer, to contribute usefully to code review. Even noting that you don't understand something in a pull request
is valuable feedback and will be taken seriously.


Formal approval
===============

Formal approval means "OK to merge" comments, following review, from at least two different members of the core team
who have expertise in the relevant areas, and excluding the author of the pull request.

The exceptions to this are frontend code and documentation, where one "OK to merge" comment will suffice, at least
until the team has more expert developers in those areas.


**********************************************
Proposal and discussion of significant changes
**********************************************

New features and backward-incompatible changes should be proposed using the `django CMS developers email list
<https://groups.google.com/group/django-cms-developers>`_. Discussion should take place there before any pull requests
are made.

This is in the interests of openness and transparency, and to give the community a chance to participate in and
understand the decisions taken by the project.


****************
Release schedule
****************

The `roadmap <https://www.django-cms.org/en/roadmap/>`_ can be found on our website.

We are planning releases according to **key principles and aims**. Issues within milestones are
therefore subject to change.

The `django CMS developers email list <https://groups.google.com/group/django-cms-developers>`_ serves as gathering
point for developers. We submit ideas and proposals prior to the roadmap goals.

django CMS 3.4 will be the first "LTS" ("Long-Term Support") release of the application. *Long-term support* means that
this version will continue to receive security and other critical updates for 24 months after its first release.

Any updates it does receive will be backward-compatible and will not alter functional behaviour. This means that users
can deploy this version confident that keeping it up-to-date requires only easily-applied security and other critical
updates, until the next LTS release.


.. _branch_policy:

********
Branches
********

..  versionchanged:: 3.3

    Previously, we maintained a ``master`` branch (now deleted), and a set of ``support`` branches (now pruned, and
    renamed ``release``).

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

*******
Commits
*******

.. versionadded:: 3.3

Commit messages
===============

Commit messages and their subject lines should be written in the past tense, not present tense, for example:

    Updated contribution policies.

    * Updated branch policy to clarify purpose of develop/release branches
    * Added commit policy.
    * Added changelog policy.

Keep lines short, and within 72 characters as far as possible.


Squashing commits
=================

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

    85d925c Updated contribution policies.


How to squash commits
---------------------

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

    85d925c Updated contribution policies.

Ask for help if you run into trouble!


.. _changelog_policy:

*********
Changelog
*********

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
.. _django-cms-developers: https://groups.google.com/group/django-cms-developers
.. _freenode: http://freenode.net/

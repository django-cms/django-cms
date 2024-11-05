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
    it **privately**, by emailing us at `security@django-cms.org <security@django-cms.org>`_.

    Please **do not** raise it in any public forum until we have had a
    chance to deal with it.


******
Review
******

All patches should be made as pull requests **against develop-4** to
`the GitHub repository <https://github.com/django-cms/django-cms>`_. Patches should
never be pushed directly.

**Nothing** may enter the code-base, *including the documentation*, without
proper review and formal approval from the core team.

Reviews are welcomed by all members of the community. You don't need to be a core developer, or even an experienced
programmer, to contribute usefully to code review. Even noting that you don't understand something in a pull request
is valuable feedback and will be taken seriously.


Formal approval
===============

Formal approval means "OK to merge" comments, following review, from at least
one member of the core team who has expertise in the relevant areas, and excluding
the author of the pull request.


**********************************************
Proposal and discussion of significant changes
**********************************************

New features and backward-incompatible changes should follow the best practice of `DEPS <https://github.com/django/deps>`_ and
should be discussed in the community first. After your proposal has been reviewed by the community,
it needs to be finally approved by the `Tech Committee <https://github.com/django-cms/django-cms-mgmt/blob/master/tech-committee/about.md>`_.
This is in the interests of openness and transparency,
and to give the community a chance to participate in and understand the decisions taken by the project.

So before submitting pull requests with significant changes, please make sure that the community agrees and the
Technical Committee approves.


To create a proposal...

1. please use this `DEP template <https://github.com/django/deps/blob/main/template.rst>`_
2. create a discussion in the main `Github repository <https://github.com/django-cms/django-cms/discussions>`_
3. discuss, discuss, discuss
4. join the Tech Committee (`#technical-committee <https://discord-tech-committee-channel.django-cms.org>`_) and make the team aware of your proposal after the proposal has been reviewed by the Technical Committee, it is put to a vote at one of the weekly meetings of the technical committee


****************
Release schedule
****************

The `roadmap <https://www.django-cms.org/en/roadmap/>`_ can be found on our website. The release schedule is
managed by the release management workgroup. The plan is to release quarterly and according to a retrospective approach.

Example of retrospective approach.

* Q1 2021 -> 3.9 Release
* End of Q1 2021 -> freeze
* Check what’s available
* Merge in anything that’s been approved
* Q2 2021 Release -> 3.10
* ...
* Unscheduled Releases -> e.g. bug fix -> 3.x.x

Release management is managed on `Discord <https://discord-tech-committee-channel.django-cms.org>`_ in the #technical-committee channel.
For questions regarding the release process please join the channel and reach out. We're happy to help.

Long-Term Support Release
===========================

For the current Long-Term Support (LTS) release overview see :ref:`here <LTS>`. *Long-term
support* means that this version will continue to receive security and other
critical updates in alignment with the corresponding Django LTS release.

Any updates it does receive will be backward-compatible and will not alter functional behaviour. This means that users
can deploy this version confident that keeping it up-to-date requires only easily-applied security and other critical
updates, until the next LTS release.


.. _branch_policy:

********
Branches
********

We maintain a number of branches on
`our GitHub repository <https://github.com/django-cms/django-cms>`_:

``develop-4``
    The default target branch for on-going development and new pull requests.

``release/x.y.z`` are the latest released versions of django CMS. Commits
    are cherry-picked from ``develop-4`` and merged into ``release/x.y.z``
    when suitable. We **officially support** the latest, highest released version
    and the latest LTS.

Please always open PR's against ``develop-4`` and indicate that they should be
backported to the latest LTS release when necessary. Older branches are not
supported any longer.


.. _commit_policy:

*******
Commits
*******

Commit messages
===============

We follow the `Conventional Commits
<https://www.conventionalcommits.org>`_ specification for commit messages.
Pull requests are linted against this specification so please make your PR title
match the specification.

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

**Every new feature, bugfix or other change of substance** must be represented in the `CHANGELOG
<https://github.com/django-cms/django-cms/blob/develop/CHANGELOG.rst>`_. This includes documentation, but **doesn't** extend
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

.. _management:

###########################
Code and project management
###########################

We use our `GitHub project <https://github.com/divio/django-cms>`_ for managing both django CMS code
and development activity.

This document describes how we manage tickets on GitHub. By "tickets", we mean GitHub issues and
pull requests (in fact as far as GitHub is concerned, pull requests are simply a species of issue).

******
Issues
******

Raising an issue
================

.. ATTENTION::

    If you think you have discovered a security issue in our code, please report
    it **privately**, by emailing us at `security@django-cms.org`_.

        Please **do not** raise it on:

        * IRC
        * GitHub
        * either of our email lists

        or in any other public forum until we have had a chance to deal with it.

Except in the case of security matters, of course, you're welcome to raise issues in any way that
suits you - :ref:`on one of our email lists, or the IRC channel <development-community>` or in person
if you happen to meet another django CMS developer.

It's very helpful though if you don't just raise an issue by mentioning it to people, but actually
file it too, and that means creating a `new issue on GitHub
<https://github.com/divio/django-cms/issues/new>`_.

There's an art to creating a good issue report.

The *Title* needs to be both succinct and informative. "show_sub_menu displays incorrect nodes when
used with soft_root" is helpful, whereas "Menus are broken" is not.

In the *Description* of your report, we'd like to see:

* how to reproduce the problem
* what you expected to happen
* what did happen (a traceback is often helpful, if you get one)

Getting your issue accepted
===========================

Other django CMS developers will see your issue, and will be able to comment. A core developer may
add further comments, or a :ref:`label <label-reference>`.

The important thing at this stage is to have your issue *accepted*. This means that we've agreed
it's a genuine issue, and represents something we can or are willing to do in the CMS.

You may be asked for more information before it's accepted, and there may be some discussion before
it is. It could also be rejected as a :term:`non-issue` (it's not actually a problem) or
:term:`won't fix` (addressing your issue is beyond the scope of the project, or is incompatible
with our other aims).

Feel free to explain why you think a decision to reject your issue is incorrect - very few
decisions are final, and we're always happy to correct our mistakes.

**********************
How we process tickets
**********************

Tickets should be:

* given a :ref:`status <label-status>`
* marked with :ref:`needs <label-need>`
* marked with a kind
* marked with the components they apply to
* marked with :ref:`miscellaneous other labels <label-others>`
* commented

A ticket's *status* and *needs* are the most important of these. They tell us two key things:

* *status*: what stage the ticket is at
* *needs*: what next actions are required to move it forward

Needless to say, these labels need to be applied carefully, according to the rules of this system.

GitHub's interface means that we have no alternative but to use colours to help identify our
tickets. We're sorry about this. We've tried to use colours that will cause the fewest issues for
colour-blind people, so we don't use green (since we use red) or yellow (since we use blue) labels,
but we are aware it's not ideal.

django CMS ticket processing system rules
=========================================

* one and only one status **must** be applied to each ticket
* a healthy ticket (blue) **cannot** have any :ref:`critical needs <label-need-critical>` (red)
* when closed, tickets **must** have either a healthy (blue) or dead (black) status
* a ticket with :ref:`critical needs <label-need-critical>` **must not** have :ref:`non-critical
  needs <label-need-non-critical>` or :ref:`miscellaneous other <label-others>` labels
* :term:`has patch` and :term:`on hold` labels imply a related pull request, which **must** be
  linked-to when these labels are applied
* *component*, :ref:`non-critical need <label-need-non-critical>` and :ref:`miscellaneous other
  <label-others>` labels should be applied as seems appropriate

Status
======

The first thing we do is decide whether we accept the ticket, whether it's a pull request or an
issue. An accepted status means the ticket is healthy, and will have a blue label.

Basically, it's good for open tickets to be healthy (blue), because that means they are going
somewhere.

.. IMPORTANT::
   Accepting a ticket means marking it as healthy, with one of the blue labels.

    issues
        The bar for :term:`status: accepted <accepted>` is high. The status can be revoked at any
        time, and should be when appropriate. If the issue needs a :term:`design decision`,
        :term:`expert opinion` or :term:`more info`, it can't be *accepted*.

    pull requests
        When a pull request is accepted, it should become :term:`work in progress` or (more rarely)
        :term:`ready for review` or even :term:`ready to be merged`, in those rare cases where a
        perfectly-formed and unimprovable pull request lands in our laps. As for issues, if it
        needs a :term:`design decision`, :term:`expert opinion` or :term:`more info`, it can't be
        accepted.

        **No issue or pull request can have both a blue (accepted) and a red, grey or black label
        at the same time.**

Preferably, the ticket should either be accepted (blue), rejected (black) or marked as having
critical needs (red) *as soon as possible*. It's important that open tickets should have a clear
status, not least for the sake of the person who submitted it so that they know it's being assessed.

Tickets should not be allowed to linger indefinitely with critical (red) needs. If the opinions or
information required to accept the ticket are not forthcoming, the ticket should be declared
unhealthy (grey) with :term:`marked for rejection` and rejected (black) at the next release.

Needs
=====

Critical needs (red) affect status.

:ref:`label-need-non-critical` labels (pink) can be added as appropriate (and of course, removed
as work progresses) to pull requests.

It's important that open tickets should have a clear needs labels, so that it's apparent what needs
to be done to make progress with it.

Kinds and components
====================

Of necessity, these are somewhat porous categories. For example, it's not always absolutely clear
whether a pull request represents an enhancement or a bug-fix, and tickets can apply to multiple
parts of the CMS - so do the best you can with them.

Other labels
============

:term:`backport`, :term:`blocker`, :term:`has patch` or :term:`easy pickings` labels should be applied as appropriate, to healthy (blue) tickets only.

Comments
========

At any time, people can comment on the ticket, of course. Although only core maintainers can change
labels, anyone can suggest changing a label.

..  _label-reference:

***************
Label reference
***************

*Components* and *kinds* should be self-explanatory, but :ref:`statuses <label-status>`,
:ref:`needs <label-need>` and :ref:`miscellaneous other labels <label-others>` are clarified below.

..  _label-status:

Statuses
========

A ticket's *status* is its position in the pipeline - its point in our workflow.

Every issue should have a status, and be given one as soon as possible. **An issue should have only
one status applied to it**.

Many of these statuses apply equally well to both issues and pull requests, but some make sense
only for one or the other:

.. glossary::

    accepted
        (issues only) The issue has been accepted as a genuine issue that needs to be addressed.
        Note that it doesn't necessarily mean we will do what the issue suggests, if it makes a
        suggestion - simply that we agree that there is an issue to be resolved.

    non-issue
        The issue or pull request are in some way mistaken - the 'problem' is in fact correct and
        expected behaviour, or the problems were caused by (for example) misconfiguration.

        When this label is applied, an explanation must be provided in a comment.

    won't fix
        The issue or pull request imply changes to django CMS's design or behaviour that the core
        team consider incompatible with our chosen approach.

        When this label is applied, an explanation must be provided in a comment.

    marked for rejection
        We've been unable to reproduce the issue, and it has lain dormant for a long time. Or, it's
        a pull request of low significance that requires more work, and looks like it might have
        been abandoned. These tickets will be closed when we make the next release.

        When this label is applied, an explanation must be provided in a comment.

    work in progress
        (pull requests only) Work is on-going.

        The author of the pull request should include "(work in progress)" in its title, and remove
        this when they feel it's ready for final review.

    ready for review
        (pull requests only) The pull request needs to be reviewed. (Anyone can review and make
        comments recommending that it be merged (or indeed, any further action) but only a core
        maintainer can change the label.)

    ready to be merged
        (pull requests only) The pull request has successfully passed review. Core maintainers
        should not mark their own code, except in the simplest of cases, as *ready to be merged*,
        nor should they mark any code as *ready to be merged* and then merge it themselves - there
        should be another person involved in the process.

        When the pull request is merged, the label should be removed.

..  _label-need:

Needs
=====

If an issue or pull request lacks something that needs to be provided for it to progress further,
this should be marked with a "needs" label. A "needs" label indicates an *action* that should
be taken in order to advance the item's status.

..  _label-need-critical:

Critical needs
--------------

*Critical needs* (red) mean that a ticket is 'unhealthy' and won't be :term:`accepted`
(issues) or :term:`work in progress`, :term:`ready for review` or :term:`ready to be merged` until
those needs are addressed. In other words, no ticket can have both a blue and a red label.)

.. glossary::

    more info
        Not enough information has been provided to allow us to proceed, for example to reproduce a
        bug or to explain the purpose of a pull request.

    expert opinion
        The issue or pull request presents a technical problem that needs to be looked at by a
        member of the core maintenance team who has a special insight into that particular aspect
        of the system.

    design decision
        The issue or pull request has deeper implications for the CMS, that need to be considered
        carefully before we can proceed further.

..  _label-need-non-critical:

Non-critical needs
------------------

A healthy (blue) ticket can have non-critical needs:

.. glossary::

    patch
        (issues only) The issue has been given a *status: accepted*, but now someone needs to write
        the patch to address it.

    tests
    docs
        (pull requests only) Code without docs or tests?! In django CMS? No way!

..  _label-others:

Other
=====

.. glossary::

    has patch
        (issues only) A patch intended to address the issue exists. This doesn't imply that the
        patch will be accepted, or even that it contains a viable solution.

        When this label is applied, a comment should cross-reference the pull request(s) containing
        the patch.

    easy pickings
        An easy-to-fix issue, or an easy-to-review pull request - newcomers to django CMS
        development are encouraged to tackle *easy pickings* tickets.

    blocker
        We can't make the next release without resolving this issue.

    backport
        Any patch will should be backported to a previous release, either because it has security
        implications or it improves documentation.

    on hold
        (pull requests only) The pull request has to wait for a higher-priority pull request to land
        first, to avoid complex merges or extra work later. Any *on hold* pull request is by
        definition :term:`work in progress`.

        When this label is applied, a comment should cross-reference the other pull request(s).

.. _security@django-cms.org: mailto:security@django-cms.org

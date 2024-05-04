
Guidelines for django CMS projects
==================================

.. note::

    These guidelines are based on the best practice established by the Jazzband project,
    a community of contributors that shares the responsibility of maintaining
    Python-based projects.

The django CMS ecosystem consists of many custom projects. Often these projects are
maintained by the author themselves. However, sometimes it can make sense to put a
project in the care of the django CMS project. Either because it is of interest to the
entire community, or because the author can no longer devote time to maintain the
project themselves.

Whether an existing project is transferred to the django CMS Github organization, or a
new project is set up within the django CMS Github organization, it is important that
certain standards are followed.

Acceptance criteria for new projects or existing ones
-----------------------------------------------------

Projects must meet the criteria of viability, documentation, testing, code of conducts
and contributing guidelines. But before that, they must be approved by the Tech
Committee.

Approval by Tech Committee of the django CMS Association
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

New projects or project transfers under the django CMS patronage must first be approved
by the `Tech Committee
<https://github.com/django-cms/django-cms-mgmt/blob/master/tech-committee/about.md>`_.
For that you should join the #tech-committee channel on `Discord
<https://discord-tech-committee-channel.django-cms.org>`_ and simply submit your proposal. Then, the TC
decides whether or not your project is in line with the product roadmap and overall
vision for django CMS.

Viability
~~~~~~~~~

Projects to be maintained by the django CMS project must have a certain maturity (No
proof of concepts, one-off toys or code snippet hosts) and provide useful functionality.
They should also be transferred to django CMS with the agreement of the previous
maintainer and in consultation with the Tech Committee (see `Tech Committee
<https://github.com/django-cms/django-cms-mgmt/blob/master/tech-committee/about.md>`_).

Documentation
~~~~~~~~~~~~~

Project documentation is one of the most important aspects of a project. For this
reason, it is of utmost importance that the project includes prose documentation for end
users and contributors. It is also strongly recommended to prepare inline code
documentation, as this is considered an indicator of high quality code. Please document
as much as possible, but also as clearly and concisely as possible. To quote `Jazzband
<https://jazzband.co/about/guidelines>`_ “Write like you’re addressing yourself in a few
years.” More information about how to contribute software documentation can be found
`here <https://docs.django-cms.org/en/latest/contributing/documentation.html>`_.

Tests
~~~~~

Your contributions and fixes are more than welcome as are your tests. We do not want to
compromise our codebase. Therefore, you are going to have to include tests if you want
to contribute. For more information about running and writing tests please `see here
<https://docs.django-cms.org/en/latest/contributing/testing.html>`_.

Conduct
~~~~~~~

Projects are required to adopt and follow the django CMS `code of conduct
<https://docs.django-cms.org/en/latest/contributing/code_of_conduct.html>`_. Please see
the Contributor Code of Conduct for more information about what that entails and how to
report conduct violations.

Contributing Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

Projects have to add a CONTRIBUTING.md ( `Markdown
<https://daringfireball.net/projects/markdown/syntax>`_ ) or CONTRIBUTING.rst (
`reStructuredText <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html>`_
) file to their repository so it’s automatically displayed when new issues and pull
requests are created.

The respective file needs to contain this text:

First of all, thank you for wanting to contribute to the django CMS. We always welcome
contributions, like many other open-source projects. We are very thankful to the many
`present, past and future contributors
<https://github.com/django-cms/django-cms/graphs/contributors>`_, to our `community
heroes
<https://github.com/django-cms/django-cms-mgmt/blob/master/community%20heros/list%20of%20community%20heros.md>`_
and to the [members of the `django CMS Association
<https://github.com/django-cms/django-cms-mgmt/blob/master/association/members.md>`_.
This is a `django CMS <https://www.django-cms.org>`_ project. By contributing you agree
to abide by the `Contributor Code of Conduct
<https://docs.django-cms.org/en/latest/contributing/code_of_conduct.html>`_ and follow
the `guidelines <https://docs.django-cms.org/en/latest/contributing/index.html>`_. Of
course extending the contributing document with your project’s contributing guide is
highly encouraged, too. See GitHub’s documentation on contributing guidelines for more
information.

Move an existing project to the django CMS Github organization
--------------------------------------------------------------

To initiate the transfer to django CMS, you should use Github’s `Transfer Feature
<https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository>`_
to transfer the repository to the django CMS organization.

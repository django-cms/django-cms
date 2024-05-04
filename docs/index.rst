.. raw:: html

    <style>
        .row {
           clear: both;
        }

        .column img {border: 1px solid gray;}

        @media only screen and (min-width: 1000px),
               only screen and (min-width: 500px) and (max-width: 768px){

            .column {
                padding-left: 5px;
                padding-right: 5px;
                float: left;
            }

            .column3  {
                width: calc(33.3% - 10px);
            }

            .column2  {
                width: calc(50% - 11px);
                position: relative;
            }
            .column2:before {
                padding-top: 61.8%;
                content: "";
                display: block;
                float: left;
            }
            .top-left {
                border-right: 1px solid var(--color-background-border);
                border-bottom: 1px solid var(--color-background-border);
            }
            .top-right {
                border-bottom: 1px solid var(--color-background-border);
            }
            .bottom-left {
                border-right: 1px solid var(--color-background-border);
            }
        }
    </style>

django CMS documentation
========================

.. image:: /images/django-cms-logo.png
    :alt: django CMS logo

Philosophy
----------

The design philosophy of django CMS is to solve something complex with many simple
things.

The core of django CMS is designed to be simple and integrate with simple packages to
create complex applications. For example, you may add ``djangocms-versioning`` to manage
versions of your content, ``djangocms-moderation`` to define workflows for how content
moves from authoring to being published.

Overview
--------

django CMS is a modern web publishing platform built with Django_, the web application
framework "for perfectionists with deadlines".

django CMS offers out-of-the-box support for the common features you'd expect from a
CMS, but can also be easily customised and extended by developers to create a site that
is tailored to their precise needs.

This is the developer documentation. To get an overview on how to use django CMS, see
the `django CMS User Guide <https://user-guide.django-cms.org/>`_.

.. rst-class:: clearfix row

.. rst-class:: column column2 top-left

:ref:`tutorials`
~~~~~~~~~~~~~~~~

**Start here as a new django CMS developer**:

- installation
- using additional packages
- creating your own addon applications.

.. rst-class:: column column2 top-right

:ref:`how-to`
~~~~~~~~~~~~~

Practical **step-by-step guides** for the more experienced developer, covering several
important topics.

.. rst-class:: column column2 bottom-left

:ref:`explanation`
~~~~~~~~~~~~~~~~~~

Explanation and analysis of some key concepts in django CMS.

.. rst-class:: column column2 bottom-right

:ref:`reference`
~~~~~~~~~~~~~~~~

Technical reference material, for

- classes,
- methods,
- APIs,
- commands.

.. rst-class:: clearfix row

Join us online
--------------

The `django CMS Association <https://www.django-cms.org/en/about-us/>`_ is a non-profit
organisation that exists to support the development of django CMS and its community.

.. rst-class:: column column2

Discord
~~~~~

Join `our friendly Discord server <https://discord-support-channel.django-cms.org>`_ for **support** and
to **share ideas** and **discuss technical questions** with other members of the
community.

.. rst-class:: column column2

StackOverflow
~~~~~~~~~~~~~

`StackOverflow <https://stackoverflow.com/questions/tagged/django-cms>`_ is also a good
place for questions around django CMS and its plugin ecosystem.

.. rst-class:: row clearfix

Why django CMS?
---------------

django CMS is a well-tested CMS platform that powers sites both large and small. Here
are a few of the key features:

- robust internationalisation (i18n) support for creating multilingual sites
- front-end editing, providing rapid access to the content management interface
- support for a variety of editors with advanced text editing features.
- a flexible plugin system that lets developers put powerful tools at the fingertips of
  editors, without overwhelming them with a difficult interface
- ...and much more

There are other capable Django-based CMS platforms, but here's why you should consider
django CMS:

- thorough documentation
- easy and comprehensive integration into existing projects - django CMS isn't a
  monolithic application
- a healthy, active and supportive developer community
- a strong culture of good code, including an emphasis on automated testing

.. _requirements:

Software version requirements and release notes
-----------------------------------------------

This document refers to version |release|.

Long-term support (LTS)
~~~~~~~~~~~~~~~~~~~~~~~

Django has a `long-term support (LTS)
<https://www.djangoproject.com/download/#supported-versions>`_ policy which django CMS
adapts.

Designated django CMS versions receive support for use with official Django LTS
versions:

Current LTS table
+++++++++++++++++

========== ============== ====== ========================
django CMS Feature freeze Django End of long-term support
========== ============== ====== ========================
4.1 x      tbd            4.2    April 2026
\          \              3.2    April 2024
3.11.x     September 2023 4.2    April 2026
\          \              3.2    April 2024
========== ============== ====== ========================

After feature freeze, new features go into the next major version of django CMS.

Unsupported LTS versions
++++++++++++++++++++++++

The following LTS versions **do not** receive any support any more:

========== ============== ====== ========================
django CMS Feature freeze Django End of long-term support
========== ============== ====== ========================
3.8 x      June 2020      2.2    April 2022
3.7.x      October 2020   2.2    March 2022
\          \              1.11   March 2020
========== ============== ====== ========================

Django/Python compatibility table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*LTS* in the table indicates a combination of Django and django CMS *both* covered by a
long-term support policy.

*✓* indicates that the version has been tested and works. *×* indicates that it has not
been tested, or is known to be incompatible.

.. include:: compatibility.include

.. _django: https://www.djangoproject.com

.. _python: https://www.python.org

See the repository's ``setup.cfg`` for details of dependencies, or the
:ref:`release-notes` for information about what is required or has changed in particular
versions of the CMS.

The :ref:`Commonly Used Plugin section <commonly-used-plugins>` provides an overview of
other packages required in a django CMS project.

.. toctree::
    :maxdepth: 2
    :hidden:

    introduction/index
    explanation/index
    how_to/index
    reference/index
    upgrade/index
    contributing/index
    whoisbehind/index

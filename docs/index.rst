.. raw:: html

    <style>
        .row {clear: both}
        .row h2  {border-bottom: 1px solid gray;}

        .column img {border: 1px solid gray;}

        @media only screen and (min-width: 1000px),
               only screen and (min-width: 500px) and (max-width: 768px){

            .column {
                padding-left: 5px;
                padding-right: 5px;
                float: left;
            }

            .column3  {
                width: 33.3%;
            }

            .column2  {
                width: 50%;
            }
        }
    </style>


########################
django CMS documentation
########################

.. image:: /images/django-cms-logo.png
   :alt: django CMS logo

********
Overview
********

django CMS is a modern web publishing platform built with `Django`_, the web application framework "for
perfectionists with deadlines".

django CMS offers out-of-the-box support for the common features you'd expect
from a CMS, but can also be easily customised and extended by developers to
create a site that is tailored to their precise needs.


.. rst-class:: clearfix row

.. rst-class:: column column2

:ref:`tutorials` - start here
=============================

For the new django CMS developer, from installation to creating your own addon applications.

.. rst-class:: column column2

:ref:`how-to`
=============

Practical step-by-step guides for the more experienced developer, covering several important topics.

.. rst-class:: column column2

:ref:`key-topics`
=================

Explanation and analysis of some key concepts in django CMS.

.. rst-class:: column column2

:ref:`reference`
================

Technical reference material, for classes, methods, APIs, commands.



.. rst-class:: clearfix row

**************
Join us online
**************

The `django CMS Association <https://www.django-cms.org/en/about-us/>`_ is a non-profit
organisation that exists to support the development of django CMS and its community.


.. rst-class:: column column3

Slack
=====

Join `our friendly Slack group <https://www.django-cms.org/slack>`_ for
**support** and to **share ideas** and **discuss technical questions** with
other members of the community.


.. rst-class:: column column3

Discourse
=========

Our `Discourse forum <https://discourse.django-cms.org>`_ is also used for
discussion of django CMS, particularly to manage its technical development process.


.. rst-class:: column column3

StackOverflow
=============

`StackOverflow <https://stackoverflow.com/questions/tagged/django-cms>`_ is also a good place
for questions around django CMS and its plugin ecosystem.


***************
Why django CMS?
***************

django CMS is a well-tested CMS platform that powers sites both large and
small. Here are a few of the key features:

* robust internationalisation (i18n) support for creating multilingual sites
* front-end editing, providing rapid access to the content management interface
* support for a variety of editors with advanced text editing features.
* a flexible plugins system that lets developers put powerful tools at the
  fingertips of editors, without overwhelming them with a difficult interface

* ...and much more

There are other capable Django-based CMS platforms but here's why you should
consider django CMS:

* thorough documentation
* easy and comprehensive integration into existing projects - django CMS isn't a monolithic application
* a healthy, active and supportive developer community
* a strong culture of good code, including an emphasis on automated testing


.. _requirements:

***********************************************
Software version requirements and release notes
***********************************************

This document refers to version |release|.


Django/Python compatibility table
=================================

*LTS* in the table indicates a combination of Django and django CMS *both* covered
by a long-term support policy.

*✓* indicates that the version has been tested and works. *×* indicates that it has not been tested, or
is known to be incompatible.

===========  ==== ==== === === === === ===  === === === === === === === === === ====
django CMS   Python                                  Django
-----------  -----------------------------  ----------------------------------------
\            3.11 3.10 3.9 3.8 3.7 3.6 3.5  4.2 4.1 4.0 3.2 3.1 3.0 2.2 2.1 2.0 1.11
===========  ==== ==== === === === === ===  === === === === === === === === === ====
4.1.x        ✓    ✓    ✓   ✓   ✓   ×   ×    ✓   ✓   ✓   ✓   ✓   ✓   ✓   ×   ×   ×
3.11.2       ✓    ✓    ✓   ✓   ✓   ×   ×    LTS ✓   ✓   LTS ×   ×   ×   ×   ×   ×
3.11.1       ✓    ✓    ✓   ✓   ✓   ×   ×    ×   ✓   ✓   LTS ×   ×   ×   ×   ×   ×
3.11.0       ✓    ✓    ✓   ✓   ✓   ×   ×    ×   ×   ✓   ✓   ×   ×   ×   ×   ×   ×
3.10.x       ×    ✓    ✓   ✓   ✓   ×   ×    ×   ×   ×   ✓   ✓   ✓   ✓   ×   ×   ×
3.9.x        ×    ×    ✓   ✓   ✓   ✓   ×    ×   ×   ×   ✓   ✓   ✓   ✓   ×   ×   ×
3.8.x        ×    ×    ✓   ✓   ✓   ✓   ×    ×   ×   ×   ×   ✓   ✓   LTS ×   ×   ×
3.7.x        ×    ×    ✓   ✓   ✓   ✓   ✓    ×   ×   ×   ×   ×   ✓   LTS ✓   ✓   LTS
3.6.x        ×    ×    ×   ✓   ✓   ✓   ✓    ×   ×   ×   ×   ×   ×   ✓   ✓   ✓   ✓
3.5.x        ×    ×    ×   ✓   ✓   ✓   ✓    ×   ×   ×   ×   ×   ×   ×   ×   ×   ✓
3.4.5        ×    ×    ×   ×   ✓   ✓   ✓    ×   ×   ×   ×   ×   ×   ×   ×   ×   LTS
===========  ==== ==== === === === === ===  === === === === === === === === === ====


.. _Python: https://www.python.org
.. _Django: https://www.djangoproject.com


See the repository's ``setup.py`` for more specific details of dependencies, or the :ref:`release-notes` for
information about what is required or has changed in particular versions of the CMS.

The :ref:`installation how-to guide <installation>` provides an overview of other packages required in a django CMS
project.


.. toctree::
    :maxdepth: 2
    :hidden:

    introduction/index
    how_to/index
    reference/index
    topics/index
    contributing/index
    upgrade/index
    whoisbehind/index

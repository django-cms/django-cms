##########################
Contributing to django CMS
##########################

Like every open-source project, django CMS is always looking for motivated
individuals to contribute to its source code. However, to ensure the highest
code quality and keep the repository nice and tidy, everybody has to follow a
few rules (nothing major, I promise :) )


.. ATTENTION::

    If you think you have discovered a security issue in our code, please report
    it **privately**, by emailing us at `security@django-cms.org`_.
    
        Please don't raise it on:
    
        * IRC
        * GitHub
        * either of our email lists

        or in any other public forum until we have had a chance to deal with it. 


*********
Community
*********

People interested in developing for the django CMS should join the
`django-cms-developers`_ mailing list as well as heading over to #django-cms on
the `freenode`_ IRC network for help and to discuss the development.

You may also be interested in following `@djangocmsstatus`_ on twitter to get the
GitHub commits as well as the hudson build reports. There is also a `@djangocms`_
account for less technical announcements.


*************
In a nutshell
*************

Here's what the contribution process looks like, in a bullet-points fashion, and
only for the stuff we host on GitHub:

#. django CMS is hosted on `GitHub`_, at https://github.com/divio/django-cms
#. The best method to contribute back is to create an account there, then fork
   the project. You can use this fork as if it was your own project, and should
   push your changes to it.
#. When you feel your code is good enough for inclusion, "send us a `pull
   request`_", by using the nice GitHub web interface.



*****************
Contributing Code
*****************


Getting the source code
=======================

If you're interested in developing a new feature for the CMS, it is recommended
that you first discuss it on the `django-cms-developers`_  mailing list so as
not to do any work that will not get merged in anyway.

- Code will be reviewed and tested by at least one core developer, preferably
  by several. Other community members are welcome to give feedback.
- Code *must* be tested. Your pull request should include unit-tests (that cover
  the piece of code you're submitting, obviously)
- Documentation should reflect your changes if relevant. There is nothing worse
  than invalid documentation.
- Usually, if unit tests are written, pass, and your change is relevant, then
  it'll be merged.

Since we're hosted on GitHub, django CMS uses `git`_ as a version control system.

The `GitHub help`_ is very well written and will get you started on using git
and GitHub in a jiffy. It is an invaluable resource for newbies and old timers
alike.


Syntax and conventions
======================

We try to conform to `PEP8`_ as much as possible. A few highlights:

- Indentation should be exactly 4 spaces. Not 2, not 6, not 8. **4**. Also, tabs
  are evil.
- We try (loosely) to keep the line length at 79 characters. Generally the rule
  is "it should look good in a terminal-base editor" (eg vim), but we try not be
  [Godwin's law] about it.


Process
=======

This is how you fix a bug or add a feature:

#. `fork`_ us on GitHub.
#. Checkout your fork.
#. *Hack hack hack*, *test test test*, *commit commit commit*, test again.
#. Push to your fork.
#. Open a pull request.

And at any point in that process, you can add: *discuss discuss discuss*,
because it's always useful for everyone to pass ideas around and look at thngs
together.

:ref:`testing` is really important.

We have an IRC channel, our `django-cms-developers`_ email list,
and of course the code reviews mechanism on GitHub - do use them.


**************************
Contributing Documentation
**************************

Perhaps considered "boring" by hard-core coders, documentation is sometimes even
more important than code! This is what brings fresh blood to a project, and
serves as a reference for old timers. On top of this, documentation is the one
area where less technical people can help most - you just need to write
semi-decent English. People need to understand you. We don't care about style or
correctness.

Documentation should be:

- We use `Sphinx`_/`restructuredText`_. So obviously this is the format you should
  use :) File extensions should be .rst.
- Written in English. We could discuss how it would bring more people to the
  project by having a Klingon or some other translation, but that's a problem we
  will confront once we already have good documentation in English.
- Accessible. You should assume the reader to be moderately familiar with
  Python and Django, but not anything else. Link to documentation of libraries
  you use, for example, even if they are "obvious" to you (South is the first
  example that comes to mind - it's obvious to any Django programmer, but not to
  any newbie at all).
  A brief description of what it does is also welcome. 

Pulling of documentation is pretty fast and painless. Usually somebody goes over
your text and merges it, since there are no "breaks" and that GitHub parses rst
files automagically it's really convenient to work with.

Also, contributing to the documentation will earn you great respect from the
core developers. You get good karma just like a test contributor, but you get
double cookie points. Seriously. You rock.

Section style
=============

We use Python documentation conventions for section marking:

* ``#`` with overline, for parts
* ``*`` with overline, for chapters
* ``=``, for sections
* ``-``, for subsections
* ``^``, for subsubsections
* ``"``, for paragraphs


************
Translations
************


For translators we have a `Transifex account
<https://www.transifex.com/projects/p/django-cms/>`_ where you can translate
the .po files and don't need to install git or mercurial to be able to
contribute. All changes there will be automatically sent to the project.


    .. raw:: html

        Top translations django-cms core:<br/>

        <img border="0" src="https://www.transifex.com/projects/p/django-cms/resource/core/chart/image_png"/>



.. _security@django-cms.org: mailto:security@django-cms.org
.. _fork: http://github.com/divio/django-cms
.. _Sphinx: http://sphinx.pocoo.org/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _django-cms-developers: http://groups.google.com/group/django-cms-developers
.. _GitHub : http://www.github.com
.. _GitHub help : http://help.github.com
.. _freenode : http://freenode.net/
.. _@djangocmsstatus : https://twitter.com/djangocmsstatus
.. _@djangocms : https://twitter.com/djangocms
.. _pull request : http://help.github.com/send-pull-requests/
.. _git : http://git-scm.com/
.. _restructuredText: http://docutils.sourceforge.net/docs/ref/rst/introduction.html


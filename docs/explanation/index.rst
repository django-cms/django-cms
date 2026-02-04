.. _explanation:

Explanation
===========

This section explains the **design principles, concepts, and architectural
decisions** behind django CMS.

Rather than showing *how to perform specific tasks*, these pages focus on
*why django CMS works the way it does* and *how its core ideas shape the
system as a whole*. They are intended to provide context and understanding
that will help you make better design and implementation decisions in your
own projects.

At the centre of django CMS is a deliberate philosophy: complex publishing
requirements are best addressed through **small, composable building
blocks** rather than a single monolithic system. The pages in this section
explore how that philosophy is reflected throughout the CMS.

.. toctree::
   :maxdepth: 1

   philosophy
   plugins
   apphooks
   publishing
   multiple_languages
   i18n
   permissions
   menu_system
   frontend-integration
   commonly_used_plugins
   searchdocs
   touch
   colorscheme

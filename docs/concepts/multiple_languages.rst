#####################################
Serving content in multiple languages
#####################################

**************
Basic concepts
**************

django CMS has a sophisticated multilingual capability. It is able to serve
content in multiple languages, with fallbacks into other languages where
translations have not been provided. It also has the facility for the user to set the
preferred language and so on.

How django CMS determines the user's preferred language
=======================================================

django CMS determines the user's language based on (in order of priority):

* the language code prefix in the URL (but see :ref:`the_bug` below)
* the last language the user chose in the language chooser
* the language that the browser says its user prefers

How django CMS determines what language to serve
================================================

Once it has identified a user's language, it will try to accommodate it using the languages set in :setting:`CMS_LANGUAGES`.

If :setting:`CMS_LANGUAGE_FALLBACK` is True, and if the user's preferred
language is not available for that content, it will use the fallbacks
specified for the language in :setting:`CMS_LANGUAGE_CONF`.

What django CMS shows in your menus
===================================

If :setting:`CMS_HIDE_UNTRANSLATED` is ``True`` (the default) then pages that
aren't translated into the desired language will not appear in the menu.

*****************
Follow an example
*****************

It helps to understand how the system behaves by stepping through some actual
examples.

#. the situation:
    * your browser wants Italian content
    * the CMS is set up to provide content in English and Italian
    * :setting:`CMS_HIDE_UNTRANSLATED` is False
    * the page ``/some/page``

#. you visit ``/some/page``
    * the content is served in Italian
    * all link URLs (menus etc.) on that page will be prepended with /it
    * the page is served at ``/some/page`` (i.e. no redirection has taken place)

#. now you select one of those links ``/it/some/other/page`` that is available in Italian
    * Italian content is served
    * the page is served at ``/it/some/other/page``

#. now you select a link to a page **not** available in Italian
    * the link is still ``/it/some/other/page``
    * you'll get the English version, because Italian's not available
    * the path of the new page is ``/en/some/other/page`` (i.e. it has redirected)
    * some issues (see :ref:`the_bug` below)

    * all links on ``/en/some/other/page`` are prepended with ``/en`` - even if they are available in Italian
    * if you now visit ``/some/page`` or any other page without using a language prefix, you'll get content in English - even though your browser wants Italian

.. _the_bug:

*********************
Watch out for the bug
********************* 

What goes wrong
===============

As soon as you visit any page with a ``/en`` prefix in the path, the system
sets a ``django_language cookie`` (which will expire when the browser is quit)
with content "en".

From now on, the system thinks that you want English content.

Note that this could have happened:

* because you chose English in the language selector (good)
* because you arrived at a /en page from a search engine (possibly bad)
* because the page you wanted in Italian redirected you to an English one without warning or choice (bad)

.. note::
    This is an issue the developers are aware of and are working towards fixing.

What should happen
==================

Your language cookie should only ever get set or changed if:

* you choose a language in the language selector
* your browser has asked for a language (but this can't override your choice above)

If your cookie contains a particualar language (say, "it"):

* the content should be served in Italian wherever available
* links on a page should be to ``/it`` content where available, and fallback where not

When visiting a page only available in English:

* content will have to be in English
* links should be to Italian content where possible

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

django CMS determines the user's language the same way Django does it.

* the language code prefix in the URL
* the language set in the session
* the language in the language cookie
* the language that the browser says its user prefers

It uses the django built in capabilities for this.

By default no session and cookie are set. If you want to enable this use the
`cms.middleware.language.LanguageCookieMiddleware` to set the cookie on every request.


How django CMS determines what language to serve
================================================

Once it has identified a user's language, it will try to accommodate it using the languages set in :setting:`CMS_LANGUAGES`.

If :setting:`fallbacks` is set, and if the user's preferred
language is not available for that content, it will use the fallbacks
specified for the language in :setting:`CMS_LANGUAGES`.

What django CMS shows in your menus
===================================

If :setting:`hide_untranslated` is ``True`` (the default) then pages that
aren't translated into the desired language will not appear in the menu.

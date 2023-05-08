=========
Changelog
=========

3.11.3 (2023-04-25)
===================

Bug Fixes:
----------
* Remove superfluous curly bracket left behind on PR 7488 (#7529) -- Corentin Bettiol
* Fix admin tests (#6848) for some post requests (#7535) -- Fabian Braun

Statistics:
-----------

This release includes 2 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Corentin Bettiol (1 pull request)
* Fabian Braun (1 pull requests)

With the review help of the following contributors:

* Fabian Braun
* Vinit Kumar

Thanks to all contributors for their efforts!

3.11.2 (2023-04-18)
===================

Features:
---------
* add django 4.2 support (#7481) (5478faa5c) -- Vinit Kumar
* add setting to redirect slugs to lowercase (#7509) (01aedee9f) -- pajowu
* add setting so redirect preserves params (#7489) (dcb9c4b3a) -- Ivo Branco
* add download statistics to readme (#7474) (25b2303f7) -- Fabian Braun

Bug Fixes:
----------
* replace ' by ′ in fr translation − no more "page d\u0027accueil"! (#7488) (b4acc9a6b) -- Corentin Bettiol
* Link both user and group from global page permissions to change form (#7486) (6cb47629b) -- Fabian Braun
* Build docs always from the current local version (#7472) (#7475) (7aaddd45a) -- Fabian Braun

Statistics:
-----------

This release includes 21 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Corentin Bettiol (1 pull request)
* Danny Waser (1 pull request)
* Fabian Braun (10 pull requests)
* Ivo Branco (1 pull request)
* Jasper (1 pull request)
* Nihal Rahman (1 pull request)
* Vinit Kumar (3 pull requests)
* pajowu (1 pull request)

With the review help of the following contributors:

* Fabian Braun
* Nihal
* Vinit Kumar

Thanks to all contributors for their efforts!

3.11.1 (2022-12-12)
===================

Features:
---------
* add Python 3.11 support for Django CMS (#7422) (3fe1449e6) -- Vinit Kumar
* Support for Django 4.1 (#7404) (777864af3) -- Fabian Braun
* Add support for tel: and mailto: URIs in Advanced Page Settings redirect field (#7370) (0fd058ed3) -- Mark Walker
* Improved dutch translations -- Stefan van den Eertwegh

Bug Fixes:
----------
* Prefer titles matching request language (#7144) (06c9a85df) -- Micah Denbraver
* Adds a deprecation warning for SEND_BROKEN_LINK_EMAILS (#7420) (d38f4a1cc) -- Fabian Braun
* Added deprecation warning to `get_current_language()` (#7410) (2788f75e6) -- Mark Walker
* CMS check management command fixed [#7412] (#7413) (dcf394bd5) -- ton77v
* Changing color scheme resets session settings to defaults (#7407) (fcfe77f63) -- Fabian Braun
* Clear page permission cache on page create (#6866) (e59c179dd) -- G3RB3N
* Unlocalize page and node ids when rendering the page tree in the admin (#7188) (9e3c57946) -- Marco Bonetti
* Allow partially overriding CMS_CACHE_DURATIONS (#7339) (162ff8dd8) -- Qijia Liu
* CMS check management command fixed [#7386] (cdcf260aa) -- Marco Bonetti
* default light mode (#7381) (abc6e6c5b) -- viliammihalik
* Added language to page cache key (#7354) (d5a9f49e6) -- Mark Walker

Refactoring and Cleanups:
-------------------------
* Move js API functions to CMS.Helpers to make them available also to the admin site (#7384) (a7f8cd44f) -- Fabian Braun

Statistics:
-----------

This release  was created with the help of the following contributors (in alphabetical order):

* Fabian Braun
* G3RB3N
* Marco Benetti
* Mark Walker
* Micah Denbraver
* Qijia Liu
* Stefan van den Eertwegh
* villiammihalik
* Vinit Kumar


With the review help of the following contributors:

* Cage Johnson
* Christian Clauss
* Conrad
* Dapo Adedire
* Fabian Braun
* Florian Delizy
* G3RB3N
* Hussein Srour
* Marco Bonetti
* Mark Walker
* Micah Denbraver
* Pankrat
* Patrick Mazulo
* Qijia Liu
* Shivan Sivakumaran
* Simon Krull
* Vinit Kumar
* code-review-doctor
* dependabot[bot]
* fsbraun
* jefe
* ton77v
* viliammihalik
* wesleysima

Thanks to all contributors for their efforts!

3.11.0 (2022-08-02)
===================

Highlights:
-----------
* Support for django 4
* Dark mode support

Bug fixes:
----------

* Fix publishing of static placeholders outside of CMS pages
* Allow to override the template rendered after a plugin has been saved.
* Revert change to the toolbar sites menu to use ``http`` protocol.
* Fix edit plugin popup width (remove 850px width constraint).
* Fix except block using list instead of tuple. (#7334)
* Added spell checking to pre-commit and github workflows
* Added cache ttl extension point.
* Added current language to the page cache key (#6607)
* Fix isort line length to by in sync with flake8

3.10.1 (2022-06-28)
===================

Bug Fixes:
----------
* Changelog titles for 3.10.x (#7347) (31f399535) -- Mark Walker
* Request missing from test rendering (#7346) (eff54b0fd) -- Mark Walker
* Changelog title for 3.10.1rc1 (#7345) (966a90fd2) -- Mark Walker
* Revert change to the toolbar sites menu to use ``http`` protocol (#7332) (caddfe7f4) -- Mark Walker
* Fixed ``AttributeError`` (#7288) when the current toolbar object doesn't define ``get_draft_url()`` (#7289) -- Marco Bonetti
* Fix for django 2.2 in middleware [#7290] (#7293) -- Mark Walker
* Update release script to start bringing support for macOS (#7294) -- Mark Walker
* Fix release script version commit. (#7295) -- Mark Walker
* Revert change to the toolbar sites menu to use ``http`` protocol. (#7331) -- Mark Walker

Statistics:
-----------

This release includes 12 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Conrad (3 pull requests)
* Florian Delizy (1 pull request)
* Marco Bonetti (1 pull request)
* Mark Walker (7 pull requests)

Thanks to all contributors for their efforts!

3.10.0 (2022-03-26)
===================

Highlights:
-----------

This feature focuses on bringing python 3.10 support, bringing build system to latest nodejs, and bugfixes

Features:
---------
* python3.10 support (#7126) (324f08594) -- Vinit Kumar
* improve build performance (#7192) (bdb04bc31) -- Vinit Kumar

Bug Fixes:
----------
* using .nvmrc to target the right nvm version (3e5227def) -- Florian Delizy
* Add toolbar fix for broken CMS in the release 3.10.x -- Vinit Kumar
* fixing release script to use 'unreleased' (low caps) instead of mixed caps (#7202) (b7a793c88) -- Florian Delizy
* Cap django requirement at <4 (#7182) (c6c278497) -- Mark Walker
* Set the default_auto_field on the AppConfigs (#7181) (272d62ced) -- Jeffrey de Lange
* do not convert & URL query separator to &amp; (#7114) (c0c10e051) -- nichoski
* discrepancy around python 3.6 compatibility between `setup.py`, docs and tests (#7095) (70970061f) -- Mark Walker
* update permission cache when moving pages and adding pages. (#7090) (53dddb106) -- Ryo Shimada
* https://github.com/django-cms/django-cms/projects/6#card-63761457 (#7085) (a5159d3a6) -- Gabriel Andrade
* missing tests of django3.2 for mysql and sqlite (#7082) (c7fd7c0c5) -- Vinit Kumar
* Fixes #7033: also check for Django 3.2, now that 3.9 supports it. (#7054) (#7062) (f4043cd75) -- Vinit Kumar

Statistics:
-----------

This release includes 59 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Anatoliy (3 pull requests)
* Angelo Dini (1 pull request)
* Dmytro Litvinov (1 pull request)
* Florian Delizy (10 pull requests)
* Gabriel Andrade (1 pull request)
* Halit Çelik (1 pull request)
* Jean-Baptiste PENRATH (1 pull request)
* Jeffrey de Lange (1 pull request)
* Jens-Erik Weber (1 pull request)
* Kaushal Dhungel (1 pull request)
* Marco Bonetti (2 pull requests)
* Mark Walker (10 pull requests)
* Nebojsa Knezevic (2 pull requests)
* nichoski (2 pull requests)
* Nicolai (11 pull requests)
* Ryo Shimada (1 pull request)
* Simon Krull (4 pull requests)
* Stefan van den Eertwegh (1 pull request)
* Vinit Kumar (5 pull requests)

With the review help of the following contributors:

* fsbraun
* Gabriel Andrade
* Marco Bonetti
* Mark Walker
* Nicolai
* Simon Krull
* TiredFingers
* victor-yunenko
* Vinit Kumar

Thanks to all contributors for their efforts!

3.9.0 (2021-06-30)
==================

Highlights:
-----------

This release of django CMS (first community driven release) introduces support for Django 3.2, and bugfix.
We tried to catch up with as many long waited feature/bugfix requests as possible.

Features:
---------
* Add support for Django 3.2 LTS version
* Page changed_date added to the Page tree admin actions dropdown template #6701 (#7046) (73cbbdb00) -- Vladimir Kuvandjiev
* Allow recursive template extending in placeholders (#6564) (fed6fe54d) -- Stefan Wehrmeyer
* Added ability to set placeholder global limit on children only (#6847) (18e146495) -- G3RB3N
* Replaced Travis.CI with Github Actions (#7000) (0f33b5839) -- Vinit Kumar
* Added support for Github Actions based CI.
* Added Support for testing frontend, docs, test and linting in different/parallel CI pipelines.
* Added django-treebeard 4.5.1 support, previously pinned django-treebeard<4.5 to avoid breaking changes introduced
* Improved performance of ``cms list plugins`` command
* Page changed date added to the Page tree admin actions dropdown
* add django3.2 in the framework identifier for setup.py (#7081) (8ef90fefa) -- Vinit Kumar

Bug Fixes:
----------
* Fixed an issue where the wrong page title was returned (#6466) (3a0c4d26e) -- Alexandre Joly
* Fixed #6413: migrations 0019 and 0020 on multi db setups (#6708) (826d57f0f) -- Petr Glotov
* Added fix to migrations to handle multi database routing (#6721) (98658a909) -- Michael Anckaert
* Fixed issue where default fallbacks is not used when it's an empty list (#6795) (5d21fa5eb) -- Arjan de Pooter
* Fixed prefix_default_language = False redirect behavior (#6851) (34a26bd1b) -- Radek Stępień
* Fix not checking slug uniqueness on page move (#6958) (5976d393a) -- Iacopo Spalletti
* Fixed DontUsePageAttributeWarning message (#6734) (45383888e) -- carmenkow
* Fixed Cache not invalidated when using a PlaceholderField outside the CMS #6912 (#6956) (3ce63d7d3) -- Benjamin PIERRE
* Fixed unexpected behavior get_page_from_request (#6974) (#6073) (52f926e0d) -- Yuriy Mamaev
* Fixed django treebeard 4.5.1 compatibility (#6988) (eeb86fd70) -- Aiky30
* Fixed Bad Title.path in Multilanguage sites if parent slug is created or modified (#6968) (6e7b0ae48) -- fp4code
* Fixed redirect issues when i18n_patterns had prefix_default_language = False
* Fixed not checking slug uniqueness when moving a page
* Fixed builds on RTD
* Fixed the cache not being invalidated when updating a PlaceholderField in a custom model
* Fixed 66622 bad Title.path in multilingual sites when parent slug is created or modified
* Fixed 6973 bag with unexpected behavior ``get_page_from_request``
* Fixed migrations with multiple databases
* Fix styles issues, caused by switching to the ``display: flex`` on the page tree renderer.
* Fixed missing builtin arguments on main ``cms`` management command causing it to crash
* Fixed template label nested translation
* Fixed a bug where the fallback page title would be returned instead of the one from the current language
* Fixed an issue when running migrations on a multi database project
* Fixes #7033: also check for Django 3.2, now that 3.9 supports it. (#7054) (02083f2dc) -- Marco Bonetti

Refactoring and Cleanups:
-------------------------
* Remove unmaintained translations (#7039) (97ffa2481) -- Florian Delizy
* Remove debug print from apphook_reload
* Removed zh and zh_hans translation (keep zh_CN and zh_TW) -- Florian Delizy
* Cleaned-up unmaintained translations -- Florian Delizy
* Few changes in docs/contributing/code.rst
* Temporarily pinned django-treebeard to < 4.5, this avoids breaking changes introduced
* Updated documentation links
* documentation: Added an example of sqlite database configuration in documentation
* Repair broken docs link to users/index.rst

Internal Tools:
---------------
* adding django CMS release script (will be used starting 3.9.0 release) (#7036) (c95aacf14) -- Florian Delizy
* updating PR template and contribution guideline, no need to modify CHANGELOG.rst manually (#7041) (6c2b057c0) -- Florian Delizy
* Enforce use of coverage > 4 for python 3.8 support
* Fix all GitHub actions tests run on pull requests
* Remove travis integration from the project as the project has moved to Github Actions.
* Fixing release information and publish script (#7055) (0cfc42ba3) -- Florian Delizy

Statistics:
-----------

This release includes 89 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Abdur-Rahmaan Janhangeer (1 pull request)
* Aiky30 (3 pull requests)
* Alexandre Joly (1 pull request)
* Anatoliy (3 pull requests)
* Angelo Dini (3 pull requests)
* Arjan de Pooter (1 pull request)
* Benbb96 (1 pull request)
* Benjamin PIERRE (1 pull request)
* BrijeshVP (1 pull request)
* carmenkow (1 pull request)
* Daniele Procida (3 pull requests)
* Florian Delizy (19 pull requests)
* fp4code (3 pull requests)
* Frank (1 pull request)
* G3RB3N (1 pull request)
* greengoaxe (1 pull request)
* Iacopo Spalletti (3 pull requests)
* Jacob Rief (3 pull requests)
* Jean-Baptiste PENRATH (1 pull request)
* John Bazik (1 pull request)
* Marco Bonetti (1 pull request)
* Mark Walker (3 pull requests)
* Michael Anckaert (1 pull request)
* Munim Munna (2 pull requests)
* Nicolai (15 pull requests)
* Petr Glotov (1 pull request)
* Radek Stępień (1 pull request)
* Sebastian Weigand (2 pull requests)
* sin-ack (1 pull request)
* Stefan Wehrmeyer (1 pull request)
* victor-yunenko (1 pull request)
* Vinit Kumar (5 pull requests)
* Vladimir Kuvandjiev (1 pull request)
* Vytis Banaitis (1 pull request)
* Yuriy Mamaev (1 pull request)

With the review help of the following contributors:

* Aiky30
* Angelo Dini
* Benjamin PIERRE
* Daniele Procida
* Éric Araujo
* Florian Delizy
* Francesco Verde
* greengoaxe
* John Bazik
* Mario Colombo
* Mark Walker
* Nicolai
* Petr Glotov
* Radosław Stępień
* sin-ack
* Stuart Axon
* Vinit
* Vinit Kumar

Thanks to all contributors for their efforts!

3.8.0 (2020-10-28)
==================

* Introduced support for Django 3.1
* Dropped support for Python 2.7 and Python 3.4
* Dropped support for Django < 2.2
* Removed ``djangocms-column`` from the manual installation instructions
* Removed duplicate ``attr`` declaration from the documentation
* Fixed a reference to a wrong variable in log messages in ``utils/conf.py``
* Fixed an issue in ``wizards/create.html`` where the error message did not use the plural form
* Improved documentation building
* Updated the content for django CMS’s development community
* Replaced all occurrences of ``force_text`` and ``smart_text`` against
  ``force_str``and ``smart_str``.



3.7.4 (2020-07-21)
==================

* Fixed a security vulnerability in the plugin_type url parameter to insert JavaScript code.


3.7.3 (2020-05-27)
==================

* Fixed apphooks config select in Firefox
* Fixed compatibility errors on python 2
* Fixed long page titles in Page tree/list view to prevent horizontal scrolling
* Adapted plugin documentations


3.7.2 (2020-04-22)
==================

* Added support for Django 3.0
* Added support for Python 3.8
* migrated from ``django.utils.six`` to the six package
* migrated from ``django.utils.lru_cache`` to ``functools.lru_cache``
* migrated from ``render_to_response`` to ``render`` in ``cms.views``
* added ``cms.utils.compat.dj.available_attrs``
* added ``--force-color`` and ``--skip-checks`` in base commands when using Django 3
* replaced ``staticfiles`` and ``admin_static`` with ``static``
* replaced djangocms-helper with django-app-helper
* Added ability to set placeholder global limit on children only


3.7.1 (2019-11-26)
==================

* Added code of conduct reference file to the root directory
* Moved contributing file to the root directory
* Added better templates for new issue requests
* Fixed a bug where creating a page via the ``cms.api.create_page`` ignores
  left/right positions.
* Fixed documentation example for ``urls.py`` when using multiple languages.
* Mark public static placeholder dirty when published.
* Fixed a bug where ``request.current_page`` would always be the public page,
  regardless of the toolbar status (draft / live). This only affected custom
  urls from an apphook.
* Fixed a bug where the menu would render draft pages even if the page on
  the request was a public page. This happens when a user without change
  permissions requests edit mode.
* Fixed the 'urls.W001' warning with custom apphook urls
* Prevent non-staff users to login with the django CMS toolbar
* Added missing ``{% trans %}`` to toolbar shortcuts.
* Fixed branch and release policy.
* Improved and simplified permissions documentation.
* Improved apphooks documentation.
* Improved CMSPluginBase documentation.
* Improved documentation related to nested plugins.
* Updated installation tutorial.
* Fixed a simple typo in the docstring for ``cms.utils.helpers.normalize_name``.
* Updated 'How to create Plugins' Tutorial.


3.7.0 (2019-09-25)
==================

* Introduced Django 2.2 support.
* Introduced Python 3.7 support.
* Fixed test suite.
* Fixed override ``urlconf_module`` so that Django system checks don't crash.


3.6.1 (2020-07-21)
==================

* Fixed a security vulnerability in the plugin_type url parameter to insert JavaScript code.


3.6.0 (2019-01-29)
==================

* Removed the ``cms moderator`` command.
* Dropped Django < 1.11 support.
* Removed the translatable content get / set methods from ``CMSPlugin`` model.
* Removed signal handlers for ``Page``, ``Title``, ``Placeholder`` and ``CMSPlugin`` models.
* Moved ``Title.meta_description`` length restriction from model to form
  and increased its max length to 320 characters.
* Added ``page_title`` parameter for ``cms.api.create_page()`` and ``cms.api.create_title()``.
* Introduced Django 2.0 support.
* Introduced Django 2.1 support.


3.5.4 (2020-07-21)
==================

* Fixed a security vulnerability in the plugin_type url parameter to insert JavaScript code.


3.5.3 (2018-11-20)
==================

* Fixed ``TreeNode.DoesNotExist`` exception raised when exporting
  and loading database contents via ``dumpdata`` and ``loaddata``.
* Fixed a bug where ``request.current_page`` would always be the public page,
  regardless of the toolbar status (draft / live). This only affected custom
  urls from an apphook.
* Removed extra quotation mark from the sideframe button template
* Fixed a bug where structureboard tried to preload markup when using legacy
  renderer
* Fixed a bug where updates on other tab are not correctly propagated if the
  operation was to move a plugin in the top level of same placeholder
* Fixed a bug where xframe options were processed by clickjacking middleware
  when page was served from cache, rather then get this value from cache
* Fixed a bug where cached page permissions overrides global permissions
* Fixed a bug where plugins that are not rendered in content wouldn't be
  editable in structure board
* Fixed a bug with expanding static placeholder by clicking on "Expand All" button
* Fixed a bug where descendant pages with a custom url would lose the overwritten
  url on save.
* Fixed a bug where setting the ``on_delete`` option on ``PlaceholderField``
  and ``PageField`` fields would be ignored.
* Fixed a bug when deleting a modal from changelist inside a modal


3.5.2 (2018-04-11)
==================

* Fixed a bug where shortcuts menu entry would stop working after toolbar reload
* Fixed a race condition in frontend code that could lead to sideframe being
  opened with blank page
* Fixed a bug where the direct children of the homepage would get a leading ``/``
  character when the homepage was moved or published.
* Fixed a bug where non-staff user would be able to open empty structure board
* Fixed a bug where a static file from Django admin was referenced that no
  longer existed in Django 1.9 and up.
* Fixed a bug where the migration 0018 would fail under certain databases.


3.5.1 (2018-03-05)
==================

* Fixed a bug where editing pages with primary keys greater than 999 would throw an
  exception.
* Fixed a ``MultipleObjectsReturned`` exception raised on the page types migration
  with multiple page types per site.
* Fixed a bug which prevented toolbar js from working correctly when rendered
  before toolbar.
* Fixed a bug where CMS would incorrectly highlight plugin content when plugin
  contains invisible elements
* Fixed a regression where templates which inherit from a template using an ``{% extends %}``
  tag with a default would raise an exception.


3.5.0 (2018-01-31)
==================

* Fixed a bug which prevented users from seeing the welcome screen when debug is
  turned off.
* Introduced improved repr for ``Page``, ``Title``, ``Placeholder`` and ``CMSPlugin`` models.
* Rename publish buttons to no longer reference "page"
* Page rendering will now use the draft page instead of public page for logged in
  users with change permissions, unless the ``preview`` GET parameter is used.
* Fixed "Expand all / Collapse all" not reflecting real state of the placeholder tree
* Fixed a bug where Aliased plugins would render if their host page was unpublished (and user was not on edit mode).
* Fixed a bug where focusing inputs in modal would require 2 clicks in some browsers
* Changed the language chooser to always show all configured languages to staff members
  and public-only languages to anon users.
* Introduced logic to copy pages to different sites from the admin.
* Removed "View on Site" button when adding a page
* Welcome page no longer uses multilingual URLs when not required.
* Prevent users from passing a public page as parent in ``create_page`` api function


3.4.7 (2020-07-21)
==================

* Removed extra quotation mark from the sideframe button template
* Fixed a bug where xframe options were processed by clickjacking middleware
  when page was served from cache, rather then get this value from cache
* Fixed a bug where cached page permissions overrides global permissions
* Fixed a bug where editing pages with primary keys greater than 9999 would throw an
  exception.
* Fixed broken wizard page creation when no language is set within the template context (see #5828).
* Fixed a security vulnerability in the plugin_type url parameter to insert JavaScript code.


3.4.6 (2018-03-26)
==================

* Changed the way drag and drop works in the page tree. The page has to be
  selected first before moving.
* Fixed a bug where the cms alias plugin leaks context into the rendered aliased plugins.
* Fixed a bug where users without the "Change advanced settings" permission could still
  change a page's template.
* Added ``on_delete`` to ``ForeignKey`` and ``OneToOneField`` to silence Django
  deprecation warnings.
* Fixed a bug where the sitemap would ignore the ``public`` setting of the site languages
  and thus display hidden languages.
* Fixed an ``AttributeError`` raised when adding or removing apphooks in Django 1.11.
* Fixed an ``InconsistentMigrationHistory`` error raised when the contenttypes app
  has a pending migration after the user has applied the ``0010_migrate_use_structure`` migration.
* Fixed a bug where plugins rendered multiple times won't be editable


3.4.5 (2017-10-12)
==================

* Introduced Django 1.11 compatibility
* Fixed a bug where slug wouldn't be generated in the creation wizard
* Fixed a bug where the add page endpoint rendered ``Change page`` as the html title.
* Fixed an issue where non-staff users could request the wizard create endpoint.
* Fixed an issue where the ``Edit page`` toolbar button wouldn't show on non-cms pages
  with placeholders.
* Fixed a bug where placeholder inheritance wouldn't work if the inherited placeholder
  is cached in an ancestor page.
* Fixed a regression where the code following a ``{% placeholder x or %}`` declaration,
  was rendered before attempting to inherit content from parent pages.
* Changed page/placeholder cache keys to use sha1 hash instead of md5 to be FIPS compliant.
* Fixed a bug where the change of a slug would not propagate to all descendant pages
* Fixed a ``ValueError`` raised when using ``ManifestStaticFilesStorage`` or similar for static files.
  This only affects Django >= 1.10


3.4.4 (2017-06-15)
==================

* Fixed a bug in which cancelling the publishing dialog wasn't respected.
* Fixed a bug causing post-login redirection to an incorrect URL on single-language sites.
* Changed the signature for internal ``cms.plugin_base.CMSPluginBase`` methods ``get_child_classes``
  and ``get_parent_classes`` to take an optional ``instance`` parameter.
* Fixed an error when retrieving placeholder label from configuration.
* Fixed a bug which caused certain translations to display double-escaped text in the page
  list admin view.
* Adjusted the toolbar JavaScript template to escape values coming from the request.
* Added Dropdown class to toolbar items
* Replaced all custom markup on the ``admin/cms/page/includes/fieldset.html`` template
  with an ``{% include %}`` call to Django's built-in ``fieldset.html`` template.
* Fixed a bug which prevented a page from being marked as dirty when a placeholder was cleared.
* Fixed an IntegrityError raised when publishing a page with no public version and whose publisher
  state was pending.
* Fixed an issue with JavaScript not being able to determine correct path to the async bundle
* Fixed a ``DoesNotExist`` database error raised when moving a page marked as published, but whose public
  translation did not exist.
* Fixed a bug in which the menu rendered nodes using the site session variable (set in the admin),
  instead of the current request site.
* Fixed a race condition bug in which the database cache keys were deleted without syncing with the
  cache server, and as a result old menu items would continue to be displayed.
* Fixed a 404 raised when using the ``Delete`` button for a Page or Title extension on Django >= 1.9
* Added "How to serve multiple languages" section to documentation
* Fixed a performance issue with nested pages when using the ``inherit`` flag on the ``{% placeholder %}`` tag.
* Removed the internal ``reset_to_public`` page method in favour of the ``revert_to_live`` method.
* Fixed a bug in which the placeholder cache was not consistently cleared when a page was published.
* Enhanced the plugin menu to not show plugins the user does not have permission to add.
* Fixed a regression which prevented users from setting a redirect to the homepage.


3.4.3 (2017-04-24)
==================

* Fixed a security vulnerability in the page redirect field which allowed users
  to insert JavaScript code.
* Fixed a security vulnerability where the ``next`` parameter for the toolbar login
  was not sanitised and could point to another domain.


3.4.2 (2017-01-23)
==================

* Escaped strings in ``close_frame`` JS template.
* Fixed a bug with `text-transform` styles on inputs affecting CMS login
* Fixed a typo in the confirmation message for copying plugins from a different
  language
* Fixed a bug which prevented certain migrations from running in a multi-db setup.
* Fixed a regression which prevented the ``Page`` model from rendering correctly
  when used in a ``raw_id_field``.
* Fixed a regression which caused the CMS to cache the toolbar when ``CMS_PAGE_CACHE``
  was set to ``True`` and an anonymous user had ``cms_edit`` set to ``True`` on their session.
* Fixed a regression which prevented users from overriding content in an inherited
  placeholder.
* Added official support for Django 1.10.
* Fixed a bug affecting Firefox for Macintosh users, in which use of the Command key later followed by Return would
  trigger a plugin save.
* Fixed a bug where template inheritance setting creates spurious migration (see #3479)
* Fixed a bug which prevented the page from being marked as dirty (pending changes)
  when changing the value of the overwrite url field.
* Adjusted Ajax calls triggered when performing a placeholder operation (add plugin, etc..) to include
  a GET query called cms_path. This query points to the path where the operation originates from.
* Added a deprecation warning to method ``render_plugin()`` in class ``CMSPlugin``.
* Since ``get_parent_classes()`` became a classmethod, do not instantiate plugin before invocation.
* Fixed a bug where the page tree would not update correctly when a sibling page was moved
  from left to right or right to left.
* Improved the ``fix-tree`` command so that it also fixes non-root nodes (pages).
* Removed the deprecated ``add_url()``, ``edit_url()``, ``move_url()``, ``delete_url()``, ``copy_url()`` properties of
  CMSPlugin model.
* Deprecated ``frontend_edit_template`` attribute of ``CMSPluginBase``.
* Introduced placeholder operation signals.
* The ``post_`` methods in ```PlaceholderAdminMixin`` have been deprecated in favor of
  placeholder operation signals.
* Re-introduced the "Revert to live" menu option.
* Added support for django-reversion >= 2 (see #5830)
* Rewrote manual installation how-to documentation


3.4.1 (2016-10-04)
==================

* Fixed a regression when static placeholder was uneditable if it was present
  on the page multiple times
* Removed globally unique constraint for Apphook configs.
* Fixed a bug when keyboard shortcuts were triggered when form fields were
  focused
* Fixed a bug when ``shift + space`` shortcut wouldn't correctly highlight a
  plugin in the structure board
* Fixed a bug when plugins that have top-level svg element would break
  structure board
* Fixed a bug where output from the ``show_admin_menu_for_pages`` template tag
  was escaped in Django 1.9
* Fixed a bug where plugins would be rendered as editable if toolbar was shown
  but user was not in edit mode.
* Fixed css reset issue with shortcuts modal


3.4.0 (2016-09-14)
==================

* Changed the way CMS plugins are rendered. The div with `cms-plugin` class is
  no longer rendered around every CMS plugin, instead a combination of `template`
  tags and JavaScript is used to add event handlers and plugin data directly to
  the plugin markup. This fixes most of the rendering issues that were present
  because of the extra markup.
* Changed cache-busting implementation, it is now handled by a path change,
  not by GET parameter.
* Added a possibility to copy pages in the Page Tree by drag'n'drop.
* Make it possible to use multi-table inheritance for Page/Title extensions.
* Refactored plugin rendering functionality to speed up loading time in both
  structure and content mode.
* Added ``Shift + Space`` shortcut that behaves similar to ``Space`` shortcut
  but takes into account currently hovered plugin.
* Improved keyboard navigation
* Added help modal about available shortcuts
* Added fuzzy matching to plugin picker
* Changed the ``downcast_plugins`` utility to return a generator instead of a list
* Fixed a bug that caused an aliased placeholder to show in structure mode.
* Fixed a bug which prevented aliased content from showing correctly without
  publishing the page first.
* Added help text to an ``Alias`` plugin change form when attached to a page
  to show the content editor where the content is aliased from.
* Removed revision support from djangoCMS core.
  As a result both ``CMS_MAX_PAGE_HISTORY_REVERSIONS`` and ``CMS_MAX_PAGE_PUBLISH_REVERSIONS``
  settings are no longer supported, as well as the ``with_revision`` parameter
  in ``cms.api.create_page`` and ``cms.api.create_title``.


3.3.3 (unreleased)
==================

* Fixed a bug where where the plugin picker would display the plugin names
  translated in the request language instead of the user's language.
* Fixed a bug which raised an exception when the ``AdvancedSettingsForm``
  failed validation on certain fields.
* Fixed a bug with widgets not initialising correctly sometimes
* Fixed a tree corruption when moving a published page under a published one.
* Fixed a tree corruption caused by ``fix-tree`` when an unpublished page is parent
  to a published page.
* Fixed an error when publishing a page that has an unpublished child page who is
  parent to a published page.
* Fixed a bug where moving a published page under a page marked as pending publishing
  is left as published instead of being marked as pending publishing.
* Fixed AttributeError when using ``create_page`` in management command
* Fixed a bug in getting the language from current request which can cause error 500
* API functions are now atomic by design (use the @atomic decorator)
* Fixed a bug where a ``Page`` was created with it's languages field set to ``None``.


3.3.2 (2016-08-11)
==================

* Fixed a bug where it wasn't possible to scroll the toolbar menu if scroll
  started on the disabled menu item on small screens.
* Fixed a migration error (0014) that occurred under certain environments.
* Fixed a regression when standalone CMS Widgets wouldn't work due to
  non-existing JavaScript dependencies.
* Fixed a possible recursion error when using the ``Alias`` plugin.
* Fixed a regression where submit handlers for modal form wouldn't be executed
  under certain circumstances


3.3.1 (2016-07-13)
==================

* Added a warning for users who are leaving the page or closing the plugin
  modal by pressing ESC to prevent accidental loss of content.
* Fixed a bug when clicking inside sideframe didn't close toolbar dropdowns
* Fixed a bug where saving errors wouldn't be shown in the modal window.
* Fixed a misleading message when modal iframe contents couldn't be accessed.
* Added a workaround for a bug when plugins couldn't be deleted in Firefox
  with 1Password extension installed
* Changed CMS JavaScript bundling from simple concatenation to webpack-based.
  Using CMS JavaScript modules directly is no longer possible.
* Fixed an issue where plugins that have no immediate DOM representation
  wouldn't be editable or movable.
* Fixed a regression in which plugins that defined ``parent_classes``
  would not show up in the structure mode.
* Introduced new logic to leverage Django's dynamic related name
  functionality on ``CMSPlugin`` subclasses for the parent link field.
* Backported a performance fix from Django to avoid extra queries when
  plugins access their parent via the parent link field ``cmsplugin_ptr``.
* Fixed typo in ``AdvancedSettingsForm`` error messages.
* Fixed long standing bug that prevented apphook endspoints from being
  CSRF exempt.
* Changed default value for ``CMS_INTERNAL_IPS``.
* Fixed an issue that prevented non superusers from copying all plugins
  in a placeholder.
* Fixed an issue where plugin permissions where not checked when clearing
  a placeholder.
* Fixed an issue where plugin permissions where not checked when deleting
  a page or page translation.
* Added support for tiered ``CMS_PLACEHOLDER_CONF``.
* Fixed a useless placeholders edit permissions checking when not in edit
  mode.
* Fixed a bug where users with limited permissions could not interact with
  page tree dropdowns.
* Fixed a bug where Django Compressor could not be used on the sekizai ``js``
  block.
* Fixed an encoding error when running the ``publisher-publish`` command.
* Fixed regression introduced in 3.3.0 when using the
  ``render_plugin_toolbar_config`` template tag directly.
* Fixed ``render_model`` template tags to work with models containing deferred
  fields.
* Fixed error in retrieving placeholder label from configuration.


3.3.0 (2016-05-26)
==================

* Fixed regression in management commands
* Fixed documentation typo
* Added contribution policies documentation
* Corrected documentation in numerous places
* Corrected an issue where someone could see and use the internal placeholder plugin in the structure board
* Fixed a regression where the first page created was not automatically published
* Corrected the instructions for using the ``delete-orphaned-plugins`` command
* Re-pinned django-treebeard to >=4.0.1
* Added CMS_WIZARD_CONTENT_PLACEHOLDER setting
* Renamed the CMS_WIZARD_* settings to CMS_PAGE_WIZARD_*
* Deprecated the old-style wizard-related settings
* Improved documentation further
* Improved handling of uninstalled apphooks
* Fixed toolbar placement when foundation is installed
* Fixed an issue which could lead to an apphook without a slug
* Fixed numerous frontend issues
* Removed support for Django 1.6, 1.7 and python 2.6
* Changed the default value of CMSPlugin.position to 0 instead of null
* Refactored the language menu to allow for better integration with many languages
* Refactored management commands completely for better consistency
* Fixed "failed to load resource" for favicon on welcome screen
* Changed behaviour of toolbar CSS classes: ``cms-toolbar-expanded`` class is only added now when toolbar is fully
  expanded and not at the beginning of the animation. ``cms-toolbar-expanding`` and ``cms-toolbar-collapsing`` classes
  are added at the beginning of their respective animations.
* Added unit tests for CMS JavaScript files
* Added frontend integration tests (written with Casper JS)
* Removed frontend integration tests (written with Selenium)
* Added the ability to declare cache expiration periods on a per-plugin basis
* Improved UI of page tree
* Improved UI in various minor ways
* Added a new setting CMS_INTERNAL_IPS for defining a set of IP addresses for which
  the toolbar will appear for authorized users. If left unset, retains the
  existing behavior of allowing toolbar for authorized users at any IP address.
* Changed behaviour of sideframe; is no longer resizable, opens to 90% of the screen or 100% on
  small screens.
* Removed some unnecessary reloads after closing sideframe.
* Added the ability to make pagetree actions work on currently picked language
* Removed deprecated CMS_TOOLBAR_SIMPLE_STRUCTURE_MODE setting
* Introduced the method ``get_cache_expiration`` on CMSPluginBase to be used
  by plugins for declaring their rendered content's period of validity.
* Introduced the method ``get_vary_cache_on`` on CMSPluginBase to be used
  by plugins for declaring ``VARY`` headers.
* Improved performance of plugin moving; no longer saves all plugins inside the placeholder.
* Fixed breadcrumbs of recently moved plugin reflecting previous position in
  the tree
* Refactored plugin adding logic to no longer create the plugin before the user submits the form.
* Improved the behaviour of the placeholder cache
* Improved fix-tree command to sort by position and path when rebuilding positions.
* Fixed several regressions and tree corruptions on page move.
* Added new class method on CMSPlugin ``requires_parent_plugin``
* Fixed behaviour of ``get_child_classes``; now correctly calculates child classes when not
  configured in the placeholder.
* Removed internal ``ExtraMenuItems`` tag.
* Removed internal ``PluginChildClasses`` tag.
* Modified RenderPlugin tag; no longer renders the ``content.html`` template
  and instead just returns the results.
* Added a ``get_cached_template`` method to the ``Toolbar()`` main class to reuse loaded templates per request. It
  works like Django's cached template loader, but on a request basis.
* Added a new method ``get_urls()`` on the appbase class to get CMSApp.urls, to allow passing a page object to it.
* Changed JavaScript linting from JSHint and JSCS to ESLint
* Fixed a bug when it was possible to drag plugin into clipboard
* Fixed a bug where clearing clipboard was closing any open modal


3.2.5 (2016-04-27)
==================

- Fixed regression when page couldn't be copied if CMS_PERMISSION was False
- Improved handling of uninstalled apphooks
- Fix packaging problem with the wheel distribution


3.2.4 (2016-04-26)
==================

- Fix cache settings
- Fix user lookup for view restrictions/page permissions when using raw id field
- Fixed regression when page couldn't be copied if CMS_PERMISSION was False
- Fixes an issue relating to uninstalling a namespaced application
- Adds "Can change page" permission
- Fixes a number of page-tree issues the could lead data corruption under
  certain conditions
- Addresses security vulnerabilities in the `render_model` template tag that
  could lead to escalation of privileges or other security issues.
- Addresses a security vulnerability in the cms' usage of the messages framework
- Fixes security vulnerabilities in custom FormFields that could lead to
  escalation of privileges or other security issues.


3.2.3 (2016-03-09)
==================

- Fix the display of hyphenated language codes in the page tree
- Fix a family of issues relating to unescaped translations in the page tree


3.2.2 (2016-03-02)
==================

- Substantial improvements to the page tree and significant reduction of reloads
- Update jsTree version to 3.2.1 with slight adaptions to the Pagetree
- Documentation improvements
- Improve the display and usability of the language menu, especially in cases
  where there are many languages.
- Fix an issue relating to search fields in plugins
- Fix an issue where the app-resolver would trigger locales into migrations
- Fix cache settings
- Fix ToolbarMiddleware.is_cms_request logic
- Fix numerous Django 1.9 deprecations
- Numerous other improvements to overall stability and code quality


3.2.1 (2016-01-29)
==================

- Add support for Django 1.9 (with some deprecation warnings).
- Add support for django-reversion 1.10+ (required by Django 1.9+).
- Add placeholder name to the edit tooltip.
- Add ``attr['is_page']=True`` to CMS Page navigation nodes.
- Add Django and Python versions to debug bar info tooltip
- Fix an issue with refreshing the UI when switching CMS language.
- Fix an issue with sideframe urls not being remembered after reload.
- Fix breadcrumb in page revision list.
- Fix clash with Foundation that caused "Add plugin" button to be unusable.
- Fix a tree corruption when pasting a nested plugin under another plugin.
- Fix message with CMS version not showing up on hover in debug mode.
- Fix messages not being positioned correctly in debug mode.
- Fix an issue where plugin parent restrictions where not respected when pasting a plugin.
- Fix an issue where "Copy all" menu item could have been clicked on empty placeholder.
- Fix a bug where page tree styles didn't load from STATIC_URL that pointed to a different host.
- Fix an issue where the side-frame wouldn't refresh under some circumstances.
- Honor CMS_RAW_ID_USERS in GlobalPagePermissionAdmin.


3.2.0 (2015-11-24)
==================

- Added new wizard to improve content creation
- Added Aldryn Apphook Reload https://github.com/aldryn/aldryn-apphook-reload/ into core
- Added database migration creating ``UrlconfRevision`` for apphook reload.
- Added tooltips for certain user interaction elements
- Added full touch support and optimisations for mobile devices
- Added gulp.js for linting, compressing and bundling
- Added YuiDocs for JavaScript documentation
- Added ``CMS_TOOLBAR_SIMPLE_STRUCTURE_MODE`` to switch back to the old board rendering,
  this will be deprecated in 3.3.0
- Added ``request.toolbars.placeholder_list`` this will replace
  ``request.toolbars.placeholders`` in 3.3.0
- Added new installation screen with optimisation alongside the new content creation wizard
- Added ``.editorconfig`` to the django-cms project
- Added HTML rendering capabilities for the modal
- Added browser history to the sideframe
- Improved design for better touch support
- Improved design for better accessibility support such as contrast ratio
- Improved design to reflect latest responsive design standards such as the toolbar
  menu which collapses to "More"
- Improved UI for scrolling, saving and navigating through content
  creation and editing such as ``CTRL + Enter`` for saving
- Improved overall speed loading times and interaction response
- Improved drag & drop experience
- Improved structure board hierarchy to be displayed as tree elements instead of nested boxes
- Improved clipboard to be integrated within the toolbar and structure board (copy & paste)
- Improved modal UI and added significant speed improvements
- Improved sideframe UI and reduced functionality
- Improved messaging system within ``cms.messages.js``
- Improved pagetree design and UI (soft-redesign) refactoring will follow in 3.3
- Improved parent plugin restricts on frontend
- Improved frontend code to comply with aldryn-boilerplate-bootstrap3
- Improved folder structure for frontend related components such as JavaScript and SASS
- Improved color and value variable declarations for Styles
- Improved key mapping for actions such as saving, closing and switching across browsers
- Switched from tabs to 4 spaces everywhere
- Switched from ruby sass/compass to libsass/autoprefixer
- Switched from sprite images to auto generated webfonts via gulp
- Moved widgets.py javascript to ``static/cms/js/widgets``
- Fixed an issue in which placeholder template tags ignored the ``lang`` parameter
- Renamed cms_app, cms_menu, cms_toolbar to plural versions eg. ``cms_apps.py``
  ``cms_menus.py``, ``cms_toolbars.py`` with backwards compatibility
- Removed all id attributes on html elements in favour of classes
- Removed 'develop.py' to replace with 'manage.py' (devs)
- Removed Alias plugin from list of plugins (Create Alias still an option)
- Added support for 3rd party admin themes
- Update the toolbar tutorial
- Update the 3rd party integration tutorial
- Fixed an issue where dialogs can't be closed when activating prevent checkbox
- Fixed edit and edit_off constants not being honoured in frontend code
- Deprecate CMSPlugin.disable_child_plugin in favour of disable_child_plugins
- Fixed an issue where ``allow_children`` and ``disable_child_plugins`` didn't work on dragitems


3.1.8 (unreleased)
==================

- Removed html5lib from setup.py


3.1.7 (2016-04-27)
==================

- Fix packaging problem with the wheel distribution


3.1.6 (2016-04-26)
==================

- Fix cache settings
- Fix user lookup for view restrictions/page permissions when using raw id field
- Fixes an issue relating to uninstalling a namespaced application
- Adds "Can change page" permission
- Addresses security vulnerabilities in the `render_model` template tag that
  could lead to escalation of privileges or other security issues.
- Addresses a security vulnerability in the cms' usage of the messages framework
- Fixes security vulnerabilities in custom FormFields that could lead to
  escalation of privileges or other security issues.


3.1.5 (2016-01-29)
==================

- Fixed a tree corruption when pasting a nested plugin under another plugin.
- Improve CMSPluginBase.render documentation
- Fix CMSEditableObject context generation which generates to errors with django-classy-tags 0.7.1
- Fix error in toolbar when LocaleMiddleware is not used
- Move templates validation in app.ready
- Fix ExtensionToolbar when language is removed but titles still exists
- Fix pages menu missing on fresh install 3.1
- Fix incorrect language on placeholder text for redirect field
- Fix PageSelectWidget JS syntax
- Fix redirect when disabling toolbar
- Fix CMS_TOOLBAR_HIDE causes 'WSGIRequest' object has no attribute 'toolbar'


3.1.4 (2015-11-24)
==================

- Fixed a problem in ``0010_migrate_use_structure.py`` that broke some migration paths to Django 1.8
- Fixed ``fix_tree`` command
- Removed some warnings for Django 1.9
- Fixed issue causing plugins to move when using scroll bar of plugin menu in Firefox & IE
- Fixed JavaScript error when using ``PageSelectWidget``
- Fixed whitespace markup issues in draft mode
- Added plugin migrations layout detection in tests
- Fixed some treebeard corruption issues


3.1.3 (2015-09-01)
==================

- Add missing migration
- Exclude PageUser manager from migrations
- Fix check for template instance in Django 1.8.x
- Fix error in PageField for Django 1.8
- Fix some Page tree bugs
- Declare Django 1.6.9 dependency in setup.py
- Make sure cache version returned is an int
- Fix issue preventing migrations to run on a new database (django 1.8)
- Fix get User model in 0010 migration
- Fix support for unpublished language pages
- Add documentation for plugins datamigration
- Fix getting request in _show_placeholder_for_page on Django 1.8
- Fix template inheritance order
- Fix xframe options inheritance order
- Fix placeholder inheritance order
- Fix language chooser template
- Relax html5lib versions
- Fix redirect when deleting a page
- Correct South migration error
- Correct validation on numeric fields in modal popups
- Exclude scssc from manifest
- Remove unpublished pages from menu
- Remove page from menu items for performance reason
- Fix reachability of pages with expired ancestors
- Don't try to modify an immutable QueryDict
- Only attempt to delete cache keys if there are some to be deleted
- Update documentation section
- Fix language chooser template
- Cast to int cache version
- Fix extensions copy when using duplicate page/create page type


3.1.2 (2015-07-02)
==================

- Fix placeholder cache invalidation under some circumstances
- Update translations


3.1.1 (2015-06-27)
==================

- Add Django 1.8 support
- Tutorial updates and improvements
- Fix issue with causes menu classes to be duplicated in advanced settings
- Fix issue with breadcrumbs not showing
- Fix issues with show_menu templatetags
- Minor documentation fixes
- Revert whitespace cleanup on flash player to fix it
- Correctly restore previous status of dragbars
- Add copy_site command
- Fix an issue related to "Empty all" Placeholder feature
- Fix plugin sorting in py3
- Fix language-related issues when retrieving page URL
- Add setting to disable toolbar for anonymous users
- Fix search results number and items alignment in page changelist
- Preserve information regarding the current view when applying the CMS decorator
- Fix errors with toolbar population
- Fix error with watch_models type
- Fix error with plugin breadcrumbs order
- Change the label "Save and close" to "Save as draft"
- Fix X-Frame-Options on top-level pages
- Fix order of which application urls are injected into urlpatterns
- Fix delete non existing page language
- Fix language fallback for nested plugins
- Fix render_model template tag doesn't show correct change list
- Fix Scanning for placeholders fails on include tags with a variable as an argument
- Fix handling of plugin position attribute
- Fix for some structureboard issues
- Add setting to hide toolbar when a URL is not handled by django CMS
- Add editorconfig configuration
- Make shift tab work correctly in submenu
- Fix get_language_from_request if POST and GET exists
- Fix an error in placeholder cache
- Fix language chooser template


3.1.0 (2015-04-20)
==================

- Remove django-mptt in favor of django-treebeard
- Remove compatibility with Django 1.4 / 1.5
- General code cleanup
- Simplify loading of view restrictions in the menu
- South is not marked as optional; to use south on Django 1.6 install django-cms[south]
- Add system_plugin attribute to CMSPluginBase that allow the plugin to override any configured restriction
- Change placeholder language fallback default to True
- Remove plugin table naming compatibility layer
- Remove deprecated cms.context_processors.media context processor
- Add templatetag render_plugin_block
- Add templatetag render_model_add_block
- Add "Structure mode" permission


3.0.17 (unreleased)
===================

- Addresses security vulnerabilities in the `render_model` template tag that could
  lead to escalation of privileges or other security issues.
- Fix ExtensionToolbar when language is removed but titles still exists…
- Fix PageSelectWidget JS syntax
- Fix cache settings


3.0.16 (2015-11-24)
===================

- Fixed JavaScript error when using ``PageSelectWidget``
- Fixed whitespace markup issues in draft mode
- Added plugin migrations layout detection in tests


3.0.15 (2015-09-01)
===================

- Relax html5lib versions
- Fix redirect when deleting a page
- Correct South migration error
- Correct validation on numeric fields in modal popups
- Exclude scssc from manifest
- Remove unpublished pages from menu
- Remove page from menu items for performance reason
- Fix reachability of pages with expired ancestors
- Don't try to modify an immutable QueryDict
- Only attempt to delete cache keys if there are some to be deleted
- Update documentation section
- Fix language chooser template
- Cast to int cache version
- Fix extensions copy when using duplicate page/create page type


3.0.14 (2015-06-27)
===================

- Fixed an issue where privileged users could be tricked into performing actions without their knowledge via a CSRF vulnerability
- Fixed an issue related to "Empty all" Placeholder feature
- Fix issue with causes menu classes to be duplicated in advanced settings
- Fix issue with breadcrumbs not showing
- Fix issues with show_menu templatetags
- Fix plugin sorting in py3
- Fix search results number and items alignment in page changelist
- Fix X-Frame-Options on top-level pages
- Preserve information regarding the current view when applying the CMS decorator
- Fix render_model template tag doesn't show correct change list
- Fix language fallback for nested plugins
- Fix order of which application urls are injected into urlpatterns
- Fix delete non existing page language
- Fix Scanning for placeholders fails on include tags with a variable as an argument
- Minor documentation fixes
- Pin South version to 1.0.2
- Pin Html5lib version to 0.999 until a current bug is fixed
- Fix language chooser template


3.0.13 (2015-04-15)
===================

- Numerous documentation including installation and tutorial updates
- Numerous improvements to translations
- Improves reliability of apphooks
- Improves reliabiliy of Advanced Settings on page when using apphooks
- Allow page deletion after template removal
- Improves upstream caching accuracy
- Improves CMSAttachMenu registration
- Improves handling of mistyped URLs
- Improves redirection as a result of changes to page slugs, etc.
- Improves performance of "watched models"
- Improves frontend performance relating to resizing the sideframe
- Corrects an issue where items might not be visible in structure mode menus
- Limits version of django-mptt used in CMS for 3.0.x
- Prevent accidental upgrades to Django 1.8, which is not yet supported


3.0.12 (2015-03-06)
===================

- Fixed a typo in JavaScript which prevents page tree from working


3.0.11 (2015-03-05)
===================

- Core support for multiple instances of the same apphook'ed application
- Fixed the template tag `render_model_add`
- Fixed an issue with reverting to Live
- Fixed a missing migration issue
- Fixed an issue when using the PageField widget
- Fixed an issue where duplicate page slugs is not prevented in some cases
- Fixed an issue where copying a page didn't copy its extensions
- Fixed an issue where translations where broken when operating on a page
- Fixed an edge-case SQLite issue under Django 1.7
- Fixed an issue with confirmation dialog
- Fixed an issue with deprecated 'mimetype'
- Fixed an issue where `cms check`
- Documentation updates


3.0.10 (2015-02-14)
===================

- Improved Py3 compatibility
- Improved the behavior when changing the operator's language
- Numerous documentation updates
- Revert a change that caused an issue with saving plugins in some browsers
- Fix an issue where urls were not refreshed when a page slug changes
- Fix an issue with FR translations
- Fixed an issue preventing the correct rendering of custom contextual menu items for plugins
- Fixed an issue relating to recovering deleted pages
- Fixed an issue that caused the uncached placeholder tag to display cached content
- Fixed an issue where extra slashed would appear in apphooked URLs when APPEND_SLASH=False
- Fixed issues relating to the logout function


3.0.9 (2015-01-11)
==================

- Revert a change that caused a regression in toolbar login
- Fix an error in a translated phrase
- Fix error when moving items in the page tree


3.0.8 (2015-01-11)
==================

- Add require_parent option to CMS_PLACEHOLDER_CONF
- Fix django-mptt version dependency to be PEP440 compatible
- Fix some Django 1.4 compatibility issues
- Add toolbar sanity check
- Fix behavior with CMSPluginBase.get_render_template()
- Fix issue on django >= 1.6 with page form fields.
- Resolve jQuery namespace issues in admin page tree and changeform
- Fix issues for PageField in Firefox/Safari
- Fix some Python 3.4 compatibility issue when using proxy models
- Fix corner case in plugin copy
- Documentation fixes
- Minor code cleanups


3.0.7 (2014-11-27)
==================

- Complete Django 1.7 support
- Numerous updates to the documentation
- Numerous updates to the tutorial
- Updates to better support South 1.0
- Adds some new, user-facing documentation
- Fixes an issue with placeholderadmin permissions
- Numerous fixes for minor issues with the frontend UI
- Fixes issue where the CMS would not reload pages properly if the URL contained a # symbol
- Fixes an issue relating to 'limit_choices_to' in forms.MultiValueFields
- Fixes PageField to work in Django 1.7 environments
- Updates to community and project governance documentation
- Added list of retired core developers
- Added branch policy documentation


3.0.6 (2014-10-07)
==================

- Experimental full Django 1.7 migrations support
- Add CMSPlugin.get_render_model to get the plugin model at render time
- Add simplified API to handle toolbar for page extensions
- Extended custom user model support
- Added option to publish all the pages in a language / site in publisher_publish command
- Fixed a few frontend glitches
- Fixed menu when hide untranslated is set to False
- Fix sitemap ordering
- Fix plugin table name generation fixes


3.0.5 (2014-08-20)
==================

- Fixes 2 regressions introduced in 3.0.4
- apphook and plugins can now be registered via decorator


3.0.4 (2014-08-16)
==================

- Removed file cms/utils/compat/type_checks.py, use django.utils.six module instead
- Removed file cms/utils/compat/string_io.py, use django.utils.six module instead
- Removed file cms/utils/compat/input.py, use django.utils.six module instead
- Use PY3 from django.utils.six instead of PY2 from cms.utils.compat to check Python version
- Staticplaceholders have not their own permissions
- Apphooks support now nested namespaces
- Apphooks can now exclude module for page permission checking
- fixed the permissions for plugins on apphook pages
- Allow the use of custom admin sites that do not reside under the 'admin' namespace
- Added django 1.7 migrations
- updated docs
- slots for placeholders can now be 255 characters long
- Plugin pool initialises incorrectly if database is down during first request
- some refactoring and simplifications


3.0.3 (2014-07-07)
==================

- Added an alias plugin for referencing plugins and placeholders
- Added an api to change the context menus of plugins and placeholders from plugins
- Apphooks respect the page permissions
- Decorator for views with page permissions
- #3266 - api.create_page respects site
- Fixed how permissions are checked for static placeholder.
- Reduced queries on placeholder.clear by 60%
- auto-detect django-suit instead of using explicit setting
- Added the ability to mark (Sub)Menu's 'active'.
- fallback language fixes for pages
- Implemented transaction.atomic in django 1.4/1.5 way
- Added a automatic dynamic template directory for page templates


3.0.2 (2014-05-21)
==================

- Add 'as' form to render_placeholder templatetag to save the result in context
- Added changeable strings for "?edit", "?edit_off" and "?build" urls
- utils.page_resolver was optimized. get_page_from_path() api changed


3.0.1 (2014-04-30)
==================

- Renamed NamespaceAllreadyRegistered to NamespaceAlreadyRegistered in menus/exceptions.py
- Frontend editor UI fixes
- Fix in cms fix-mptt command


3.0.0 (2014-04-08)
==================

- Plugins are only editable in frontend
- PluginEditor has been removed in backend
- New frontend editing
- New Toolbar
- Plugin API for creating new plugins and moving has changed
- render_to_response replaced with TemplateResponse in cms.views
- CMS_SEO_FIELDS removed and seo fields better integrated
- meta_keywords field removed as not relevant anymore
- CMS_MENU_TITLE_OVERWRITE default changed to True
- Toolbar has language switcher built in
- User settings module added for saving the language of the user so when he switches languages the toolbar/interface
  keeps the language.
- language_chooser templatetag now only displays public languages, even when you are logged in as staff.
- undo and redo functionality added in toolbar if django-reversion is installed.
- page admin split in 3 different for basic, advanced and permissions
- New show_editable_page_title templatetag to edit page title from the frontend
- Removed PLACEHOLDER_FRONTEND_EDITING setting
- Removed CMS_URL_OVERWRITE setting. Always enabled.
- Removed CMS_MENU_TITLE_OVERWRITE settings. Always enabled.
- Removed CMS_REDIRECTS. Always enabled.
- Removed CMS_SOFTROOT. Always enabled.
- Removed CMS_SHOW_START_DATE. Always enabled.
- Removed CMS_SHOW_END_DATE. Always enabled.
- Added (optional) language fallback for placeholders.
- moved apphooks from title to page model so we need to add them only once.
- request.current_app has been removed.
- added a namespace field, reverse_id is not used anymore for apphook namespaces.
- PlaceholderAdmin is deprecated and available as mixin class renamed to PlaceholderAdminMixin.
- PlaceholderAdmin does not have LanguageTabs anymore. It only has a PluginAPI now.
- PageAdmin uses the same Plugin API as PlaceholderAdmin
- Toolbar API for your own apps added
- twitter plugin removed
- file plugin removed
- flash plugin removed
- googlemap plugin removed
- inherit plugin removed
- picture plugin removed
- teaser plugin removed
- video plugin removed
- link plugin removed
- snippet plugin removed
- Object level permission support for Placeholder
- Configuration for plugin custom modules and labels in the toolbar UI
- Added copy-lang subcommand to copy content between languages
- Added static_placeholder templatetag
- Moved render_placeholder from placeholder_tags to cms_tags
- django 1.6 support added
- Frontedit editor for Django models
- Extending the page & title model API
- Placeholders can be configured to have plugins automatically added.
- Publishing is now language independent and the tree-view has been updated to reflect this
- Removed the plugin DB-name magic and added a compatibility layer
- urls_need_reloading signal added when an apphook change is detected.
- CMS_PAGE_CACHE, CMS_PLACEHOLDER_CACHE and CMS_PLUGIN_CACHE settings and functionality added. Default is True
- Detect admin object creation and changes via toolbar and redirect to them.
- Added support for custom user models
- Added PageTypes
- Added CMS_MAX_PAGE_HISTORY_REVERSIONS and changed default of CMS_MAX_PAGE_PUBLISH_REVERSIONS
- Added option to {% static_placeholder %} to render only on the current site.


2.4.2 (2013-05-29)
==================

- Apphook edit mode bugfix
- Added option to render_placeholder tag to set language
- Huge permission cache invalidation speed up
- Doc improvements
- css cleanup in PlaceholderAdmin
- Log change of page status done via AJAX
- Use --noinput convention for delete_orphaned_plugins command
- added Testing docs
- fixed more issues with only one language
- locales updated


2.4.1 (2013-04-22)
==================

- USE_I18N=False fixed
- some frontend css stuff fixed
- check_copy_relations fixed for abstract classes
- non public frontend languages fixed


2.4.0 (2013-04-17)
==================

Please see Install/2.4 release notes *before* attempting to upgrade to version 2.4.

- Compatibility with Django 1.4 and 1.5 (1.3 support dropped)
- Support for Python 2.5 dropped
- CMS_MAX_PAGE_PUBLISH_REVERSIONS has been added
- Reversion integration has changed to limit DB size
- CMS_LANGUAGE setting has changed
- CMS_HIDE_UNTRANSLATED setting removed
- CMS_LANGUAGE_FALLBACK setting removed
- CMS_LANGUAGE_CONF setting removed
- CMS_SITE_LANGUAGES setting removed
- CMS_FRONTEND_LANGUAGES setting removed
- MultilingualMiddleware has been removed
- CMS_FLAT_URLS has been removed
- CMS_MODERATOR has been removed and replaced with simple publisher.
- PlaceholderAdmin has now language tabs and has support for django-hvad
- Added `cms.middleware.language.LanguageCookieMiddleware`
- Added CMS_RAW_ID_USERS


2.3.4 (2012-11-09)
==================

- Fixed WymEditor
- Fixed Norwegian translations
- Fixed a bug that could lead to slug clashes
- Fixed page change form (jQuery and permissions)
- Fixed placeholder field permission checks


2.3.3 (2012-09-21)
==================

 - fixed an incompatibility with Python 2.5


2.3.2 (2012-09-19)
==================

- MIGRATION: 0036_auto__add_field_cmsplugin_changed_date.py - new field changed_date on CMSPlugin
- CMS_FRONTEND_LANGUAGES limits django languages as well during language selection
- Wymeditor updated to 1.0.4a
- icon_url escape fixed
- Ukrainian translation added
- Fixed wrong language prefix handling for form actions and admin preview
- Admin icons in django 1.4 fixed
- Added requirements.txt for pip and testing in test_requirements
- Google map plugin with height and width properties. Migrations will set default values on not-null fields.
- Docs fixes
- Code cleanup
- Switched html5lib to HTML serializer
- Removed handling of iterables in plugin_pool.register_plugin
- Performance and reduced queries
- Link has target support
- Made the PageAttribute templatetag an 'asTag'
- JQuery namespace fixes in admin


2.3.1 (2012-08-22)
==================

- pinned version of django-mptt to 0.5.1 or 0.5.2


2.3.0 (2012-06-29)
==================

- Compatibility with Django 1.3.1 and 1.4 (1.2 support dropped)
- Lazy admin page tree loading
- Toolbar JS isolation
- Destructive plugin actions fixed (cancel button, moving plugins)
- Refactored tests
- Fixed or clause of placeholder tag
- Fixed double escaping of icon sources for inline plugins
- Fixed order of PageSelectWidget
- Fixed invalid HTML generated by file plugin
- Fixed migration order of plugins
- Fixed internationalized strings in JS not being escaped
- django-reversion dependency upgraded to 1.6
- django-sekizai dependency upgraded to 0.6.1 or higher
- django-mptt dependency upgraded to 0.5.1 or higher


2.2.0 (2011-09-10)
==================

- Replaced the old plugin media framework with django-sekizai. (This changed some plugin templates which might cause problems with your CSS styling).
- Made django-mptt a proper dependency
- Removed support for django-dbgettext
- Google Maps Plugin now defaults to use HTTPS.
- Google Maps Plugin now uses the version 3 of their API, no longer requiring an API Key.


2.1.4 (2011-08-24)
==================

- Fixed a XSS issue in Text Plugins


2.1.3 (2011-02-22)
==================

- Fixed a serious security issue in PlaceholderAdmin
- Fixed bug with submenus showing pages that are not 'in_navigation' (#716, thanks to Iacopo Spalletti for the patch)
- Fixed PlaceholderField not respecting limits in CMS_PLACEHOLDER_CONF (thanks to Ben Hockey for reporting this)
- Fixed the double-monkeypatch check for url reversing (thanks to Benjamin Wohlwend for the patch)


2.1.2 (2011-02-16)
==================

- Fixed issues with the CSRF fix from 2.1.1.
- Updated translation files from transifex.


2.1.1 (2011-02-09)
==================

- Fixed CMS AJAX requests not being CSRF protected, thus not working in Django 1.2.5
- Fixed toolbar CSS issues in Chrome/Firefox


2.1.0 (2011-01-26)
==================

- language namespaces for apphooks (reverse("de:myview"), reverse("en:myview"))
- video plugin switch to https://github.com/FlashJunior/OSFlashVideoPlayer
- frontediting added (cms.middleware.toolbar.ToolbarMiddleware)
- testsuite works now under sqlite and postgres
- orphaned text embed plugins get now deleted if not referenced in the text anymore
- placeholder templatetag: "theme" attribute removed in favor of "width" (backward incompatible change if theme was used)
- menu is its own app now
- menu modifiers (you can register menu modifiers that can change menu nodes or rearrange them)
- menus are now class based.
- apphooks are now class based and can bring multiple menus and urls.py with them.
- menus and apphooks are auto-discovered now
- example templates look a lot better now.
- languages are not a dropdown anymore but fancy tabs
- placeholderend templatetag added: {% placeholder "content" %}There is no content here{% endplaceholder %}
- plugins can now be used in other apps :) see cms/docs/placeholders.txt
- plugins can now be grouped
- a lot of bugfixes
- the cms now depends on the cms.middleware.media.PlaceholderMediaMiddleware middleware
- templatetags refactored: see cms/docs/templatetags.txt for new signatures.
- placeholder has new option: or and a endpalceholder templatetag


2.0.2 (2009-12-14)
==================

- testsuite working again
- changelog file added


2.0.1 (2009-12-13)
==================

- mostly bugfixes (18 tickets closed)
- docs updated
- permissions now working in multisite environment
- home is now graphically designated in tree-view

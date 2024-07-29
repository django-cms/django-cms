4.1.1 (2024-04-30)
==================

Features:
---------
* send post request if toolbar button has `cms-form-post-method` class (bb31ba990) -- Fabian Braun
* Add RTL support to modal header and related components (#7863) (bef004550) -- Moe
* Add RTL support to toolbar (#7871) (92a1086de) -- Moe
* add versioned deprecation warnings (#7750) (545ea1f6d) -- Fabian Braun
* Added new contributor message based on django's own version (#7797) (311af6cf3) -- Mark Walker

Bug Fixes:
----------
* Placeholders must not block deletion of their source objects (ccb2e8b3b) -- Fabian Braun
* structure board on the right for ltr (a4c6ccb68) -- Fabian Braun
* CMS widgets need not load if they are read only (#7880) (fb30434e4) -- Fabian Braun
* some Django antipatterns (#7867) (c436cf45a) -- Jacob Rief
* Redirects to newly created object (#7864) (0b43a43c3) -- Fabian Braun
* `views.details` revealed existence of unpublished language (#7853) (fa7b89cee) -- Fabian Braun
* Render structure view in toolbar object's language (#7846) (d123d118d) -- Fabian Braun
* Add RTL support to pagetree (#7817) (21d6a6def) -- Moe
* 7828, try using uv as pip replacement (#7829) (08463c274) -- Vinit Kumar
* Efficient build menu for versioned and unversioned pages (#7807) (b0f59bb55) -- Fabian Braun
* Delete orphaned plugin management command for django CMS 4 (#7814) (3e635d3db) -- Fabian Braun
* render content in place `redirect_on_fallback` is False (#7781) (e264d0400) -- Moe
* solved issue #7818 (#7819) (087fa3ec7) -- Raffaella
* Port forward #7070 - faster DOM update after editing (#7787) (26b081a31) -- Fabian Braun
* return _handle_no_page when page is None (#7786) (ce8d5d557) -- Moe
* Redirect user to edit url after a successful page creation (#7772) (f290e3d09) -- Moe
* editing of apphooked CMS pages without apphook landing page (#7766) (cd6df846b) -- Philipp S. Sommer
* make messages readable in dark mode, let user close long messages (#7740) (68749cbb3) -- Fabian Braun
* Replace the VCS pip installs with release name in docs (#7755) (10e9b5327) -- sakhawy
* Incorrect commands to migrate database in docs (#7754) (082214be6) -- sakhawy
* Incomplete command to create a virtual env in docs (#7735) (490dffab1) -- Fabian Braun

Statistics:
-----------

This release includes 89 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Aiden-RC (2 pull requests)
* Erdenebat Oyungerel (1 pull request)
* Fabian Braun (37 pull requests)
* Github Release Action (4 pull requests)
* Jacob Rief (4 pull requests)
* Mario Colombo (1 pull request)
* Mark Walker (9 pull requests)
* Miloš Nikić (1 pull request)
* Moe (6 pull requests)
* Philipp S. Sommer (1 pull request)
* Raffaella (1 pull request)
* Vinit Kumar (1 pull request)
* dependabot[bot] (0 pull request)
* sakhawy (2 pull requests)
* sparrow (1 pull request)

With the review help of the following contributors:

* Fabian Braun
* Github Release Action
* Jacob Rief
* Leonardo Cavallucci
* Mario Colombo
* Mark Walker
* Vinit Kumar
* dependabot[bot]
* nichoski

Thanks to all contributors for their efforts!

4.1.0 (2023-12-22)
==================

Features:
---------
* Dark mode for v4 branch (#7597) (e0c923836) -- Fabian Braun
* Graceful plugin exceptions (#7423)
* Reintroduce indicator menus (#7426)
* Add release scripts for develop-4 branch (#7466)
* Icon update (#7494)
* Add setting to redirect slugs to lowercase et al. (#7510)
* Grouper model admin class
* Change `TitleExtension` to `PageContentExtension` (#7369)
* Optimize populating page content cache for Page model. (#7177)
* Unified icon font with icons for versioning, moderation and version locking
* Django 4.2, 4.1 and 4.0 support
* Python 3.11, 3.10 support
* Remove patching of PageContent by djangocms-versioning (#7446)
* Utility function get_placeholder_from_slot for PlaceholderRelationField (#7479)

Bug Fixes:
----------
* Open new plugin window in language of toolbar not of page (#7632) (ac74c2127) -- Fabian Braun
* Update transifex source file (#7629) (06ecf3a8e) -- Fabian Braun
* Remove publish/draft reference from grouper admin message (fcc2f7ad5) -- Fabian Braun
* Update _modal.scss (4ab1f58cd) -- Fabian Braun
* Better action feedback (94cc9b0f5) -- Fabian Braun
* modal.scss dark-mode compatibilitiy (318d417a4) -- Fabian Braun
* remove `copy_to_public` from page and page content extensions (#7604) (81ad858e9) -- Fabian Braun
* Cross-talk between grouper admins due to common list initialization (#7613) (1f932b097) -- Fabian Braun
* Remove admin view provided cancel button from modals (since it has its own cancel button) (#7603) (5caf8d5c2) -- Fabian Braun
* Upgrade js build system to node.js 18 (#7601) (a0977a7f9) -- Vinit Kumar
* update diff-dom and karma, run frontend tests on Chrome Headless (#7599) (69a6cef63) -- Fabian Braun
* Sitemaps in v4 relied on availability of `PageUrl` instead of `PageContent` (#7596) (1c208a8cb) -- Fabian Braun
* page settings does not correctly focus (#7576) (e100087c3) -- Fabian Braun
* Add (back) navigation extenders to advanced settings (#7578) (3e3a86b4f) -- Fabian Braun
* Unlocalize ids to avoid js errors for ids greater than 999 (#7577) (52e6f8751) -- Fabian Braun
* create page wizard fails with Asian page titles/unicode slugs (#7572) (79a063f21) -- Fabian Braun
* take csrf token from admin form or cms toolbar instead of cookie (6a6ebecff) -- Fabian Braun
* Menu link is outdated when page moved (#7558)
* Preview button lead to the wrong language (#7558)
* empty actions shown without unwanted spaces (#7545) (#7552) (aee76b492) -- Fabian Braun
* Language switching in page settings (#7507)
* Show language menu in toolbar only if at least two languages are configured (#7508)
* Moving plugins between placeholders, plugin api (#7394)
* Apphooks at endpoints (#7496)
* Fix bug that broke page tree if it contained empty page content
* Fix bug that created new page content not in the displayed language but the browser language
* Remove outdated Django setting SEND_BROKEN_LINK_EMAILS
* Fixed redirect issues when i18n_patterns had prefix_default_language = False
* add release scripts for develop-4 branch (#7466) (ddbc99a53) -- Fabian Braun

Statistics:
-----------

This release includes 201 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Adam Murray (2 pull requests)
* Aiky30 (35 pull requests)
* Andrew Aikman (1 pull request)
* Chematronix (1 pull request)
* Fabian Braun (83 pull requests)
* Github Release Action (4 pull requests)
* Jacob Rief (2 pull requests)
* Jonathan Sundqvist (7 pull requests)
* Krzysztof Socha (17 pull requests)
* Malinda Perera (3 pull requests)
* Mark Walker (8 pull requests)
* Mateusz Kamycki (1 pull request)
* Nebojsa Knezevic (1 pull request)
* Paulo (18 pull requests)
* Paulo Alvarado (12 pull requests)
* Simon (1 pull request)
* Vadim Sikora (11 pull requests)
* Vinit Kumar (2 pull requests)
* anirbanlahiri-fidelity (1 pull request)
* monikasulik (3 pull requests)

With the review help of the following contributors:

* Adam Murray
* Aiky30
* Andrew Aikman
* Angelo Dini
* Bartosz Płóciennik
* Fabian Braun
* Florian Delizy
* Github Release Action
* Iacopo Spalletti
* Jacob Rief
* Krzysztof Socha
* Marco Bonetti
* Mark Walker
* Radek Stępień
* Radosław Stępień
* Raffaele Salmaso
* Stuart Axon
* Vinit Kumar
* Will Hoey
* dwintergruen
* pajowu
* wfehr
* wintergruen
* Éric Araujo

Thanks to all contributors for their efforts!

4.0 (unreleased)
================

Features:
---------
* Added pre-migrate hook to check version 4 is intentional (#7249) (ff6cb9b5d) -- Mark Walker
* Add live-url url query parameter to PageContent cms Preview and Edit endpoints (#7359) (ee89fe4f4) -- Adam Murray
* backport - Upgrade Gulp and Nodejs (#7255) (f110ddb25) -- Aiky30
* Re-enable showing the toolbar to anonymous users (#7221) (2008ca8a8) -- Aiky30
* backport - django-cms 4.0.x - Django 3.2 support  (#7153) (b0deaedd7) -- Aiky30
* backport - django-cms 4.0.x - Django 3.1 support (#7145) (fb0d4f235) -- Aiky30
* backport - django-cms 4.0.x - Django 3.0 support (#7105) (c44b6beda) -- Aiky30
* djangocms 4.0.x documentation updates (#7007) (#7130) (28f41fe9c) -- Aiky30
* Split database packages so that tests can be run with sqlite (same changes as develop) (#7042) (c77b5e08a) -- Mark Walker
* Back ported migrating from Travis.ci to Github actions from develop (#7006) (29ae26eaf) -- Aiky30
* Add CMSAppExtension.ready which is called after all cms app configs are loaded (#6554) (c02308fc5) -- Krzysztof Socha
* Deprecate the core Alias plugin (#6918) (0fec81224) -- Aiky30
* Refactor get_title_cache to be straightforward and populate when only partially populated (#6829) (80911296b) -- Jonathan Sundqvist
* Add Oracle support to custom plugin queries. (#6832) (90bb064fa) -- Jonathan Sundqvist
* Provide a general get method that can be monkeypatched (#6806) (e429b4584) -- Jonathan Sundqvist
* Adding support for Django 2.2 LTS to django-cms 4.0 (#6790) (1b80000cf) -- Jonathan Sundqvist
* Optionally disable the sideframe (#6553) (a1ac04d3f) -- Aiky30
* Dedicated edit preview buttons (#6528) (5005cd933) -- Malinda Perera
* Use PageContent instance in wizard form instead of Page instance (#6532) (4307e1b8c) -- Krzysztof Socha
* Expose sideframe in CMS.API (4dadf9f1e) -- Vadim Sikora
* Add toolbar persist GET parameter (#6516) (fb27c34e2) -- Krzysztof Socha
* Rename default persist param (a7df58dc5) -- Krzysztof Socha
* Removed resolve view (e3a23a7fc) -- Paulo
* Removed resolve page (0e885ca9e) -- Vadim Sikora
* Add toolbar_persist GET parameter, defaulting to true. If set to false disabling/enabling toolbar won't be saving in the session (77a48d6ee) -- Krzysztof Socha
* Added language to Page translation operations (ca16415b1) -- Paulo
* Use get_title_obj on Page toolbar (#6508) (4981c6229) -- Krzysztof Socha
* Add frontend editing & rendering registry (#6500) (db4ff4162) -- Krzysztof Socha
* Added placeholder checks (#6505) (53171cf2b) -- Krzysztof Socha
* Added language switcher to page tree + re-enabled tests (#6506) (70db27c49) -- Vadim Sikora
* Added PageContent admin (#6503) (2e090d6c2) -- Paulo Alvarado
* Integrated Placeholder source field (#6496) (b075f44d3) -- Malinda Perera
* Added BaseToolbar.preview_mode_active property (#6499) (39562aeb9) -- Krzysztof Socha
* Renamed Title model to PageContent (#6489) (2894ae8bc) -- Aiky30
* Added warning for create_page published arg (f48b8698f) -- Paulo Alvarado
* Fixed frontend to use new edit/structure urls (e960ce726) -- Vadim Sikora
* Added Preview, Structure and Edit endpoints (#6490) (0f12156c8) -- Malinda Perera
* Removed publisher from core (#6486) (9f2507545) -- Paulo Alvarado
* Moved certain Page fields to Title model (#6477) (d7e2d26a6) -- Krzysztof Socha
* Moved permission creation logic out of _create_user (cd74dc85d) -- Paulo Alvarado
* Replaced custom app plugin endpoints with placeholder endpoints (#6469) (685361d47) -- Aiky30
* Frontend for new plugin architecture (bda219b7f) -- Vadim Sikora
* Removed default plugin creation for placeholders (#6468) (eef5cbbfe) -- Krzysztof Socha
* Added MySQL and SQLite compatibility to plugin tree (#6461) (4dfaa1c36) -- Mateusz Kamycki
* Added Placeholder admin plugin endpoints (#6465) (bf1af91bf) -- Aiky30
* Refactored plugin tree (#6437) (83d38dbb2) -- Paulo Alvarado
* Register Placeholder model with admin (#6458) (5a1c89316) -- Aiky30
* Removed placeholder content fallbacks (#6456) (a9947fed1) -- Aiky30
* Added Generic Foreign Key field to Placeholder model (#6452) (0aedfbbd1) -- anirbanlahiri-fidelity
* Removed revert to live feature (#6454) (1d7894684) -- Aiky30
* Removed publisher_publish management command (#6453) (cb19c6069) -- monikasulik
* Removed publish / unpublish buttons from page changelist (#6445) (9905ca6ec) -- Aiky30
* Introduced Django 2.0 & 2.1 support (#6447) (30f2d28cc) -- Paulo Alvarado
* Removed logic which publishes the first page page as soon as it is created (#6446) (cf442f756) -- Aiky30
* Removed unpublish button from toolbar (#6438) (14110d067) -- Aiky30
* Moved placeholders from Page to Title model (#6442) (37082d074) -- Aiky30
* Added app registration integration for wizards (#6436) (c8f56a969) -- monikasulik
* Log all page and placeholder operations (#6419) (039415336) -- Aiky30
* Added request to page create form (#6425) (61150ed91) -- Paulo Alvarado
* Introduced app registration system (#6421) (97515c81d) -- monikasulik
* Update apphooks.rst (#6255) (98380b5d7) -- Chematronix
* Removed Publish button from the toolbar (#6414) (41c4ab0dc) -- Aiky30

Bug Fixes:
----------
* Structure mode toggle button disappearing from toolbar (#7272) (7dafe846a) -- Fabian Braun
* Placeholder copy orphaned plugin children (#7065) (#7131) (39483cf32) -- Aiky30
* Update support options in README.rst (#7059) (22395d7c5) -- Simon
* Fix being able to reset the setting PageContent.limit_visibility_in_menu (#7016) (66c70394c) -- Aiky30
* Patch defects (#6930) (d88932559) -- Adam Murray
* Pagecontent template not changing when the UI option is changed (#6921) (68947484a) -- Aiky30
* Replace deprecated Jquery .load() call with .on('load', (#6922) (c9cd9fbf2) -- Aiky30
* Added missing softroot to the migration copy from Page to PageContent (#6888) (c8fbde737) -- Aiky30
* Display the correct url in change_language_menu (#6828) (026ff1c86) -- Jonathan Sundqvist
* Prevent JS injection in the admin add plugin url (#6885) (72025947d) -- Aiky30
* Fix 'urls.W001' warning with custom apphook urls  (#6874) (75978fb1c) -- Aiky30
* Override urlconf_module so that Django system checks don't crash. (#6873) (f1226a57b) -- Aiky30
* ``get_object`` call was missing request argument (#7302) (98959dc12) -- Mark Walker
* page tree display and status alignment (#7263) (914558d28) -- Mark Walker
* Removed bad migration character (#6834) (d6cabc49f) -- Aiky30
* Remove exclude as no longer supported (#6830) (7aeacb045) -- Jonathan Sundqvist
* Replaced incorrect model being saved when a foreign key to placeholder is remapped to use the generic foreign key (#6802) (5bfb1d144) -- Aiky30
* Raise 404 on when page has no content (#6803) (8e7cdb12d) -- Jonathan Sundqvist
* Fix add translation form, as AddPageForm expects cms_page parameter (#6534) (017a7e472) -- Krzysztof Socha
* Fixed a bug with deleting a model from changelist inside modal (597488954) -- Vadim Sikora
* Fix data validation (085ab6d13) -- Krzysztof Socha
* Failing log entry tests (59441e5a5) -- Paulo
* Broken migration (3c3bf884b) -- Paulo
* Page list language switcher bugs (cfeb3a74c) -- Paulo
* Missing permissions bug (ba60a1c3a) -- Paulo
* Fixed a bug with expanding static placeholder by clicking on "Expand All" button (e0c940ce3) -- Vadim Sikora
* Fixed a bug with not enabling plugins that are not rendered in content (dca32358a) -- Vadim Sikora

Statistics:
-----------

This release includes 107 pull requests, and was created with the help of the following contributors (in alphabetical order):

* Aiky30 (35 pull requests)
* Krzysztof Socha (17 pull requests)
* Paulo Alvarado (12 pull requests)
* Vadim Sikora (11 pull requests)
* Jonathan Sundqvist (7 pull requests)
* Mark Walker (6 pull requests)
* Paulo (6 pull requests)
* Malinda Perera (3 pull requests)
* monikasulik (3 pull requests)
* Adam Murray (2 pull requests)
* Chematronix (1 pull request)
* Fabian Braun (1 pull request)
* Mateusz Kamycki (1 pull request)
* Simon (1 pull request)
* anirbanlahiri-fidelity (1 pull request)


With the review help of the following contributors:

* Adam Murray
* Aiky30
* Angelo Dini
* Krzysztof Socha

Thanks to all contributors for their efforts!

3.6.0 (2019-01-29)
==================

* Introduced Django 2.2 support.
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

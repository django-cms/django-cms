# Changes from 3.x

## Main differences to django CMS 3.x

The main differences to note in the core CMS which is now extremely simplified are:

- No concept of publishing, removed because it was limited to just draft and live. An opinionated implementation is now accomplished through djangocms_versioning. Many new concepts exist in this application. The reason that the publishing is external is due to the fact that it is an opinionated implementation. If it is agreed as the way forward by the community it could potentially be brought in as an internal app that compliments the core codebase, similar to how Django is organised internally.
- CMS app config, allows other apps to customise / control other apps by enabling or disabling features.
- Dedicated Edit, Preview and Structure endpoints, this allows any applications using Placeholders inside or outside of the CMS (djangocms_alias) to use the same editing experience.
- New plugin architecture, simplified and no reliance on treebeard which was problematic in the past.
- Static placeholders are being replaced by djangocms_alias because static placeholders cannot be versioned or allow moderation.


| Topic                                                                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New Plugin Architecture (Backend)                                         | Treebeard was previously used. Treebeard only used for pagetree. Migration possible, simple                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Placeholder field relations                                               | Affected for programmed placeholder fields. Now better to know what plugin is stored where. Should still work on a migration, source is backwards compatible                                                                                                                                                                                                                                                                                                                                                   |
| Pages and titles                                                          | Placeholders are now separated into languagesBefore you had one placeholder per page for all languages now it is 3placeholders for 3 languages                                                                                                                                                                                                                                                                                                                                                                 |
| Title is now “page contents”                                              | Basic settings were stored in the title object and advanced settings in the page object. Title is now PageContentSome settings have been moved to PageContent. For example templates can now be set as PageContent meaning if you have different languages each language can have a different template. Should be fine but might eventually require  work                                                                                                                                                              |
| Changes in how we store the URL information                               | Slug and path is now stored outside of PageContentIs now stored in PageUrlShould be migrated to new system                                                                                                                                                                                                                                                                                                                                                                                                     |
| Publishing of django CMS has been removed                                 | Draft and live pages don’t exist anymore. Migration is possible and has been achieved.                                                                                                                                                                                                                                                                                                                                     |
| ?edit has been removed                                                    | There are 3 new endpoints to change contentLive version of the page. Edit button that goes to versioning. Preview view of a websiteKeep ?edit would the same as ?toolbar_on. Should be migrated to new system                                                                                                                                                                                                                                                                                                        |
| New system to interact between addons via CMSAppConfig andCMSAppExtension | Is a new systemBackwards compatibility is available                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Disabled Features – Backwards Incompatible                                | Page types have been disabled. Why has it been removed, alternative? GOOD Default plugins per placeholder on render (if the placeholder isempty check if it has configured default plugins > create these on rendertime). Handover 3Kryz working on an add-on to do it on addon level                                                                                                                                                                                                                               |
| Need to continue conversation                                             | A few things have been removed from the core. Removing / deprecating the alias addon. Upgrade path can be added. Default plugins. Feature from placeholder configurations. Plugin inheritance has been removed. If placeholder is empty take the plugins from the parentKeep or remove? Static placeholders will be gone? As plugins cannot be stored the traditional way. Add warning for deprecations that changes will be removed in 4.2 |


## App registration

https://github.com/divio/django-cms/pull/6421 app registration docs in the description of the PR

- Add-ons now make use of a new config system; this is to be migrated to all pools. Add-ons can now define whether they support other addons (such as versioning) as well as provide configuration. This is useful in telling features like versioning how to version an add-on.
- Previously all add-ons would manage their own pool, now it is moving to an app registry based system that will allow centralised control. Although all new add-ons should implement this system the new system will not be depreciated at this time.
- CMSApp is an existing term from v2.5, it is how apphooks are declared in the newer versions of the cms.
- CMSAPPConfig is a class, which defines the configuration for a specific add-on, this is then passed to CMSAppExtension. It provides a way of telling the core that an app wants to access something from another app config (the centralized way of handling app config). For example: Alias wants to tell versioning to version it. This requires two components, versioning must define CMSAppExtension, all it needs to do is implement one method, called `configure_app`, which takes an instance of the CMSAppConfig. In order for an alias app to be linked to it set `app_name_enabled=True`. When the extension is configured like this the cms will take all the config settings and pass them to the relevant extension, specify models that need to be versioned and which apps need to access this config. CMSAppExtension is the way to register the add-ons and in the future plugins (or plugin_pools) with have their configs defined in CMSAPPConfig.

## Versioning

- There is no longer the concept of publishing baked into the core of the CMS. By default any content changes are instantly live with no option to unpublish other than to remove altogether.
- To enable publishing the package djangocms-versioning or other similar package that is Django CMS 4.0+ compatible should be installed.
- The reason that publishing was removed from the core is because the solution baked in made a lot of assumptions that enforced various limitations on developers. By not providing a publishing method it allows developers to provide their own solutions to the publishing
  paradigm.
- Goal is to migrate the monkey patching of versioning into the core to allow a "simple" mode in djangocns-versioning that replaces the 3.x draft/live mode when installing (default option).

djangocms-versioning documentation: https://divio-djangocms-versioning.readthedocs-hosted.com/en/latest/

### djangocms-versioning overrides queries from PageContent

- django CMS Versioning overrides the standard query manager for PageContent by adding the query manager: PublishedContentManagerMixin. https://github.com/divio/djangocms-versioning/blob/429e50d4de6d14f1088cbdba2be63b20c2885be9/djangocms_versioning/managers.py#L4
- By default only published versions are returned from `PageContents.objects.all()`. To get all versions regardless of versioning state you can use the "\_base_manager": `PageContent._base_manager.all()`

```
# Get only published PageContents
PageContent.objects.all()

# Get all PageContents regardless of the versioning status, be careful with this as it can return archived, draft and published versions!
PageContent._base_manager.all()

# Get only draft PageContents
from djangcms-versioning.constants import DRAFT PageContent._base_manager.filter(versions__state=DRAFT)
```

## Disabling the admin sideframe

- The CMS sideframe in the Django admin caused many issues when navigating through different plugins admin views, the experience it offered left the user confused at the page they were currently on after making various changes, it was also buggy at times. Disable the sideframe by adding the following setting in the settings.py file, it is enabled by default. CMS_SIDEFRAME_ENABLED = False

## Plugin refactor

- Plugins used to utilise Treebeard. The Treebeard implementation was not coping with this, it was prone to breakage and tree corruption. The refactor simplifies and avoids this by utilising a parent child relationship with plugins. The main issue when replacing the Treebeard implementation was performance, here the standard Django ORM could not provide the query complexity and performance required, individual implementations for the different SQL dialects was implemented to aid performance of plugin queries.
- Initial plugin refactor: https://github.com/divio/django-cms/commit/83d38dbb2e51b4cb65aff5726a1c415de7a1c376
- Support for other SQL dialects for the plugin tree structure: https://github.com/divio/django-cms/commit /4dfaa1c360c2a15f6572b89fc994a254be9e961d

## Title, Page and Placeholder refactor

There are various changes to the model structure for the Page and PageContents (formerly Title). The most notable is the fact that plugins from different Title instances were all saved in the same Placeholder instance. This has now changed in DjangoCMS 4, a PageContent (formerly Title) instance now contains a dedicated set of Placeholder instances. Please see the illustration below:

### Data model of CMS < 4

- Page
  - Title Language: "EN"
  - Title Language: "DE"
    - Placeholder Slot: "header"
    - Placeholder Slot: "contents"
      - Plugin 1 Language "EN"
      - Plugin 2 Language "DE"

### Data model of CMS >= 4

- Page
  - PageContents Language: "EN"
    - Placeholder Slot: "header"
    - Placeholder Slot: "contents"
      - Plugin 1 Language "EN"
  - PageContents Language: "DE"
    - Placeholder Slot: "header"
    - Placeholder Slot: "contents"
      - Plugin 2 Language "DE"

Page, PageContents (Title) and Placeholder relation refactor: https://github.com/divio/django-cms/commit /37082d074a4e37a9d2114c4236d526529daa1219

## Signals

Page signals have been merged into pre_obj and post_obj signals for operations on Page. Publishing signals have been removed as of DjangoCMS 4.0 but are available in djangocms-versioning: https://github.com/divio/django-cms/commit/03941533670ee9f8c5c078bda8e5cfdd9a639f53

## Log Operations

- Previously the logs created were inconsistent and were not created for all page and placeholder operations. Now all page and placeholder operations are logged in the Django Admin model LogEntry. The logs can also be triggered by external apps via using the signals provided in the CMS. https://github.com/divio/django-cms/commit/03941533670ee9f8c5c078bda8e5cfdd9a639f53

## Placeholder Admin

The placeholder is now responsible for the edit, structure and preview endpoints. This was previously taken care of by appending `?edit`, `?structure` and `?preview`, This change was made to allow objects that weren't pages to be viewed and edited in their own way (Alias is an example of this).

- The views to render the endpoints: render_object_structure, render_object_edit, render_object_preview located at: https://github.com/divio/django-cms/blob/release/4.0.x/cms/views.py#L195 The endpoint is determined by using a reverse look up to the registered admin instance using the toolbar utils: (get_object_preview_url, get_object_structure_url, get_object_edit_url) https://github.com/divio/django-cms/blob/release/4.0.x/cms/toolbar/utils.py#L122 This is due to the addition of versioning. Previously every add-on was responsible for their edit end points which made it impossible for versioning to bring the correct end point for a specific version. You need to specify cms_toolbar_enabled_models attribute, which is a list of tuples in the following format: (model, render function). model - model you want to be editable
- render function - a function that takes django.http.HttpRequest object and an object of the model specified above, and returns a django.http.HttpResponse (or any subclass, like TemplateResponse) object based on provided data. Please note that the preview/edit endpoint has changed. Appending ?edit no longer works. There's a separate endpoint for editing (that the toolbar is aware of and links to when clicking Edit button). One also needs to include `cms_enabled = True` in the cms config, otherwise that cms_toolbar_enabled_models config won’t be passed to the cms.
- PlaceholderAdminMixin is deprecated and has a deprecation notice that it will be removed in the next major release: CMS 5.0. https://github.com/divio /djangocms/blob/release/4.0.x/cms/admin/placeholderadmin.py#L178

### Placeholder relations

TODO: Describe the process of migrating from PlaceholderRelationField

### Preview end-points

### Editing end-points

## Static Placeholders

There is no longer a way to manage the content of Static Placeholders, they were disabled due to the fact that they cannot be versioned or limit control. The functionality that Static Placeholders provided has been superceeded by functionality provided by djangocms-alias.

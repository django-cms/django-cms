## Packages

## django-filer

- versioning-filer adds some oppinionated filer model replacements. This needs to be rethought as we cannot replace all filer models in all plugins (backwards incompatibility). This would hurt the existing addons-ecosystem.

## djangocms-history

- this package will not work anymore in 4.x, instead it's functionality should be integrated into djangocms-versioning (simplistic undo/redo functionality)

## djangocms-url-manager

- djangocms-url-manager redefines how URLs are managed and as such djangocms-link, or any other link plugin, will need to be adapted to its use case. We need to check if this will be part of the core system as well.

## djangocms-moderation

- Further docs on how to use the functionality can be found here: https://github.com/django-cms/djangocms-moderation/tree/release/1.0.x/docs


### Core Packages

| Package                     | Package Name               | Codebase                                                            | Documentation                                                                  |
| --------------------------- | -------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Django CMS CKEditor 4.x     | Djangocms_text_ckeditor    | https://github.com/divio/djangocms-text-ckeditor/tree/support/4.0.x | https://github.com/divio/djangocms-text-ckeditor/blob/support/4.0.x/README.rst |
| Django CMS Alias            | djangocms_alias            | https://github.com/divio/djangocms-alias                            | https://github.com/divio/djangocms-alias/blob/master/README.rst                |
| Django CMS Url Manager      | djangocms_url_manager      | https://github.com/divio/djangocms-url-manager                      | https://github.com/divio/djangocms-url-manager/blob/master/README.rst          |
| Django CMS Versioning       | djangocms_versioning       | https://github.com/divio/djangocms-versioning                       | https://divio-djangocms-versioning.readthedocs-hosted.com/en/latest/           |

### Optional Packages

| Package                     | Package Name               | Codebase                                                            | Documentation                                                                  |
| --------------------------- | -------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Django CMS Moderation       | djangocms_moderation       | https://github.com/divio/djangocms-moderation/tree/release/1.0.x    | https://github.com/divio/djangocms-moderation/tree/release/1.0.x/docs          |
| Django CMS Filer Versioning | djangocms_versioning_filer | https://github.com/divio/djangocms-versioning-filer                 | https://github.com/divio/djangocms-versioning-filer/blob/master/README.rst     |

### Third party opinionated packages

| Package                    | Package Name              | Codebase                                                           | Documentation                                                                             |
| -------------------------- | ------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Django CMS Version Locking | djangocms_version_locking | https://github.com/FidelityInternational/djangocms-version-locking | https://github.com/FidelityInternational/djangocms-version-locking/blob/master/README.rst |
| Django CMS Page Admin      | djangocms_pageadmin       | https://github.com/FidelityInternational/djangocms-pageadmin       | https://github.com/FidelityInternational/djangocms-pageadmin/tree/master/docs             |
| Django CMS Navigation      | djangocms_navigation      | https://github.com/FidelityInternational/djangocms-navigation      | https://github.com/FidelityInternational/djangocms-navigation/blob/master/README.rst      |
| Django CMS References      | djangocms_references      | https://github.com/FidelityInternational/djangocms-references      | https://github.com/FidelityInternational/djangocms-references/tree/master/docs            |
| Django CMS FIL Admin Style | djangocms_fil_admin_style | https://github.com/FidelityInternational/djangocms-fil-admin-style |                                                                                           |

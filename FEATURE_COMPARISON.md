# Feature Comparison: release/build (v5.1.0dev2) vs release/5.0.x (v5.0.5)

## Summary

This document compares the features and changes between the `release/build` branch (version 5.1.0dev2) and the `release/5.0.x` branch (version 5.0.5) of django CMS.

**Key Finding**: The `release/build` branch represents an early development version of 5.1.0 that branches from a specific point in the codebase. The main differences are infrastructure improvements, build system modernization, and **the removal of the legacy StaticPlaceholder model** rather than new CMS features.

**⚠️ BREAKING CHANGE**: The StaticPlaceholder model has been completely removed in release/build. Sites using this feature will need to migrate before upgrading.

## Version Information

- **release/build**: v5.1.0dev2 (Development version for upcoming 5.1.0 release)
- **release/5.0.x**: v5.0.5 (Stable maintenance branch for 5.0.x series)

## Major Features in release/build

### 1. Removal of StaticPlaceholder Model
**Impact**: CRITICAL (Breaking Change)  
**Type**: Major Feature / Deprecation

**BREAKING CHANGE**: The `StaticPlaceholder` model has been completely removed from django CMS.

**Changes**:
- Deleted `cms/models/static_placeholder.py` (77 lines removed)
- Deleted `cms/admin/static_placeholder.py` (15 lines removed)
- Removed `StaticPlaceholder` imports from `cms/models/__init__.py`
- Removed `StaticPlaceholder` admin import from `cms/admin/__init__.py`
- Added migration `0042_remove_placeholderreference_placeholder_ref_and_more.py` to:
  - Remove `placeholder_ref` field from `PlaceholderReference` model
  - Delete the `StaticPlaceholder` model from database

**Impact on Users**:
- **Sites using StaticPlaceholder will break** when upgrading to 5.1.0dev2
- Migration 0042 will delete all StaticPlaceholder data from the database
- Any templates using `{% static_placeholder %}` template tag may need updates
- Any custom code referencing StaticPlaceholder model will need refactoring

**Migration Path**:
- Users must migrate away from StaticPlaceholder before upgrading
- Consider using regular placeholders or alias plugins as alternatives
- Backup StaticPlaceholder data before running migrations

**Note**: This is a legacy feature removal. The StaticPlaceholder feature was hidden behind the `CMS_HIDE_LEGACY_FEATURES` setting in previous versions and is now fully removed in 5.1.0dev2.

### 2. Build System Modernization
**Impact**: High (Infrastructure)  
**Type**: Major Feature

The release/build branch migrates from the legacy `setup.cfg` + `setup.py` configuration to the modern `pyproject.toml` standard (PEP 517/518).

**Changes**:
- Removed `setup.cfg` (68 lines deleted)
- Migrated all package metadata to `pyproject.toml`
- Updated build backend to use `setuptools.build_meta`
- Modernized project metadata structure including:
  - Dependencies declaration
  - Python version requirements (>=3.9)
  - Django version support (4.2, 5.0, 5.1, 5.2, 6.0)
  - Python version support (3.10, 3.11, 3.12, 3.13, 3.14)
  - Entry points for console scripts
  - Tool configurations (flake8, ruff, codespell)

**Benefits**:
- Better alignment with modern Python packaging standards
- Improved dependency management
- Simplified build process
- Better tooling integration

### 3. CI/CD Pipeline Enhancement
**Impact**: Medium (Development Infrastructure)  
**Type**: Major Feature

**PR**: #8439 - "ci: Skip live PyPI publish for tags containing 'dev'"

**Changes**:
- Added conditional logic to skip live PyPI publishing for development tags
- Prevents accidental publishing of development versions to production PyPI
- Improved release safety for development iterations

**Files Modified**:
- `.github/workflows/publish-to-live-pypi.yml`
- Potentially other CI workflow files

**Benefits**:
- Safer development workflow
- Prevents pollution of production package index with dev versions
- Allows for more frequent development releases

### 4. License and Copyright Updates
**Impact**: Medium (Legal/Compliance)  
**Type**: Major Feature

**Changes**:
- Updated copyright attribution to clarify ownership timeline:
  - 2008: Batiste Bieler (original author)
  - 2008-2020: Divio AG and contributors
  - 2020-present: django CMS Association and contributors
- Added comprehensive license information for bundled dependencies
- Included jQuery license notice (MIT License, v1.11.3)
- Added disclaimer about node modules and vendor directories

**Benefits**:
- Improved legal clarity
- Better attribution of project ownership history
- Compliance with open source licensing requirements

## Minor Features in release/build

### 1. Code Refactoring and Organization
**Impact**: Low  
**Type**: Minor Feature

**Changes in `cms/admin/pageadmin.py`**:
- Moved `get_site()` function to `cms.utils.admin.get_site_from_request()`
- Removed duplicate implementation
- Cleaned up imports:
  - Removed unused `Site` import from `django.contrib.sites.models`
  - Removed unused `ObjectDoesNotExist` exception import
  - Added `ModelForm` import from `django.forms`

**Benefits**:
- Better code organization
- Reduced code duplication
- Improved maintainability

### 2. Workflow Configuration Updates
**Impact**: Low  
**Type**: Minor Feature

Various GitHub Actions workflow files received updates:
- Updated Node.js version in `.nvmrc` 
- Modified workflow triggers and conditions
- Updated action versions for security and compatibility
- Enhanced workflow efficiency

**Files Modified**:
- `.github/workflows/codeql.yml`
- `.github/workflows/docs.yml`
- `.github/workflows/frontend.yml`
- `.github/workflows/lint-pr.yml`
- `.github/workflows/linters.yml`
- `.github/workflows/make-release.yml`
- `.github/workflows/new_contributor_pr.yml`
- `.github/workflows/publish-to-test-pypi.yml`
- `.github/workflows/releases.yml`
- `.github/workflows/spelling.yml`
- `.github/workflows/stale.yml`
- `.github/workflows/test.yml`
- `.github/workflows/test_startcmsproject.yml`

### 3. Frontend Tooling Updates
**Impact**: Low  
**Type**: Minor Feature

**Changes**:
- Removed deprecated `.eslintrc.js` (233 lines)
- Updated `.babelrc` configuration
- Modified `webpack.config.js` (228 lines of changes)
- Updated `package.json` and `package-lock.json` with new dependencies
- Added `playwright.config.js` for end-to-end testing support
- Updated `.gitignore` with 6 new entries

**Benefits**:
- Modern frontend build tooling
- Better testing infrastructure
- Improved developer experience

### 4. Localization Updates
**Impact**: Low  
**Type**: Minor Feature

**Changes**:
- Updated German translations (`cms/locale/de/LC_MESSAGES/django.po`, `djangojs.po`)
- Updated English translations (`cms/locale/en/LC_MESSAGES/django.po`)
- Recompiled message catalogs (.mo files)

**Statistics**:
- English: ~240 lines changed, file size increased from 34KB to 39KB

### 5. Documentation and README Updates
**Impact**: Low  
**Type**: Minor Feature

**Changes**:
- Updated `README.rst` (24 lines modified)
- Updated `CONTRIBUTING.rst` (12 lines modified)
- Various documentation improvements

## Features ONLY in release/5.0.x (NOT in release/build)

The following bug fixes were added to release/5.0.x after the branching point and are NOT present in release/build:

### Bug Fixes in 5.0.5 (Missing from release/build)
1. **fix**: Improved UX for external placeholders (e.g., static aliases) (#8416, #8435)
2. **fix**: ApphookReloadMiddleware not handling new language variants #2 (#8401, #8412)
3. **fix**: Copying failed if a target placeholder was missing (#8399, #8410, #8402)
4. **fix**: Save fallback for includes when scanning for placeholders (#8405, #8407)
5. **fix**: Ensure edit endpoint language selection when admin is not using i18n_patterns (#8367, #8390)
6. **fix**: Copying x-language lead to unique constraint violation (#8366, #8386)
7. **fix**: Avoid escaping (= stringify) None-values in PageAttribute-TemplateTag (#8375, #8384)
8. **fix**: Fix default value for edit_fields parameter to avoid AttributeError (#8381)
9. **fix**: Link syntax in welcome.html
10. **fix**: Searching pages for language-specific content failed due to wrong search queryset (#8355, #8358)

### Bug Fixes in 5.0.4 (Missing from release/build)
1. **fix**: Wrong placeholders rendered when using apphooks with own placeholders (#8343, #8348)

## Code Statistics

### Lines Changed
```
386 files changed
24,392 insertions(+)
43,400 deletions(-)
Net: -19,008 lines (reduction in code size)
```

### Major File Categories Changed
- Python source files: Extensive changes in cms/ directory
- Migration files: Updated for consistency
- Frontend assets: package-lock.json significantly reorganized
- Configuration files: Modernized build and CI configuration
- Localization files: Updated translations

## Recommendations

### For Users
1. **If using release/5.0.x**: This is the stable branch with the latest bug fixes. Recommended for production.
2. **If using release/build**: This is a development version. Use only for testing future features and providing feedback.

### For Developers
1. **Backport Needed**: The 11+ bug fixes from release/5.0.x should be cherry-picked/merged into release/build to ensure it has the latest stability fixes.
2. **Testing Required**: The build system modernization needs thorough testing to ensure packaging and distribution work correctly.
3. **CI/CD Validation**: Test the new PyPI publishing logic with actual dev tag releases.

## Conclusion

The `release/build` branch (5.1.0dev2) is primarily focused on **infrastructure modernization** rather than new CMS features:

### Major Improvements
1. ✅ **BREAKING**: Removal of legacy StaticPlaceholder model
2. ✅ Modern Python packaging (pyproject.toml)
3. ✅ Enhanced CI/CD pipeline safety
4. ✅ Updated legal/copyright clarity
5. ✅ Frontend tooling modernization

### Notable Absences
1. ❌ **No new CMS end-user features** compared to 5.0.0
2. ❌ **Missing recent bug fixes** from 5.0.x branch (11 fixes from v5.0.3-5.0.5)
3. ❌ No new admin interface improvements
4. ❌ No new template tags or features
5. ❌ No new API endpoints

### Version Strategy
The 5.1.0 development version appears to be a **consolidation and modernization release** that prepares the codebase for future development by:
- **Removing legacy features** (StaticPlaceholder)
- Adopting modern Python packaging standards
- Improving CI/CD infrastructure
- Cleaning up technical debt
- Setting the stage for future feature additions

**Important**: The StaticPlaceholder removal is a **breaking change** that requires migration planning for sites using this feature.

**Next Steps**: The release/build branch should merge the latest fixes from release/5.0.x before proceeding with new feature development for a true 5.1.0 release.

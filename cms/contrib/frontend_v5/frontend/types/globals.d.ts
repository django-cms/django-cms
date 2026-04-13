/*
 * Ambient declarations for runtime globals provided by Django admin and
 * its extensions. These are NOT imported — they exist on `window` at
 * runtime because Django admin loads its own scripts on admin pages, and
 * our bundles run alongside those scripts in the same page.
 *
 * Declaring them here keeps strict-mode TypeScript happy without
 * requiring a runtime import (which would produce a bundler error,
 * because no npm package provides them).
 */

/**
 * Optional CJK → ASCII transliterator from a Django admin extension.
 * If present, Django admin sets it up on the window global and exposes
 * a factory (`window.unihandecode.Unihan`) that returns an object with a
 * `.decode(str)` method. If absent, the slug widget falls back to plain
 * URLify, which already handles basic ASCII/Latin cases.
 */
interface UnihanDecoder {
    decode(value: string): string;
}

interface UnihandecodeGlobal {
    Unihan(decoderName?: string): UnihanDecoder;
}

declare global {
    /**
     * Webpack DefinePlugin constant — string-replaced at build time
     * with the CMS_VERSION read from cms/__init__.py. Used by
     * currentVersionMatches() to detect stale cached settings.
     */
    const __CMS_VERSION__: string;

    /**
     * Django admin's URL slugifier, defined in Django's urlify.js.
     * Converts free-text to a URL-safe slug, optionally capped at
     * `numChars` characters. Available on every Django admin page.
     *
     * Source: https://github.com/django/django/blob/main/django/contrib/admin/static/admin/js/urlify.js
     */
    function URLify(value: string, numChars?: number): string;

    /**
     * Django's i18n gettext global, loaded from the `jsi18n` view on
     * admin pages that request it. Declared as possibly-undefined
     * because not every admin page includes jsi18n — call sites must
     * guard with `typeof gettext === 'function'` or `gettext?.(…)`.
     *
     * Source: https://docs.djangoproject.com/en/stable/topics/i18n/translation/#internationalization-in-javascript-code
     */
    const gettext: ((message: string) => string) | undefined;

    interface Window {
        unihandecode?: UnihandecodeGlobal;
        /**
         * Set by slug.ts after Django admin's unihandecode has been
         * instantiated. Reused across the session for the active locale.
         */
        UNIHANDECODER?: UnihanDecoder;

        /**
         * Django admin related-object popup helpers. `showRelatedObjectPopup`
         * exists on modern Django admin (used as a presence sentinel to
         * decide whether to append `?_popup=1` to add-another URLs).
         * `showAddAnotherPopup` is the older companion that opens the
         * popup window; django-cms still invokes it directly.
         */
        showRelatedObjectPopup?: (triggeringLink: HTMLElement) => void;
        showAddAnotherPopup?: (triggeringLink: HTMLElement) => void;

        /**
         * The `window.CMS` namespace — public API surface third-party
         * apps may depend on. Individual bundle entries attach class
         * exports (e.g. `PageSelectWidget`) here. The shape is
         * intentionally open-ended: anything attached is reachable at
         * runtime, and TypeScript doesn't need to know every property
         * that might be set by other bundles compiled alongside the one
         * being checked.
         */
        CMS?: CmsGlobal;

        /** jQuery global — set by admin.base.ts if absent (decision 7). */
        jQuery?: JQueryStatic;
        /** jQuery shorthand alias — set by admin.base.ts if absent. */
        $?: JQueryStatic;
    }

    interface CmsGlobal {
        /**
         * Legacy `CMS.API` namespace — a grab-bag for public JS API
         * methods exposed to inline scripts in templates and to
         * third-party apps. Individual bundles attach their methods
         * here as they're migrated (e.g. `CMS.API.changeLanguage` from
         * admin.changeform). Shape is intentionally open-ended so
         * future bundles can add their own methods without needing to
         * coordinate type declarations.
         */
        API?: CmsApi;

        /**
         * Server-rendered config blob, populated by an inline
         * template script BEFORE any bundle runs. Contains URLs,
         * settings, permissions, csrf token, etc. Shape is
         * intentionally narrow — only the fields the ported modules
         * actually read. Wider than this is possible at runtime; use
         * `CMS.config[key] as T` with a cast when consuming untyped
         * keys.
         */
        config?: CmsConfig;

        /**
         * jQuery event-bus root — set by cms-base.ts at DOM-ready time
         * to `$('#cms-top')`. The pub/sub event helpers hook their
         * .on()/.trigger() calls here. Typed loosely because the
         * jQuery type would require a bundle-wide jquery import.
         */
        _eventRoot?: unknown;

        /**
         * Array of plugin instances populated by cms.plugins (when
         * ported). cms-base.ts reads it in `_pluginExists()`. Loose
         * typing because the shape is owned by cms.plugins, not
         * cms-base.
         */
        _instances?: Array<{
            options: { plugin_id?: string | number; type?: string };
        }>;

        /** User settings persisted by setSettings/getSettings. */
        settings?: Record<string, unknown>;

        /** jQuery handle, aliased by admin.base.ts. */
        $?: unknown;

        [key: string]: unknown;
    }

    /**
     * Narrow shape of `window.CMS.config`. Only fields that ported
     * modules actually read. If you need a field not listed here,
     * add it — better to type new fields than to weaken the typing.
     */
    interface CmsConfig {
        /** CMS version string for currentVersionMatches() comparisons. */
        version?: string;
        /** User settings blob, merged into localStorage by setSettings. */
        settings?: Record<string, unknown>;
        /** URL map — setSettings posts to `urls.settings` when localStorage is unavailable. */
        urls?: {
            settings?: string;
            [key: string]: string | undefined;
        };
        /** CSRF token used by legacy $.ajax calls. */
        csrf?: string;
        /** Initial color scheme preference — 'auto' | 'light' | 'dark'. */
        color_scheme?: string;
        [key: string]: unknown;
    }

    interface CmsApi {
        /**
         * Navigate to another language tab on the page change form.
         * Shows a confirm() dialog if the title or slug has unsaved
         * edits, otherwise navigates directly. Set up by the
         * admin.changeform bundle; called from the inline template
         * script in `admin/cms/page/change_form.html`.
         */
        changeLanguage?: (url: string) => void;

        /**
         * Populated by cms-base.ts when admin.base runs. Most
         * downstream modules attach their own methods/classes to
         * `CMS.API` as they initialise — `Helpers` is the first such
         * attachment.
         */
        Helpers?: unknown;

        /**
         * Populated by cms.structureboard (when ported). Used by
         * cms-base.ts's `onPluginSave()` to invalidate state after
         * a plugin save. Pass-through reference — we don't own the
         * interface here.
         */
        StructureBoard?: {
            invalidateState?: (action: string, data: unknown) => void;
        };

        /**
         * Populated by cms-base.ts's settings-persistence helpers
         * when a synchronous-equivalent operation is in flight. NOT
         * used by the ported cms-base.ts (we dropped the sync-ajax
         * fallback), but some legacy modules check this flag so we
         * expose it as a field for compat.
         */
        locked?: boolean;

        /**
         * Populated by cms.messages (when ported). `onPluginSave` /
         * `setSettings` / `getSettings` open error messages through
         * it on failure. Optional because it's undefined until the
         * messages module initialises.
         */
        Messages?: {
            open?: (options: { message: string; error?: boolean }) => void;
        };

        [key: string]: unknown;
    }
}

export {};

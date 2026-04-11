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
     * Django admin's URL slugifier, defined in Django's urlify.js.
     * Converts free-text to a URL-safe slug, optionally capped at
     * `numChars` characters. Available on every Django admin page.
     *
     * Source: https://github.com/django/django/blob/main/django/contrib/admin/static/admin/js/urlify.js
     */
    function URLify(value: string, numChars?: number): string;

    interface Window {
        unihandecode?: UnihandecodeGlobal;
        /**
         * Set by slug.ts after Django admin's unihandecode has been
         * instantiated. Re-used across the session for the active locale.
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
    }

    interface CmsGlobal {
        [key: string]: unknown;
    }
}

export {};

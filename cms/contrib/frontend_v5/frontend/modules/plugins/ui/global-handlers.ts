/*
 * Document-level handlers shared by every Plugin instance.
 *
 * Mirrors legacy `Plugin._initializeGlobalHandlers`. Call once per
 * page (idempotent — re-calling re-binds against the same flag).
 *
 * What's wired
 * ────────────
 *   - Shift keydown / keyup → `expandmode` flag (read by collapse +
 *     content-events for nested expand/highlight behaviour).
 *   - Window blur → clear `expandmode` (safety net for alt-tab).
 *   - Document pointerup → close the open settings menu.
 *   - Click on `.cms-plugin a` → debounced single-click → window.open
 *     (legacy "double-click to edit, single-click to follow link"
 *     gate). Skipped when shift / ctrl / cmd is held.
 *   - Click on `.cms-dragarea-static .cms-dragbar` → toggle the
 *     `cms-dragarea-static-expanded` class.
 *
 * Tooltip + click-to-highlight wiring lives in `highlight.ts` because
 * it depends on the heavy positioning helper there.
 */

import { hideSettingsMenu } from './menu';

const EXPANDMODE_KEY = '__cmsExpandMode__';
interface ExpandModeWindow {
    [EXPANDMODE_KEY]?: boolean;
}

/**
 * Read the global expand-mode flag (true while shift is held).
 * Replaces the legacy `$document.data('expandmode')` lookup.
 */
export function isExpandMode(): boolean {
    return Boolean((window as ExpandModeWindow)[EXPANDMODE_KEY]);
}

/**
 * Set / clear the global expand-mode flag. Exported so tests + the
 * structureboard port can drive it without depending on a real shift
 * keydown.
 */
export function setExpandMode(on: boolean): void {
    (window as ExpandModeWindow)[EXPANDMODE_KEY] = on;
}

const SHIFT_KEY = 'Shift';
const DOUBLECLICK_DELAY_MS = 300;

let abortController: AbortController | null = null;

/**
 * Bind document-level handlers shared by every Plugin instance.
 * Idempotent — calling more than once is a no-op. Listeners are
 * tracked via an internal `AbortController` so test code can detach
 * them via `_resetGlobalHandlersForTest`.
 */
export function initializeGlobalHandlers(): void {
    if (abortController) return;
    abortController = new AbortController();
    const opts = { signal: abortController.signal };

    // Shift expand-mode flag.
    document.addEventListener(
        'keydown',
        (e: KeyboardEvent) => {
            if (e.key !== SHIFT_KEY) return;
            setExpandMode(true);
        },
        opts,
    );
    document.addEventListener(
        'keyup',
        (e: KeyboardEvent) => {
            if (e.key !== SHIFT_KEY) return;
            setExpandMode(false);
        },
        opts,
    );
    window.addEventListener('blur', () => setExpandMode(false), opts);

    // Pointerup anywhere outside an open menu closes it.
    document.addEventListener('pointerup', () => hideSettingsMenu(), opts);

    // Single-click on a link inside / around a plugin: defer the
    // navigation so a double-click can pre-empt and open the editor
    // instead. Modifier-key combinations bypass this gating.
    let timer: ReturnType<typeof setTimeout> | null = null;
    let clickCounter = 0;
    const linkSelector = '.cms-plugin a, a:has(.cms-plugin), a.cms-plugin';
    document.addEventListener(
        'click',
        (e: MouseEvent) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const anchor = target.closest<HTMLAnchorElement>(linkSelector);
            if (!anchor) return;
            if (e.shiftKey || e.ctrlKey || e.metaKey || e.defaultPrevented) return;
            e.preventDefault();
            clickCounter += 1;
            if (clickCounter === 1) {
                timer = setTimeout(() => {
                    clickCounter = 0;
                    const href = anchor.getAttribute('href') ?? '';
                    const targetAttr = anchor.getAttribute('target') ?? '_self';
                    window.open(href, targetAttr);
                }, DOUBLECLICK_DELAY_MS);
            } else {
                if (timer !== null) clearTimeout(timer);
                timer = null;
                clickCounter = 0;
            }
        },
        opts,
    );

    // Static-placeholder dragbar toggle.
    document.addEventListener(
        'click',
        (e: MouseEvent) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const dragbar = target.closest('.cms-dragbar');
            if (!dragbar) return;
            const placeholder = dragbar.closest('.cms-dragarea');
            if (!placeholder?.classList.contains('cms-dragarea-static')) return;
            if (
                placeholder.classList.contains('cms-dragarea-static-expanded') &&
                e.defaultPrevented
            ) {
                return;
            }
            placeholder.classList.toggle('cms-dragarea-static-expanded');
        },
        opts,
    );
}

/**
 * Test/migration hook: detach every document-level listener and
 * forget that initializeGlobalHandlers ran. Used by vitest so
 * listeners don't accumulate across test cases.
 */
export function _resetGlobalHandlersForTest(): void {
    abortController?.abort();
    abortController = null;
    setExpandMode(false);
}

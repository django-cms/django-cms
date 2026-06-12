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
 *   - Click on `.cms-plugin:not([class*=cms-render-model])` → ask
 *     structureboard to highlight the matching plugin.
 *   - Pointerover/out + touchstart on `.cms-plugin` → tooltip toggle.
 *   - Click on `.cms-dragarea-static .cms-dragbar` → toggle the
 *     `cms-dragarea-static-expanded` class.
 *   - Initial clipboard populate (legacy `_updateClipboard` +
 *     `Clipboard.populate` on a setTimeout-0).
 */

import { getPluginData } from '../cms-data';
import {
    getClipboard,
    getPluginsRegistry,
    getTooltip,
} from '../cms-globals';
import { findPluginById } from '../registry';
import { tryEditPlugin } from './content-events';
import { clickToHighlightHandler } from './highlight';
import { hideSettingsMenu } from './menu';
import { isMultiPlugin } from './setup';

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

    // Double-click on `.cms-plugin-<id>` → open edit modal. Single
    // delegated listener resolves the matched plugin id from the
    // class list, looks up the instance, and calls editPlugin.
    // Replaces the per-instance `document.addEventListener` legacy
    // wired in `_setPluginContentEvents`.
    document.addEventListener(
        'dblclick',
        (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const match = target.closest('.cms-plugin:not(.cms-slot)');
            if (!match) return;
            // Pull plugin id from class.
            let id: number | undefined;
            for (const cls of Array.from(match.classList)) {
                const m = /^cms-plugin-(\d+)$/.exec(cls);
                if (m && m[1]) {
                    id = Number(m[1]);
                    break;
                }
            }
            if (id === undefined) return;
            // Multi-plugin wrappers (the same node carries several
            // descriptors) are ambiguous — skip.
            if (isMultiPlugin(match)) return;
            const plugin = findPluginById(id);
            if (!plugin) return;
            tryEditPlugin(plugin, match, e);
        },
        opts,
    );

    // Click on a content-mode plugin → ask structureboard to scroll/
    // highlight the matching tree entry. Render-model blocks (which
    // overlay non-plugin content) are excluded.
    document.addEventListener(
        'click',
        (e: MouseEvent) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const plugin = target.closest('.cms-plugin');
            if (!plugin) return;
            // Match legacy `:not([class*=cms-render-model])`.
            for (const cls of Array.from(plugin.classList)) {
                if (cls.includes('cms-render-model')) return;
            }
            clickToHighlightHandler();
        },
        opts,
    );

    // Tooltip on hover / touch over a `.cms-plugin`.
    const tooltipHandler = (e: Event): void => {
        e.stopPropagation();
        const target = e.target;
        if (!(target instanceof Element)) return;
        const pluginEl = target.closest<HTMLElement>('.cms-plugin:not(.cms-slot)');
        if (!pluginEl) return;
        const data = getPluginData(pluginEl)?.[0];
        if (!data) return;
        if (e.type === 'touchstart') {
            const tooltip = getTooltip() as
                | { _forceTouchOnce?: () => void }
                | undefined;
            tooltip?._forceTouchOnce?.();
        }
        const id = data.plugin_id;
        const type = data.type;
        if (type === 'generic') return;
        let name = (data.plugin_name as string | undefined) ?? '';
        // Prepend placeholder name when the plugin lives inside one.
        if (id !== undefined && id !== null) {
            const draggable = document.querySelector<HTMLElement>(
                `.cms-draggable-${id}`,
            );
            const dragareaCls = Array.from(
                draggable?.closest('.cms-dragarea')?.classList ?? [],
            ).find((c) => /^cms-dragarea-\d+$/.test(c));
            const placeholderId = dragareaCls?.match(/(\d+)$/)?.[1];
            if (placeholderId) {
                const placeholder = document.querySelector<HTMLElement>(
                    `.cms-placeholder-${placeholderId}`,
                );
                const placeholderData = placeholder
                    ? getPluginData(placeholder)?.[0]
                    : undefined;
                const placeholderName =
                    (placeholderData?.name as string | undefined) ?? '';
                if (placeholderName) name = `${placeholderName}: ${name}`;
            }
        }
        const tooltip = getTooltip();
        const show = e.type === 'pointerover' || e.type === 'touchstart';
        const tip = tooltip as
            | {
                  displayToggle?: (
                      show: boolean,
                      target: Event,
                      name: string,
                      id?: number | string,
                  ) => void;
              }
            | undefined;
        if (id !== undefined && id !== null) {
            tip?.displayToggle?.(show, e, name, id);
        } else {
            tip?.displayToggle?.(show, e, name);
        }
    };
    for (const type of ['pointerover', 'pointerout', 'touchstart']) {
        document.addEventListener(type, tooltipHandler, opts);
    }

    // Initial clipboard populate. Legacy uses a setTimeout(0) so
    // structureboard finishes initialising first.
    setTimeout(() => populateClipboardOnLoad(), 0);
}

/**
 * Re-read the clipboard plugin's draggable element. No longer cached
 * — kept as a thin wrapper for legacy `Plugin._updateClipboard`
 * call sites. The cache that legacy held went stale after
 * structureboard re-renders.
 */
export function updateClipboard(): HTMLElement | null {
    return document.querySelector<HTMLElement>('.cms-draggable-from-clipboard');
}

function populateClipboardOnLoad(): void {
    const clipboard = updateClipboard();
    if (!clipboard) return;
    const idCls = Array.from(clipboard.classList).find((c) =>
        /^cms-draggable-/.test(c),
    );
    const id = idCls?.match(/cms-draggable-(\d+)/)?.[1];
    if (!id) return;
    const descriptor = getPluginsRegistry().find(
        ([key]) => key === `cms-plugin-${id}`,
    )?.[1];
    const html = clipboard.parentElement?.innerHTML ?? '';
    getClipboard()?.populate?.(html, descriptor);
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

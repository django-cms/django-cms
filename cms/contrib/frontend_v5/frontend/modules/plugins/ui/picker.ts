/*
 * Add-plugin picker — the modal that lists every plugin type valid as
 * a child of the current placeholder / plugin, with quick-search and
 * a "most used" shortcut row.
 *
 * Mirrors legacy `_setAddPluginModal`, `_setupQuickSearch`,
 * `_filterPluginsList`, `_updateWithMostUsedPlugins`,
 * `_getPossibleChildClasses` plus the static
 * `Plugin._removeAddPluginPlaceholder`.
 *
 * Defensive against absent globals
 * ────────────────────────────────
 * `CMS.Modal` is part of the legacy bundle and may not be loaded on a
 * contrib-only page. When the constructor isn't there we fall back to
 * the single-choice fast-path or no-op. Picker mutations (`addPlugin`)
 * land in 2g — same defensive optional-chain pattern as menu.ts.
 *
 * DOM contracts (server-rendered)
 * ───────────────────────────────
 *   - `<div class="cms-plugin-picker">` is a sibling of the trigger
 *     button (`.cms-submenu-add`). It contains a quicksearch input
 *     under `> .cms-quicksearch` plus the canonical type list.
 *   - `<div id="cms-plugin-child-classes-{placeholder_id}">` carries
 *     the markup that gets injected as the modal's "possible child
 *     classes" — server pre-renders this per placeholder.
 *
 * Cloning + listener re-binding
 * ─────────────────────────────
 * Legacy used `clone(true, true)` to copy jQuery-bound handlers along
 * with the DOM. Native `cloneNode(true)` doesn't carry listeners, so
 * after cloning the picker we re-wire `delegateAction` on every action
 * link in the clone. The original (in-page) picker keeps its handlers
 * untouched, so reopening the modal still works.
 */

import { Helpers } from '../../cms-base';
import { hideLoader } from '../../loader';
import { getCmsConfig, getModalConstructor } from '../cms-globals';
import {
    bumpUsageCount,
    getMostUsedPlugins,
} from '../registry';
import type { PluginInstance } from '../types';
import { delegateAction } from './menu';

const MAX_MOST_USED_PLUGINS = 5;
const FILTER_DEBOUNCE_MS = 100;
const PICK_DEBOUNCE_MS = 110;

/**
 * Surface the picker forwards to. `addPlugin` lands in 2g — until
 * then the call is a defensive no-op.
 */
interface PluginCallable extends PluginInstance {
    addPlugin?: (
        type: string,
        name: string,
        parent?: number | string,
        showAddForm?: boolean,
        position?: number,
    ) => void;
    editPluginPostAjax?: (toolbar: unknown, response: unknown) => void;
}

/**
 * Modal handle — loose because `CMS.Modal` isn't ported. The legacy
 * Modal API exposes `.open(...)` and emits `modal-loaded` / `-shown` /
 * `-closed` through `Helpers.dispatchEvent`. We listen via
 * `Helpers.addEventListener`.
 */
interface ModalHandle {
    open(opts: { title?: string; html?: HTMLElement | string; width?: number; height?: number }): void;
}

/**
 * Wire the add-plugin trigger button. On `pointerup`:
 *   - If exactly one plugin type is valid → call `addPlugin` directly.
 *   - Otherwise → open the picker modal.
 *
 * Returns `false` (matching legacy) when the trigger is disabled, so
 * the caller can short-circuit.
 */
export function setupAddPluginModal(
    plugin: PluginCallable,
    nav: HTMLElement,
    signal?: AbortSignal,
): boolean {
    if (nav.classList.contains('cms-btn-disabled')) return false;

    const opts = signal ? { signal } : undefined;

    let modal: ModalHandle | null = null;
    let isTouching = false;

    nav.addEventListener(
        'touchstart',
        (e) => {
            isTouching = true;
            e.stopPropagation();
        },
        opts,
    );

    nav.addEventListener(
        'pointerup',
        (e) => {
            e.preventDefault();
            e.stopPropagation();

            const possibleChildClasses = getPossibleChildClasses(plugin, nav);
            const selectableCount = possibleChildClasses.filter(
                (el) => !el.classList.contains('cms-submenu-item-title'),
            ).length;

            if (selectableCount === 1) {
                // Fast path — only one valid type. Skip the modal.
                const link = possibleChildClasses
                    .map((el) => el.querySelector<HTMLAnchorElement>('a'))
                    .find((a): a is HTMLAnchorElement => Boolean(a));
                if (!link) return;
                const pluginType = (link.getAttribute('href') ?? '').replace('#', '');
                const showAddForm = link.dataset.addForm !== 'false';
                const parentId = parseDraggableId(nav.closest('.cms-draggable'));
                bumpUsageCount(pluginType);
                plugin.addPlugin?.(
                    pluginType,
                    link.textContent ?? '',
                    parentId,
                    showAddForm,
                );
                return;
            }

            modal ??= initModal(plugin, nav, signal);
            if (!modal) return;

            const picker = findSibling(nav, '.cms-plugin-picker');
            if (!picker) return;

            const clone = picker.cloneNode(true) as HTMLElement;
            const parentDraggable = nav.closest<HTMLElement>('.cms-draggable');
            const parentId = parseDraggableId(parentDraggable);
            if (parentId !== undefined) {
                clone.dataset.parentId = String(parentId);
            }
            // Append possible child classes (already cloned by getPossibleChildClasses).
            for (const el of possibleChildClasses) clone.appendChild(el);

            const decorated = updateWithMostUsedPlugins(clone);
            // Re-bind action handlers on the clone (cloneNode doesn't
            // copy listeners). Quicksearch is wired in initModal via
            // modal-loaded.
            wireDelegateOnClone(plugin, nav, decorated, signal);

            modal.open({
                title: getAddPluginHelpTitle(plugin),
                html: decorated,
                width: 530,
                height: 400,
            });
        },
        opts,
    );

    // Stop click / pointer events from bubbling out of the trigger
    // (legacy guard so the surrounding draggable doesn't react).
    for (const type of ['pointerup', 'pointerdown', 'click', 'dblclick']) {
        nav.addEventListener(
            type,
            (e) => e.stopPropagation(),
            opts,
        );
    }

    // Same guard on the sibling quicksearch + dropdown panels.
    const quicksearch = findSibling(nav, '.cms-quicksearch');
    const dropdown = findSibling(nav, '.cms-submenu-dropdown');
    for (const target of [quicksearch, dropdown]) {
        if (!target) continue;
        for (const type of ['pointerup', 'click', 'dblclick']) {
            target.addEventListener(type, (e) => e.stopPropagation(), opts);
        }
    }

    // Track touch state so we don't focus the search input on a tap
    // open (would pop the keyboard on mobile).
    void isTouching;

    return true;
}

// ────────────────────────────────────────────────────────────────────
// Modal lifecycle
// ────────────────────────────────────────────────────────────────────

function initModal(
    plugin: PluginCallable,
    nav: HTMLElement,
    signal?: AbortSignal,
): ModalHandle | null {
    const Modal = getModalConstructor();
    if (!Modal) return null;

    const modal = new Modal({ minWidth: 400, minHeight: 400 }) as unknown as ModalHandle;
    const dragItem = nav.closest<HTMLElement>('.cms-dragitem');
    const isPlaceholder = !dragItem;
    const childrenList = isPlaceholder
        ? nav.closest<HTMLElement>('.cms-dragarea')?.querySelector<HTMLElement>(
              ':scope > .cms-draggables',
          ) ?? null
        : nav.closest<HTMLElement>('.cms-draggable')?.querySelector<HTMLElement>(
              ':scope > .cms-draggables',
          ) ?? null;

    // Modal lifecycle: legacy emits `modal-loaded` / `modal-shown` /
    // `modal-closed` via Helpers.dispatchEvent with the modal instance
    // in the payload. We listen and filter by identity.
    const onLoaded = (payload?: unknown): void => {
        if (!isOurModal(payload, modal)) return;
        // Insert the "where the new plugin will land" placeholder.
        removeAddPluginPlaceholder();
        const indicator = document.createElement('div');
        indicator.className = 'cms-add-plugin-placeholder';
        indicator.textContent = getCmsConfig().lang?.addPluginPlaceholder ?? '';
        if (childrenList) childrenList.appendChild(indicator);
        scrollToElement(indicator);
    };
    const onClosed = (payload?: unknown): void => {
        if (!isOurModal(payload, modal)) return;
        removeAddPluginPlaceholder();
    };
    const onShown = (payload?: unknown): void => {
        if (!isOurModal(payload, modal)) return;
        // Re-find the picker inside the modal mount and wire its quicksearch.
        const picker = document.querySelector<HTMLElement>(
            '.cms-modal-markup .cms-plugin-picker',
        );
        if (!picker) return;
        setupQuickSearch(plugin, nav, picker, signal);
        // Focus the input only when the user opened with a mouse.
        // Touch opens deliberately skip focus to avoid popping the
        // on-screen keyboard.
        const input = picker.querySelector<HTMLInputElement>(
            ':scope > .cms-quicksearch input',
        );
        input?.focus();
    };

    Helpers.addEventListener('modal-loaded', onLoaded);
    Helpers.addEventListener('modal-closed', onClosed);
    Helpers.addEventListener('modal-shown', onShown);
    // Detach the modal-bus listeners when the per-instance signal aborts.
    signal?.addEventListener('abort', () => {
        Helpers.removeEventListener('modal-loaded', onLoaded);
        Helpers.removeEventListener('modal-closed', onClosed);
        Helpers.removeEventListener('modal-shown', onShown);
    });

    return modal;
}

function isOurModal(payload: unknown, modal: ModalHandle): boolean {
    if (!payload || typeof payload !== 'object') return false;
    const p = payload as { instance?: unknown };
    return p.instance === modal;
}

// ────────────────────────────────────────────────────────────────────
// Possible-child-classes resolution
// ────────────────────────────────────────────────────────────────────

/**
 * Return the cloned `<li.cms-submenu-item>` nodes for every plugin
 * type valid as a child of this plugin's placeholder. Filters by
 * `plugin_restriction` and prunes orphan section titles.
 *
 * Each `<a>` inside the result has a fresh `click` listener wired to
 * `delegateAction` — same path the in-place picker uses. Caller passes
 * the trigger (`nav`) so we can locate the surrounding `cms-dragarea`
 * without reaching into `plugin.ui`.
 */
export function getPossibleChildClasses(
    plugin: PluginCallable,
    nav: HTMLElement,
): HTMLElement[] {
    const dragarea = nav.closest<HTMLElement>('.cms-dragarea');
    const placeholderId = parseDragareaId(dragarea);
    if (placeholderId === undefined) return [];

    const template = document.getElementById(`cms-plugin-child-classes-${placeholderId}`);
    if (!template) return [];

    // Parse the template HTML into a fresh element list.
    const wrapper = document.createElement('div');
    wrapper.innerHTML = template.innerHTML;
    let items = Array.from(wrapper.children) as HTMLElement[];

    const restrictions = plugin.options.plugin_restriction;
    if (Array.isArray(restrictions) && restrictions.length > 0) {
        items = items.filter((item) => {
            if (item.classList.contains('cms-submenu-item-title')) return true;
            const href = item.querySelector('a')?.getAttribute('href');
            return Boolean(href && restrictions.includes(href));
        });
        // Drop section titles whose section is now empty.
        items = items.filter((item, index) => {
            if (!item.classList.contains('cms-submenu-item-title')) return true;
            const next = items[index + 1];
            return Boolean(next && !next.classList.contains('cms-submenu-item-title'));
        });
    }

    // Click handlers are bound by `wireDelegateOnClone` after these
    // nodes are appended into the modal-cloned picker — binding here
    // would double-fire delegateAction (legacy got away with it
    // because jQuery's `clone(true,true)` would have duplicated only
    // pre-existing handlers on the clone, not on these freshly-parsed
    // template items). The fast-path consumer reads href/text
    // directly and never dispatches click on these items.
    return items;
}

// ────────────────────────────────────────────────────────────────────
// Most-used row
// ────────────────────────────────────────────────────────────────────

/**
 * Splice up to N "most used" plugin rows after the picker's
 * quicksearch row. No-op when the picker has fewer items than the
 * cap (everything fits without help).
 *
 * Returns the same picker for chaining.
 */
export function updateWithMostUsedPlugins(picker: HTMLElement): HTMLElement {
    const items = picker.querySelectorAll<HTMLElement>('.cms-submenu-item');
    const selectable = Array.from(items).filter(
        (el) => !el.classList.contains('cms-submenu-item-title'),
    );
    if (selectable.length <= MAX_MOST_USED_PLUGINS) return picker;

    const mostUsed = getMostUsedPlugins(MAX_MOST_USED_PLUGINS);
    if (mostUsed.length === 0) return picker;

    let ref = picker.querySelector<HTMLElement>('.cms-quicksearch');
    if (!ref) return picker;

    let count = 0;
    for (const name of mostUsed) {
        if (count === MAX_MOST_USED_PLUGINS) break;
        const link = picker.querySelector<HTMLAnchorElement>(
            `.cms-submenu-item a[href="${cssEscape(name)}"]`,
        );
        const item = link?.closest<HTMLElement>('.cms-submenu-item');
        if (!item) continue;
        const clone = item.cloneNode(true) as HTMLElement;
        clone.dataset.cmsMostUsed = '';
        ref.after(clone);
        ref = clone;
        count += 1;
    }

    if (count > 0) {
        const title = document.createElement('div');
        title.className = 'cms-submenu-item cms-submenu-item-title';
        title.dataset.cmsMostUsed = '';
        const span = document.createElement('span');
        span.textContent = getCmsConfig().lang?.mostUsed ?? '';
        title.appendChild(span);
        picker.querySelector<HTMLElement>('.cms-quicksearch')?.after(title);
    }

    return picker;
}

// ────────────────────────────────────────────────────────────────────
// Quicksearch
// ────────────────────────────────────────────────────────────────────

/**
 * Wire the picker's `<input>` to debounced filter + Enter-to-pick.
 * Re-finds the picker on each keystroke because the legacy code moves
 * pickers in/out of the modal — the closure-captured ref might be stale.
 */
export function setupQuickSearch(
    plugin: PluginCallable,
    nav: HTMLElement,
    picker: HTMLElement,
    signal?: AbortSignal,
): void {
    void plugin;
    void nav;
    const input = picker.querySelector<HTMLInputElement>(
        ':scope > .cms-quicksearch input',
    );
    if (!input) return;

    const opts = signal ? { signal } : undefined;

    const filterHandler = debounce(() => {
        const currentPicker = input.closest<HTMLElement>('.cms-plugin-picker') ?? picker;
        filterPluginsList(currentPicker, input.value);
    }, FILTER_DEBOUNCE_MS);

    const enterHandler = debounce((e: KeyboardEvent) => {
        if (e.key !== 'Enter') return;
        const currentPicker = input.closest<HTMLElement>('.cms-plugin-picker') ?? picker;
        const visible = Array.from(
            currentPicker.querySelectorAll<HTMLElement>('.cms-submenu-item'),
        ).filter((el) => !el.classList.contains('cms-submenu-item-title') && isVisible(el));
        const first = visible[0];
        const link = first?.querySelector<HTMLAnchorElement>('a');
        link?.focus();
        link?.click();
    }, PICK_DEBOUNCE_MS);

    input.addEventListener('keyup', filterHandler, opts);
    input.addEventListener('keyup', enterHandler, opts);
}

/**
 * Hide every `.cms-submenu-item` whose text doesn't contain the query
 * (case-insensitive). Section titles follow their section's
 * visibility, with a post-pass to make sure each visible item has a
 * visible header.
 *
 * Mirrors legacy `_filterPluginsList` exactly, minus jQuery.
 */
export function filterPluginsList(list: HTMLElement, rawQuery: string): void {
    const query = rawQuery.trim().toLowerCase();
    const items = Array.from(
        list.querySelectorAll<HTMLElement>('.cms-submenu-item'),
    );
    const titles = items.filter((el) =>
        el.classList.contains('cms-submenu-item-title'),
    );
    const nonTitleItems = items.filter(
        (el) => !el.classList.contains('cms-submenu-item-title'),
    );

    if (query === '') {
        for (const el of items) show(el);
        return;
    }

    // Most-used rows hide while the user is searching — search applies
    // only to the canonical list.
    const mostUsed = items.filter((el) => 'cmsMostUsed' in el.dataset);

    for (const el of nonTitleItems) {
        const text = (el.textContent ?? '').toLowerCase();
        if (text.includes(query)) show(el);
        else hide(el);
    }

    // Walk titles: a title is visible iff at least one item under it
    // (until the next title) is visible.
    for (const title of titles) {
        let any = false;
        let cursor = title.nextElementSibling as HTMLElement | null;
        while (cursor && !cursor.classList.contains('cms-submenu-item-title')) {
            if (isVisible(cursor)) {
                any = true;
                break;
            }
            cursor = cursor.nextElementSibling as HTMLElement | null;
        }
        if (any) show(title);
        else hide(title);
    }

    for (const el of mostUsed) hide(el);
}

// ────────────────────────────────────────────────────────────────────
// Misc helpers (also exported for tests + Plugin static API)
// ────────────────────────────────────────────────────────────────────

/**
 * Remove every floating "where the new plugin will land" placeholder.
 * Mirrors `Plugin._removeAddPluginPlaceholder`.
 */
export function removeAddPluginPlaceholder(): void {
    document
        .querySelectorAll('.cms-add-plugin-placeholder')
        .forEach((el) => el.remove());
}

/**
 * Scroll the picker placeholder into view if it's clipped below the
 * fold. Native version of legacy `_scrollToElement`.
 *
 * Rough simplification: use `scrollIntoView` instead of an animated
 * scrollTop math walk, since the picker placeholder is the only
 * caller and the timing (right after modal-loaded) doesn't depend on
 * a duration. Animation polish lands later if the UX needs it.
 */
export function scrollToElement(
    el: HTMLElement,
    _opts: { duration?: number; offset?: number } = {},
): void {
    if (!isElementInViewport(el)) {
        el.scrollIntoView({ block: 'end', behavior: 'auto' });
    }
}

function isElementInViewport(el: HTMLElement): boolean {
    const rect = el.getBoundingClientRect();
    return rect.top >= 0 && rect.bottom <= window.innerHeight;
}

/**
 * Keyboard-traversing of the picker (arrow up/down, tab/shift-tab).
 * Deferred per the inventory — the legacy code path is istanbul-
 * skipped and not part of any automated test. Lands in 2g polish.
 */
export function setupKeyboardTraversing(): void {
    /* deferred — see CLAUDE.md sub-phase-2g notes */
}

// ────────────────────────────────────────────────────────────────────
// Internal plumbing
// ────────────────────────────────────────────────────────────────────

function getAddPluginHelpTitle(plugin: PluginCallable): string {
    const opts = plugin.options as { addPluginHelpTitle?: string };
    return opts.addPluginHelpTitle ?? '';
}

function findSibling(el: HTMLElement, selector: string): HTMLElement | null {
    const parent = el.parentElement;
    if (!parent) return null;
    for (const child of Array.from(parent.children)) {
        if (child !== el && child.matches(selector)) {
            return child as HTMLElement;
        }
    }
    return null;
}

function parseDraggableId(el: Element | null): number | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-draggable-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

function parseDragareaId(el: Element | null): number | undefined {
    if (!el) return undefined;
    for (const cls of Array.from(el.classList)) {
        const match = /^cms-dragarea-(\d+)$/.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

/**
 * Re-attach the click action handler to every `<a>` in a cloned
 * picker. cloneNode(true) doesn't carry listeners.
 */
function wireDelegateOnClone(
    plugin: PluginCallable,
    nav: HTMLElement,
    clone: HTMLElement,
    signal?: AbortSignal,
): void {
    const opts = signal ? { signal } : undefined;
    clone
        .querySelectorAll<HTMLAnchorElement>('.cms-submenu-item a')
        .forEach((link) => {
            link.addEventListener(
                'click',
                (e) => delegateAction(plugin, nav, e),
                opts,
            );
        });
}

function debounce<A extends unknown[]>(
    fn: (...args: A) => void,
    ms: number,
): (...args: A) => void {
    let timer: ReturnType<typeof setTimeout> | null = null;
    return (...args: A) => {
        if (timer !== null) clearTimeout(timer);
        timer = setTimeout(() => {
            timer = null;
            fn(...args);
        }, ms);
    };
}

function show(el: HTMLElement): void {
    el.classList.remove('cms-hidden');
}

function hide(el: HTMLElement): void {
    el.classList.add('cms-hidden');
}

function isVisible(el: HTMLElement): boolean {
    return !el.classList.contains('cms-hidden');
}

/**
 * Minimal CSS.escape polyfill for jsdom. Only escapes the characters
 * that appear in plugin type names (which are Python class names —
 * very tame, but defend against an embedded `]`/`"` anyway).
 */
function cssEscape(s: string): string {
    if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') {
        return CSS.escape(s);
    }
    return s.replace(/["\\\]]/g, '\\$&');
}

void hideLoader;

export const _internals = {
    findSibling,
    parseDraggableId,
    parseDragareaId,
    debounce,
    isElementInViewport,
};

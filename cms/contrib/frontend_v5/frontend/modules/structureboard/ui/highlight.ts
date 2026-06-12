/*
 * Structure-board-side highlight helpers.
 *
 * Mirrors legacy `StructureBoard._showAndHighlightPlugin` and
 * `StructureBoard.highlightPluginFromUrl`. Re-uses the per-plugin
 * overlay primitives in `plugins/ui/highlight.ts` (already ported in
 * Phase 2).
 *
 *   - `highlightPluginFromUrl()` — read `window.location.hash`, look
 *     for a `cms-plugin-<id>` token, flash the matching content node.
 *     Called once at boot; the legacy `setTimeout(..., 0)` defer is
 *     done by the caller.
 *
 *   - `showAndHighlightPlugin(ctx, options)` — entry path for the
 *     shift+space keybind (see `ui/switcher.ts`). Reads the plugin id
 *     from CMS.API.Tooltip's data, calls `show()` to enter structure
 *     mode, then expands ancestor draggables and scrolls the target
 *     into view, finally flashing the structure-side overlay.
 *
 *     Defensive: tooltip is optional (the dedicated module hasn't
 *     been ported) — falls through to `Promise.resolve(false)` when
 *     it's missing.
 */

import { highlightPluginContent, highlightPluginStructure } from '../../plugins/ui/highlight';
import { getCmsConfig, getTooltip } from '../../plugins/cms-globals';
import { show, type ModeContext } from './mode';
import { getContentLoaded } from '../refresh';

const PLUGIN_ID_FROM_HASH = /cms-plugin-(\d+)/;

/**
 * If the page URL hash references a plugin (`#cms-plugin-42`), flash
 * the matching content node. Mirrors legacy
 * `StructureBoard.highlightPluginFromUrl` — gated on
 * `_loadedContent` because the highlight target nodes only exist
 * after content mode has rendered.
 */
export function highlightPluginFromUrl(): void {
    const hash = window.location.hash;
    if (!hash) return;
    const match = PLUGIN_ID_FROM_HASH.exec(hash);
    const pluginId = match?.[1];
    if (!pluginId) return;
    if (!getContentLoaded()) return;

    highlightPluginContent(pluginId, {
        seeThrough: true,
        prominent: true,
        delay: 3000,
    });
}

export interface ShowAndHighlightOptions {
    /** Forwarded to the structure-side overlay timing. */
    successTimeout?: number;
    /** True when the highlight should be transparent (shift-hover preview). */
    seeThrough?: boolean;
}

const HIGHLIGHT_DELAY_MS = 10;
const DRAGGABLE_HEIGHT = 50;

/**
 * Show the structure board, expand ancestors of the plugin under the
 * tooltip, scroll it into view and flash the structure overlay.
 *
 * Mirrors legacy `_showAndHighlightPlugin`. Bails to false in three
 * cases:
 *   - Live mode (page is read-only)
 *   - Tooltip API not present (defensive — unported)
 *   - Tooltip not currently visible
 */
export async function showAndHighlightPlugin(
    ctx: ModeContext,
    options: ShowAndHighlightOptions = {},
): Promise<boolean> {
    if (getCmsConfig().mode === 'live') return false;

    const tooltip = getTooltip();
    if (!tooltip) return false;

    // The tooltip module exposes `domElem` (a jQuery wrapper in
    // legacy, an HTMLElement in the eventual port). We duck-type
    // both with narrow accessors.
    interface TooltipDomElem {
        is?(selector: string): boolean;
        data?(key: string): unknown;
    }
    const domElem = (tooltip as unknown as { domElem?: HTMLElement | TooltipDomElem })
        .domElem;
    if (!domElem) return false;

    const isVisible =
        domElem instanceof HTMLElement
            ? domElem.offsetParent !== null
            : (domElem as TooltipDomElem).is?.(':visible') ?? false;
    if (!isVisible) return false;

    const pluginIdRaw = (() => {
        if (domElem instanceof HTMLElement) {
            return domElem.dataset.pluginId;
        }
        return (domElem as TooltipDomElem).data?.('plugin_id') as
            | number
            | string
            | undefined;
    })();
    const pluginId = pluginIdRaw === undefined ? undefined : String(pluginIdRaw);
    if (!pluginId) return false;

    await show(ctx);

    const draggable = document.querySelector<HTMLElement>(
        `.cms-draggable-${pluginId}`,
    );
    if (!draggable) return false;

    // Expand ancestor draggables that are currently collapsed. Legacy
    // walked `parents('.cms-draggable')` and triggered click on every
    // collapsable .cms-dragitem-text — we click directly here for the
    // same effect.
    let cursor: HTMLElement | null = draggable.parentElement;
    while (cursor) {
        if (cursor.classList.contains('cms-draggable')) {
            const dragitem = cursor.querySelector<HTMLElement>(
                ':scope > .cms-dragitem',
            );
            if (
                dragitem &&
                dragitem.classList.contains('cms-dragitem-collapsable') &&
                !dragitem.classList.contains('cms-dragitem-expanded')
            ) {
                const text = dragitem.querySelector<HTMLElement>(
                    ':scope > .cms-dragitem-text',
                );
                text?.click();
            }
        }
        cursor = cursor.parentElement;
    }

    // Scroll to the draggable on the next tick — the expand animations
    // change layout, so we let them settle first. Match legacy timing
    // (10ms).
    setTimeout(() => {
        const offsetParent = (draggable.offsetParent as HTMLElement) ?? null;
        const top = draggable.getBoundingClientRect().top;
        const scrollY = offsetParent
            ? offsetParent.scrollTop + top - window.innerHeight / 2 + DRAGGABLE_HEIGHT
            : window.scrollY + top - window.innerHeight / 2 + DRAGGABLE_HEIGHT;
        if (offsetParent) {
            offsetParent.scrollTop = scrollY;
        }

        const dragitem = draggable.querySelector<HTMLElement>(
            ':scope > .cms-dragitem',
        );
        if (dragitem) {
            const opts: Parameters<typeof highlightPluginStructure>[1] = {};
            if (options.successTimeout !== undefined) {
                opts.successTimeout = options.successTimeout;
            }
            if (options.seeThrough !== undefined) {
                opts.seeThrough = options.seeThrough;
            }
            highlightPluginStructure(dragitem, opts);
        }
    }, HIGHLIGHT_DELAY_MS);

    return true;
}

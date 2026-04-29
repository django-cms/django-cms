/*
 * Plugin highlighting helpers — overlay the user sees flash on a
 * plugin after a structure-mode action (move, paste) succeeds, and
 * the same overlay shown when shift-hovering in structure mode to
 * preview which content node a structure entry maps to.
 *
 * Mirrors legacy `Plugin._highlightPluginStructure`,
 * `Plugin._highlightPluginContent`, `Plugin._removeHighlightPluginContent`,
 * and `Plugin._clickToHighlightHandler`.
 *
 * Pure DOM math + classes — no jQuery. Uses
 * `getBoundingClientRect()` + `window.scrollX/Y` to compute absolute
 * page coordinates (matching legacy `$.offset()`), `getComputedStyle`
 * for margins, and CSS class swaps for fade-out (legacy used jQuery
 * `.fadeOut()` — we replace with `setTimeout` + `transition: opacity`).
 */

import { getCmsSettings, getStructureBoard } from '../cms-globals';

const DEFAULT_SUCCESS_TIMEOUT = 200;
const DEFAULT_DELAY = 1500;
const OVERLAY_POSITION_TO_WINDOW_HEIGHT_RATIO = 0.2;

/**
 * Add a transient success overlay on top of every `.cms-plugin-{id}`
 * node, then fade out after `delay`. Matches the legacy structure
 * mode "moved" affordance.
 */
export function highlightPluginContent(
    pluginId: number | string,
    {
        successTimeout = DEFAULT_SUCCESS_TIMEOUT,
        seeThrough = false,
        delay = DEFAULT_DELAY,
        prominent = false,
    }: {
        successTimeout?: number;
        seeThrough?: boolean;
        delay?: number;
        prominent?: boolean;
    } = {},
): void {
    const nodes = Array.from(
        document.querySelectorAll<HTMLElement>(`.cms-plugin-${pluginId}`),
    );
    if (nodes.length === 0) return;

    const positions: Array<{ x1: number; y1: number; x2: number; y2: number }> = [];
    for (const el of nodes) {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;
        const cs = window.getComputedStyle(el);
        const ml = parseFloat(cs.marginLeft) || 0;
        const mr = parseFloat(cs.marginRight) || 0;
        const mt = parseFloat(cs.marginTop) || 0;
        const mb = parseFloat(cs.marginBottom) || 0;
        positions.push({
            x1: rect.left + window.scrollX - ml,
            x2: rect.left + window.scrollX + rect.width + mr,
            y1: rect.top + window.scrollY - mt,
            y2: rect.top + window.scrollY + rect.height + mb,
        });
    }
    if (positions.length === 0) return;

    // Toolbar-relative offset correction (legacy: html { position:
    // relative } shifts coordinates by html margin-top).
    const html = document.documentElement;
    const htmlMargin =
        window.getComputedStyle(html).position === 'relative'
            ? parseFloat(window.getComputedStyle(html).marginTop) || 0
            : 0;

    const left = Math.min(...positions.map((p) => p.x1));
    const top = Math.min(...positions.map((p) => p.y1)) - htmlMargin;
    const width = Math.max(...positions.map((p) => p.x2)) - left;
    const height = Math.max(...positions.map((p) => p.y2)) - top - htmlMargin;

    try {
        window.scrollTo({
            top: top - window.innerHeight * OVERLAY_POSITION_TO_WINDOW_HEIGHT_RATIO,
        });
    } catch {
        /* jsdom + some embedded browsers throw on scrollTo */
    }

    const overlay = document.createElement('div');
    overlay.className = [
        'cms-plugin-overlay',
        'cms-dragitem-success',
        `cms-plugin-overlay-${pluginId}`,
        seeThrough ? 'cms-plugin-overlay-see-through' : '',
        prominent ? 'cms-plugin-overlay-prominent' : '',
    ]
        .filter(Boolean)
        .join(' ');
    overlay.dataset.successTimeout = String(successTimeout);
    Object.assign(overlay.style, {
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`,
        zIndex: '9999',
    } as Partial<CSSStyleDeclaration>);
    document.body.appendChild(overlay);

    if (successTimeout) {
        setTimeout(() => {
            const overlays = document.querySelectorAll<HTMLElement>(
                `.cms-plugin-overlay-${pluginId}`,
            );
            overlays.forEach((el) => fadeOutAndRemove(el, successTimeout));
        }, delay);
    }
}

/**
 * Remove every "still-showing" highlight overlay for a given plugin.
 * Matches the legacy guard: only the overlays with
 * `data-success-timeout="0"` are eligible — these are the
 * shift-hover previews that have no auto-fade scheduled.
 */
export function removeHighlightPluginContent(
    pluginId: number | string,
): void {
    const overlays = document.querySelectorAll<HTMLElement>(
        `.cms-plugin-overlay-${pluginId}[data-success-timeout="0"]`,
    );
    overlays.forEach((el) => el.remove());
}

/**
 * Add a `.cms-dragitem-success` overlay inside a draggable element
 * (used by the move/paste flow in structure mode). Mirrors the
 * legacy `Plugin._highlightPluginStructure`.
 */
export function highlightPluginStructure(
    el: HTMLElement,
    {
        successTimeout = DEFAULT_SUCCESS_TIMEOUT,
        delay = DEFAULT_DELAY,
        seeThrough = false,
    }: {
        successTimeout?: number;
        delay?: number;
        seeThrough?: boolean;
    } = {},
): void {
    const tpl = document.createElement('div');
    tpl.className = `cms-dragitem-success ${
        seeThrough ? 'cms-plugin-overlay-see-through' : ''
    }`.trim();

    el.classList.add('cms-draggable-success');
    el.appendChild(tpl);

    if (successTimeout) {
        setTimeout(() => {
            fadeOutAndRemove(tpl, successTimeout, () => {
                el.classList.remove('cms-draggable-success');
            });
        }, delay);
    }
}

/**
 * Click handler used by structure-mode tree entries to ask the
 * structureboard to scroll-and-highlight the matching plugin in
 * content view. No-op when not in structure mode.
 *
 * StructureBoard isn't ported yet; the optional-chain handles that.
 */
export function clickToHighlightHandler(): void {
    const settings = getCmsSettings();
    if (settings.mode !== 'structure') return;
    getStructureBoard()?._showAndHighlightPlugin?.(200, true);
}

// ────────────────────────────────────────────────────────────────────
// Internal
// ────────────────────────────────────────────────────────────────────

function fadeOutAndRemove(
    el: HTMLElement,
    duration: number,
    after?: () => void,
): void {
    el.style.transition = `opacity ${duration}ms`;
    el.style.opacity = '0';
    setTimeout(() => {
        el.remove();
        after?.();
    }, duration);
}

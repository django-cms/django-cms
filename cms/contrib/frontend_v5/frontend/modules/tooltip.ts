/*
 * Plugin hover tooltip — the small "click to edit" bubble that
 * follows the cursor over rendered plugins. Mirrors legacy
 * `cms.tooltip.js`.
 *
 * Public surface (read by structureboard's `showAndHighlightPlugin`,
 * by the plugins module's hover handlers):
 *
 *   class Tooltip {
 *       isTouch: boolean
 *       domElem: HTMLElement | null
 *       displayToggle(show, e?, name?, pluginId?)
 *       show(e, name, pluginId)
 *       hide()
 *   }
 *
 * Two presentations: desktop (mouse-following) and touch (pinned at
 * the touch point, click-to-edit). The class flips to "touch mode"
 * on the first `touchstart` and keeps a separate DOM element for
 * each (the page renders both `.cms-tooltip` and `.cms-tooltip-touch`).
 *
 * The plugin id is stored on the element via `dataset.pluginId` (the
 * native equivalent of the legacy `data('plugin_id')`). The
 * structureboard's `showAndHighlightPlugin` reads it back via the
 * same dataset access.
 */

const TOOLTIP_OFFSET = 20;
const ARROW_OFFSET = 12;

export class Tooltip {
    /** True after the first `touchstart` — switches to touch mode. */
    public isTouch = false;

    /**
     * The active tooltip element. May be null if neither
     * `.cms-tooltip` nor `.cms-tooltip-touch` exists on the page.
     */
    public domElem: HTMLElement | null;

    private mouseMoveCleanup: (() => void) | null = null;
    private touchTapCleanup: (() => void) | null = null;
    private touchStartCleanup: (() => void) | null = null;

    constructor() {
        this.domElem = pickTooltip(this.isTouch);
        this.bindTouchSwitch();
    }

    /**
     * Show or hide the tooltip. The legacy class only ever called
     * `show` with `e` set; we keep the signature loose so callers
     * passing partial args still work.
     */
    displayToggle(
        show: boolean,
        e?: MouseEvent | TouchEvent | null,
        name?: string,
        pluginId?: number | string,
    ): void {
        if (show && e) {
            this.show(e, name ?? '', pluginId);
        } else {
            this.hide();
        }
    }

    /**
     * Show the tooltip with the given plugin name and id, anchored at
     * the event's pointer position. Subsequent mouse moves
     * reposition until `hide()` is called (desktop only — touch
     * mode pins at the touch point).
     */
    show(
        e: MouseEvent | TouchEvent,
        name: string,
        pluginId?: number | string,
    ): void {
        if (!this.domElem) {
            // Re-pick — the tooltip element may have been added to
            // the page after construction (rare; defensive).
            this.domElem = pickTooltip(this.isTouch);
        }
        const tooltip = this.domElem;
        if (!tooltip) return;

        tooltip.style.visibility = 'visible';
        tooltip.classList.remove('cms-hidden');
        if (pluginId !== undefined && pluginId !== null) {
            tooltip.dataset.pluginId = String(pluginId);
        } else {
            delete tooltip.dataset.pluginId;
        }
        const span = tooltip.querySelector('span');
        if (span) span.textContent = name;

        this.position(e, tooltip);

        if (this.isTouch) return;

        // Track subsequent mouse moves on document.body to keep the
        // tooltip pinned to the cursor.
        this.detachMouseMove();
        const onMove = (mv: Event): void => {
            this.position(mv as MouseEvent, tooltip);
        };
        document.body.addEventListener('mousemove', onMove);
        this.mouseMoveCleanup = (): void =>
            document.body.removeEventListener('mousemove', onMove);
    }

    hide(): void {
        if (!this.domElem) return;
        this.domElem.style.visibility = 'hidden';
        this.domElem.classList.add('cms-hidden');
        this.detachMouseMove();
    }

    /**
     * Position `tooltip` next to the pointer position from `e`. The
     * tooltip nudges left when it would overflow the offsetParent's
     * right edge.
     */
    position(e: MouseEvent | TouchEvent, tooltip: HTMLElement): void {
        const point = readPointerCoords(e);
        if (!point) return;
        const offsetParent = (tooltip.offsetParent as HTMLElement | null) ?? document.body;
        const parentRect = offsetParent.getBoundingClientRect();

        // Use page coordinates the same way jQuery's `.offset()` does:
        // viewport rect + window scroll.
        const relX = point.pageX - (parentRect.left + window.scrollX);
        const relY = point.pageY - (parentRect.top + window.scrollY);
        const bound = parentRect.width;
        const tooltipWidth = outerWidthWithMargins(tooltip);
        const projected = relX + tooltipWidth + TOOLTIP_OFFSET;

        tooltip.style.left =
            projected >= bound
                ? `${relX - tooltipWidth - TOOLTIP_OFFSET}px`
                : `${relX + TOOLTIP_OFFSET}px`;
        tooltip.style.top = `${relY - ARROW_OFFSET}px`;
    }

    /**
     * Test/migration teardown — release every listener bound by the
     * constructor + show().
     */
    destroy(): void {
        this.detachMouseMove();
        this.touchStartCleanup?.();
        this.touchStartCleanup = null;
        this.touchTapCleanup?.();
        this.touchTapCleanup = null;
    }

    // ────────────────────────────────────────────────────────────

    private bindTouchSwitch(): void {
        const onTouchStart = (): void => {
            this.touchStartCleanup?.();
            this.touchStartCleanup = null;
            this.forceTouch();
        };
        document.body.addEventListener('touchstart', onTouchStart, {
            once: true,
        });
        this.touchStartCleanup = (): void =>
            document.body.removeEventListener('touchstart', onTouchStart);
    }

    private forceTouch(): void {
        this.isTouch = true;
        this.domElem = pickTooltip(this.isTouch);
        if (!this.domElem) return;

        // On touch devices, tapping the tooltip dispatches a
        // `dblclick` on the matching plugin so the standard edit
        // flow fires.
        const onTap = (): void => {
            const pid = this.domElem?.dataset.pluginId;
            if (!pid) return;
            const plugin = document.querySelector(`.cms-plugin-${pid}`);
            if (plugin) {
                plugin.dispatchEvent(
                    new MouseEvent('dblclick', { bubbles: true }),
                );
                return;
            }
            // Generic plugins are emitted as `cms-plugin cms-plugin-cms-X-<id>`.
            const generic = document.querySelector(
                `.cms-plugin[class*="cms-plugin-cms-"][class*="-${pid}"]`,
            );
            generic?.dispatchEvent(
                new MouseEvent('dblclick', { bubbles: true }),
            );
        };
        this.domElem.addEventListener('touchstart', onTap);
        this.touchTapCleanup = (): void =>
            this.domElem?.removeEventListener('touchstart', onTap);
    }

    private detachMouseMove(): void {
        this.mouseMoveCleanup?.();
        this.mouseMoveCleanup = null;
    }
}

/**
 * Pick the active tooltip element + hide all candidates. Touch mode
 * picks `.cms-tooltip-touch`; desktop mode picks `.cms-tooltip`.
 */
function pickTooltip(isTouch: boolean): HTMLElement | null {
    const candidates = document.querySelectorAll<HTMLElement>(
        '.cms-tooltip, .cms-tooltip-touch',
    );
    for (const el of Array.from(candidates)) {
        el.style.visibility = 'hidden';
        el.classList.add('cms-hidden');
    }
    const selector = isTouch ? '.cms-tooltip-touch' : '.cms-tooltip';
    return document.querySelector<HTMLElement>(selector);
}

/**
 * Pull pageX / pageY from a Mouse or Touch event. Touch events use
 * the first changed touch.
 */
function readPointerCoords(
    e: MouseEvent | TouchEvent,
): { pageX: number; pageY: number } | null {
    if ('pageX' in e && typeof e.pageX === 'number') {
        return { pageX: e.pageX, pageY: e.pageY };
    }
    const touchEvent = e as TouchEvent;
    const touch =
        touchEvent.changedTouches?.[0] ?? touchEvent.touches?.[0] ?? null;
    if (!touch) return null;
    return { pageX: touch.pageX, pageY: touch.pageY };
}

function outerWidthWithMargins(el: HTMLElement): number {
    const rect = el.getBoundingClientRect();
    const cs = window.getComputedStyle(el);
    const ml = parseFloat(cs.marginLeft) || 0;
    const mr = parseFloat(cs.marginRight) || 0;
    return rect.width + ml + mr;
}

export default Tooltip;

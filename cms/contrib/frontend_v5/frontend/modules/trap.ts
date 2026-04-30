/*
 * Focus trap — keep Tab navigation within a container element. Port
 * of the legacy `trap.js` (which itself derives from
 * jquery.trap.js). Used by the modal so the user can't tab "out" of
 * an open modal into the page underneath.
 *
 * Public surface:
 *   trap(element)       — activate the trap on `element`
 *   untrap(element)     — release it
 *   isTrapping(element) — predicate
 */

const TRAP_FLAG = '__cms_trap_active';

function getFocusableElementsInContainer(
    container: HTMLElement,
): HTMLElement[] {
    const elements = Array.from(
        container.querySelectorAll<HTMLElement>(
            'a[href], link[href], [draggable="true"], [contenteditable="true"], input:not([disabled]), button:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex], summary',
        ),
    ).filter((el) => el.offsetParent !== null);

    // Stable sort: positive-tabindex elements after natural order.
    const normal = elements
        .filter((el) => !el.tabIndex || el.tabIndex === 0)
        .map((v, i) => ({ v, t: 0, i }));
    const special = elements
        .filter((el) => el.tabIndex > 0)
        .map((v, i) => ({ v, t: v.tabIndex, i: i + normal.length }));
    return [...normal, ...special]
        .sort((a, b) => a.t - b.t || a.i - b.i)
        .map((o) => o.v);
}

function processTab(
    container: HTMLElement,
    _elt: Element | null,
    goReverse: boolean,
): void {
    const focussable = getFocusableElementsInContainer(container);
    setTimeout(() => {
        const newFocus = container.ownerDocument.activeElement;
        if (
            newFocus === null ||
            newFocus === container.ownerDocument.body ||
            !container.contains(newFocus)
        ) {
            const target = goReverse
                ? focussable[focussable.length - 1]
                : focussable[0];
            try {
                target?.focus();
            } catch {
                /* element became un-focusable between scan and focus call */
            }
        }
    }, 0);
}

function onKeyPress(e: KeyboardEvent): void {
    if (e.key !== 'Tab') return;
    const container = e.currentTarget as HTMLElement;
    processTab(
        container,
        container.ownerDocument.activeElement,
        Boolean(e.shiftKey),
    );
}

export function trap(element: HTMLElement | null | undefined): void {
    if (!element) return;
    element.addEventListener('keydown', onKeyPress);
    (element as unknown as Record<string, unknown>)[TRAP_FLAG] = true;
}

export function untrap(element: HTMLElement | null | undefined): void {
    if (!element) return;
    element.removeEventListener('keydown', onKeyPress);
    delete (element as unknown as Record<string, unknown>)[TRAP_FLAG];
}

export function isTrapping(element: HTMLElement | null | undefined): boolean {
    if (!element) return false;
    return Boolean(
        (element as unknown as Record<string, unknown>)[TRAP_FLAG],
    );
}

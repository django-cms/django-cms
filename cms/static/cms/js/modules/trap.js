

// ES6 Focus Trap module without jQuery, basoed on jquery.trap.js
// Copyright (c) 2011, 2012 Julien Wajsberg, 2025 Fabian Braun

const DATA_ISTRAPPING_KEY = '__trap_isTrapping';

/**
 * Returns all visible, focusable elements inside a container.
 * Focusable elements include links, buttons, inputs, textareas, selects, and elements with tabindex.
 * Elements must be visible (offsetParent !== null).
 * Sorted by tabIndex (positive first, then normal order).
 *
 * @param {HTMLElement} container - The container to search within.
 * @returns {HTMLElement[]} Array of focusable elements.
 */
function getFocusableElementsInContainer(container) {
    const elements = Array.from(container.querySelectorAll(
        'a[href], link[href], [draggable="true"], [contenteditable="true"], input:not([disabled]), ' +
        'button:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex], summary'
    )).filter(el => el.offsetParent !== null);

    // Sort by tabIndex: positive first, then normal
    const normal = elements.filter(el => !el.tabIndex || el.tabIndex === 0).map((v, i) => ({ v, t: 0, i }));
    const special = elements.filter(el => el.tabIndex > 0).map((v, i) => ({ v, t: v.tabIndex, i: i + normal.length }));
    const all = [...normal, ...special].sort((a, b) => (a.t - b.t) || (a.i - b.i));

    return all.map(obj => obj.v);
}

/**
 * Handles Tab and Shift+Tab key events to keep focus inside the container.
 * Moves focus to the next or previous focusable element.
 *
 * @param {HTMLElement} container - The container element.
 * @param {HTMLElement} elt - The currently focused element.
 * @param {boolean} goReverse - If true, move backwards (Shift+Tab).
 * @returns {boolean} True if tab event was processed, false otherwise.
 */
function processTab(container, elt, goReverse) {
    const focussable = getFocusableElementsInContainer(container);

    setTimeout(() => {
        const newFocus = container.ownerDocument.activeElement;

        if (newFocus === null || newFocus === container.ownerDocument.body || !container.contains(newFocus)) {
            if (goReverse) {
                try {
                    focussable[focussable.length - 1].focus();
                } catch {}
            } else {
                try {
                    focussable[0].focus();
                } catch {}
            }
        }
    }, 0);
}

/**
 * Keydown event handler for trapping focus.
 * Only processes Tab key events.
 *
 * @param {KeyboardEvent} e
 * @private
 */
function onKeyPress(e) {
    if (e.key === 'Tab') {
        const container = e.currentTarget;
        const goReverse = !!e.shiftKey;

        processTab(container, container.ownerDocument.activeElement, goReverse);
    }
}

/**
 * Enables focus trap for a given element. Focus will cycle within the element on Tab/Shift+Tab.
 *
 * @param {HTMLElement} element - The element to trap focus inside.
 */
export function trap(element) {
    if (!element) {
        return;
    }
    element.addEventListener('keydown', onKeyPress);
    element[DATA_ISTRAPPING_KEY] = true;
}

/**
 * Disables focus trap for a given element. Removes the keydown event handler.
 *
 * @param {HTMLElement} element - The element to remove focus trap from.
 */
export function untrap(element) {
    if (!element) {
        return;
    }
    element.removeEventListener('keydown', onKeyPress);
    delete element[DATA_ISTRAPPING_KEY];
}

/**
 * Checks if focus trap is currently enabled for the given element.
 *
 * @param {HTMLElement} element - The element to check.
 * @returns {boolean} True if focus trap is active, false otherwise.
 */
export function isTrapping(element) {
    return !!(element && element[DATA_ISTRAPPING_KEY]);
}


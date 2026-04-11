/*
 * Vanilla DOM helpers — replacements for the most common jQuery patterns
 * used throughout the legacy stack. Intentionally tiny: each helper does
 * one thing the standard DOM API makes mildly awkward.
 *
 * If you find yourself reaching for jQuery, add a helper here instead.
 */

/**
 * Type-narrowed querySelector. Returns the first matching element under
 * `root` (default: document), or null. Generic param lets callers state
 * the expected element type without casting at the call site.
 */
export function $<E extends Element = HTMLElement>(
    selector: string,
    root: ParentNode = document,
): E | null {
    return root.querySelector<E>(selector);
}

/**
 * Type-narrowed querySelectorAll → real Array (not a NodeList), so the
 * full array prototype is available without spread/Array.from at every
 * call site.
 */
export function $$<E extends Element = HTMLElement>(
    selector: string,
    root: ParentNode = document,
): E[] {
    return Array.from(root.querySelectorAll<E>(selector));
}

/** Variant of `closest` that returns null if `el` itself is null. */
export function closest<E extends Element = HTMLElement>(
    el: Element | null,
    selector: string,
): E | null {
    return el ? (el.closest<E>(selector)) : null;
}

/** Add one or more class names. Empty/whitespace tokens are ignored. */
export function addClass(el: Element, ...names: string[]): void {
    for (const name of names) {
        if (name) el.classList.add(name);
    }
}

/** Remove one or more class names. */
export function removeClass(el: Element, ...names: string[]): void {
    for (const name of names) {
        if (name) el.classList.remove(name);
    }
}

/**
 * Toggle a class. If `force` is provided, set/unset accordingly (matches
 * the native classList.toggle signature). Returns the new state.
 */
export function toggleClass(el: Element, name: string, force?: boolean): boolean {
    return el.classList.toggle(name, force);
}

/**
 * Parse an HTML string into a single element. Useful for the "build a
 * detached DOM subtree from a template literal" pattern. Throws if the
 * input doesn't produce exactly one root element — that asymmetry catches
 * common mistakes (forgotten wrapper, accidental whitespace creating text
 * nodes) at the call site instead of producing surprising fragments.
 */
export function html<E extends Element = HTMLElement>(markup: string): E {
    const template = document.createElement('template');
    template.innerHTML = markup.trim();
    const content = template.content;
    if (content.childElementCount !== 1) {
        throw new Error(
            `dom.html: expected exactly 1 root element, got ${content.childElementCount}`,
        );
    }
    return content.firstElementChild as E;
}

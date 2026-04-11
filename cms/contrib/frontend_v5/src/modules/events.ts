/*
 * Event delegation — replacement for jQuery's
 *   $(root).on(eventType, selector, handler)
 *
 * The native equivalent (`addEventListener` + manual `closest()` matching
 * inside the handler) is verbose and easy to get wrong, so this helper
 * encapsulates it. Returns an unsubscribe function so callers don't have
 * to remember the listener reference for `removeEventListener`.
 *
 * Notes:
 *   - The matched element (the closest ancestor of `event.target` that
 *     matches `selector`, bounded by `root`) is passed as the second
 *     argument to the handler. The first argument is the original event,
 *     unchanged. We do NOT mutate `event.currentTarget` because that
 *     property is not safely writable in all environments.
 *   - For events that don't bubble (`focus`, `blur`), pass
 *     `{ capture: true }`. This works because capture-phase listeners
 *     receive every descendant event regardless of bubbling.
 */

export type DelegatedHandler<E extends Event = Event, T extends Element = HTMLElement> = (
    event: E,
    matched: T,
) => void;

export interface DelegateOptions {
    /**
     * Use the capture phase. Required for events that don't bubble
     * (`focus`, `blur`, `mouseenter`, `mouseleave`).
     */
    capture?: boolean;
}

export function delegate<E extends Event = Event, T extends Element = HTMLElement>(
    root: Element | Document,
    type: string,
    selector: string,
    handler: DelegatedHandler<E, T>,
    options: DelegateOptions = {},
): () => void {
    const listener = (event: Event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;

        // Walk up from the event target until we either find a match or
        // pass `root`. Bounding by `root` ensures we don't accidentally
        // match elements outside the delegated region — important when
        // multiple delegate() calls coexist on different roots.
        const matched = target.closest(selector);
        if (!matched) return;
        if (root instanceof Element && !root.contains(matched)) return;
        if (root instanceof Document && !root.documentElement.contains(matched)) return;

        handler(event as E, matched as T);
    };

    const opts: AddEventListenerOptions = { capture: !!options.capture };
    root.addEventListener(type, listener, opts);
    return () => root.removeEventListener(type, listener, opts);
}

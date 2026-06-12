/*
 * Class-name → numeric id parsers.
 *
 * Legacy `cms.structureboard.js::getId` reads `el.attr('class').split(' ')[1]`
 * (the second class) and assumes it's the `cms-{type}-<id>` token. That's
 * fragile — relies on server-rendered class order. Our port walks the
 * full classList and picks the first match, which is more robust and
 * preserves legacy behaviour for every observed case.
 *
 * Pure functions — no DOM mutation, no jQuery. Single source of truth
 * for class-name parsing across plugins + structureboard.
 */

const PATTERNS = {
    plugin: /^cms-plugin-(\d+)$/,
    draggable: /^cms-draggable-(\d+)$/,
    placeholder: /^cms-placeholder-(\d+)$/,
    dragbar: /^cms-dragbar-(\d+)$/,
    dragarea: /^cms-dragarea-(\d+)$/,
} as const;

type IdKind = keyof typeof PATTERNS;

/**
 * Read the numeric id from an element's classList by matching one of
 * the known patterns. Returns `undefined` when no pattern matches.
 *
 * Order: tries plugin → draggable → placeholder → dragbar → dragarea.
 * Most elements only carry one of these so the order rarely matters,
 * but legacy behaviour favours plugin/draggable first.
 */
export function getId(el: Element | null | undefined): number | undefined {
    if (!el || !el.classList) return undefined;
    for (const cls of Array.from(el.classList)) {
        for (const pattern of Object.values(PATTERNS)) {
            const match = pattern.exec(cls);
            if (match && match[1]) return Number(match[1]);
        }
    }
    return undefined;
}

/** Map `getId` over an iterable of elements; drops the misses. */
export function getIds(els: Iterable<Element>): number[] {
    const ids: number[] = [];
    for (const el of els) {
        const id = getId(el);
        if (id !== undefined) ids.push(id);
    }
    return ids;
}

/**
 * Parse a single id-kind from an element. Used when the caller knows
 * the expected wrapper type (e.g. "I'm walking up to a `.cms-dragarea`,
 * give me its id"). Returns undefined when the element doesn't carry
 * a class matching that kind.
 */
function parseKind(el: Element | null, kind: IdKind): number | undefined {
    if (!el?.classList) return undefined;
    const pattern = PATTERNS[kind];
    for (const cls of Array.from(el.classList)) {
        const match = pattern.exec(cls);
        if (match && match[1]) return Number(match[1]);
    }
    return undefined;
}

/** `parseKind(el, 'draggable')` shortcut. */
export const parseDraggableId = (el: Element | null): number | undefined =>
    parseKind(el, 'draggable');

/** `parseKind(el, 'dragarea')` shortcut. */
export const parseDragareaId = (el: Element | null): number | undefined =>
    parseKind(el, 'dragarea');

/** `parseKind(el, 'placeholder')` shortcut. */
export const parsePlaceholderId = (el: Element | null): number | undefined =>
    parseKind(el, 'placeholder');

/** `parseKind(el, 'dragbar')` shortcut. */
export const parseDragbarId = (el: Element | null): number | undefined =>
    parseKind(el, 'dragbar');

/** `parseKind(el, 'plugin')` shortcut. */
export const parsePluginId = (el: Element | null): number | undefined =>
    parseKind(el, 'plugin');

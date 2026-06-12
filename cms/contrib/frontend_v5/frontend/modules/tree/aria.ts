/*
 * ARIA helpers for tree widgets per the WAI-ARIA tree pattern.
 * https://www.w3.org/WAI/ARIA/apg/patterns/treeview/
 *
 * This is the SINGLE SOURCE OF TRUTH for setting tree-related aria-*
 * attributes. No other module should set them directly — that way, if a
 * future spec change requires (say) renaming `aria-level` to something
 * else, we change one file and the whole rewrite stays compliant.
 *
 * Reference for the attributes used here:
 *   - role="tree"        on the container
 *   - role="treeitem"    on each node element
 *   - role="group"       on each container holding a treeitem's children
 *   - aria-expanded      on parent treeitems (true | false)
 *   - aria-selected      on the currently-selected treeitem
 *   - aria-level         1-based depth (root nodes are level 1, NOT 0)
 *   - aria-setsize       number of siblings (including self) at this level
 *   - aria-posinset      1-based position among siblings
 *
 * Leaf nodes do NOT get aria-expanded — its absence is what tells assistive
 * tech a node has no children. Setting aria-expanded="false" on a leaf is
 * a common bug; setExpanded() with `expandable=false` removes the attribute
 * to make this the obviously-correct path.
 */

export function setTreeRole(container: Element): void {
    container.setAttribute('role', 'tree');
}

export function setGroupRole(container: Element): void {
    container.setAttribute('role', 'group');
}

export function setTreeItemRole(item: Element): void {
    item.setAttribute('role', 'treeitem');
}

/**
 * Set or clear `aria-expanded`. If the item is not expandable (a leaf),
 * the attribute is removed entirely — assistive tech relies on its
 * absence to know there are no children.
 */
export function setExpanded(item: Element, expandable: boolean, expanded: boolean): void {
    if (!expandable) {
        item.removeAttribute('aria-expanded');
        return;
    }
    item.setAttribute('aria-expanded', expanded ? 'true' : 'false');
}

export function setSelected(item: Element, selected: boolean): void {
    item.setAttribute('aria-selected', selected ? 'true' : 'false');
}

/**
 * Tree depth, 1-based per the WAI-ARIA spec. Roots are level 1.
 * Callers using a 0-based depth from `TreeState.depth()` should add 1.
 */
export function setLevel(item: Element, level: number): void {
    if (level < 1) {
        throw new Error(`aria.setLevel: level must be >= 1, got ${level}`);
    }
    item.setAttribute('aria-level', String(level));
}

/**
 * Sibling count at this level, including the item itself. Use the parent's
 * children count, NOT the depth. Required by the spec for correct screen
 * reader announcements ("item 3 of 7").
 */
export function setSetSize(item: Element, size: number): void {
    if (size < 1) {
        throw new Error(`aria.setSetSize: size must be >= 1, got ${size}`);
    }
    item.setAttribute('aria-setsize', String(size));
}

/** 1-based position among siblings. First sibling is position 1. */
export function setPosInSet(item: Element, position: number): void {
    if (position < 1) {
        throw new Error(`aria.setPosInSet: position must be >= 1, got ${position}`);
    }
    item.setAttribute('aria-posinset', String(position));
}

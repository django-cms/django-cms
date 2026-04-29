/*
 * DiffDOM — port of `cms/static/cms/js/modules/dom-diff.js`.
 *
 * Lightweight DOM-tree differ used by structureboard's content
 * refresh. Two-tier matching reuses unchanged nodes (skipping script
 * re-execution) while still letting changed elements update in place.
 *
 *   1. Exact match (full key) → reuse the existing node as-is.
 *   2. Shallow match (tag + id) → keep the outer element, recurse.
 *      `<script>` is excluded — a changed script must be re-cloned
 *      so the browser re-executes it.
 *   3. No match → clone from source.
 *
 * `nodeToObj` is a serialiser used by the cross-tab `storage` payload
 * (legacy uses it before stringifying via `JSON.stringify`).
 */

interface NodeObjElement {
    nodeName: string;
    attributes: Record<string, string>;
    childNodes: NodeObj[];
}

interface NodeObjText {
    nodeName: '#text';
    data: string;
}

interface NodeObjComment {
    nodeName: '#comment';
    data: string;
}

export type NodeObj = NodeObjElement | NodeObjText | NodeObjComment;

/**
 * Serialise a DOM node to a plain JSON-friendly object. Unsupported
 * node types (cdata, doctype, etc.) return null and are dropped.
 */
export function nodeToObj(node: Node | null | undefined): NodeObj | null {
    if (!node || node.nodeType === undefined) return null;

    if (node.nodeType === Node.TEXT_NODE) {
        return { nodeName: '#text', data: (node as Text).data };
    }

    if (node.nodeType === Node.COMMENT_NODE) {
        return { nodeName: '#comment', data: (node as Comment).data };
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
        const el = node as Element;
        const attrs: Record<string, string> = {};
        for (const attr of Array.from(el.attributes)) {
            attrs[attr.name] = attr.value;
        }
        const childNodes: NodeObj[] = [];
        for (const child of Array.from(el.childNodes)) {
            const childObj = nodeToObj(child);
            if (childObj) childNodes.push(childObj);
        }
        return { nodeName: el.nodeName, attributes: attrs, childNodes };
    }

    return null;
}

export interface DiffResult {
    oldNode: Node;
    newNode: Node | null;
}

/**
 * Lightweight DOM differ. Constructed once and reused across diff
 * operations — owns a `DOMParser` instance for HTML-string inputs.
 */
export class DiffDOM {
    private readonly parser = new DOMParser();

    /**
     * Compute a diff against `newContent`. The result is an opaque
     * pair `{ oldNode, newNode }` consumed by `apply()`. We don't
     * compute a structural diff — `apply()` walks both trees together.
     */
    diff(oldNode: Node, newContent: string | NodeObj | Node): DiffResult {
        let newNode: Node | null;

        if (typeof newContent === 'string') {
            const doc = this.parser.parseFromString(newContent, 'text/html');
            newNode = doc.body.firstChild ?? doc.head.firstChild;
        } else if (
            typeof newContent === 'object' &&
            newContent !== null &&
            'nodeName' in newContent &&
            !(newContent instanceof Node)
        ) {
            newNode = this.objToNode(newContent as NodeObj);
        } else {
            newNode = newContent as Node;
        }

        return { oldNode, newNode };
    }

    /**
     * Apply a diff to `target`, syncing its children with the new
     * tree. Text and comment nodes are handled directly; element
     * children go through the two-tier matching algorithm.
     */
    apply(target: Node, diff: DiffResult): void {
        const { newNode } = diff;
        if (!newNode) return;

        if (
            newNode.nodeType === Node.TEXT_NODE ||
            newNode.nodeType === Node.COMMENT_NODE
        ) {
            (target as Text | Comment).textContent = newNode.textContent;
            return;
        }

        if (
            target instanceof Element &&
            newNode instanceof Element &&
            target.innerHTML === newNode.innerHTML
        ) {
            return;
        }

        this.syncChildren(target, newNode);
    }

    private syncChildren(target: Node, source: Node): void {
        const newChildren = source.childNodes
            ? Array.from(source.childNodes)
            : [];
        const existingChildren = Array.from(target.childNodes);

        const existingByExactKey = new Map<string, number[]>();
        existingChildren.forEach((child, i) => {
            const key = this.nodeKey(child);
            const list = existingByExactKey.get(key);
            if (list) list.push(i);
            else existingByExactKey.set(key, [i]);
        });

        const existingByShallowKey = new Map<string, number[]>();
        existingChildren.forEach((child, i) => {
            if (child.nodeType !== Node.ELEMENT_NODE) return;
            const key = this.shallowKey(child as Element);
            const list = existingByShallowKey.get(key);
            if (list) list.push(i);
            else existingByShallowKey.set(key, [i]);
        });

        const usedIndices = new Set<number>();

        const resolved: Node[] = newChildren.map((newChild) => {
            // Tier 1: exact match.
            const exactKey = this.nodeKey(newChild);
            const exactCandidates = existingByExactKey.get(exactKey);
            if (exactCandidates) {
                for (let j = 0; j < exactCandidates.length; j++) {
                    const idx = exactCandidates[j]!;
                    if (!usedIndices.has(idx)) {
                        usedIndices.add(idx);
                        exactCandidates.splice(j, 1);
                        return existingChildren[idx]!;
                    }
                }
            }

            // Tier 2: shallow match (element nodes, but not <script>).
            if (
                newChild.nodeType === Node.ELEMENT_NODE &&
                (newChild as Element).nodeName !== 'SCRIPT'
            ) {
                const shallowKey = this.shallowKey(newChild as Element);
                const shallowCandidates = existingByShallowKey.get(shallowKey);
                if (shallowCandidates) {
                    for (let j = 0; j < shallowCandidates.length; j++) {
                        const idx = shallowCandidates[j]!;
                        if (!usedIndices.has(idx)) {
                            usedIndices.add(idx);
                            shallowCandidates.splice(j, 1);
                            const existingEl = existingChildren[idx] as Element;
                            this.syncAttributes(existingEl, newChild as Element);
                            this.syncChildren(existingEl, newChild);
                            return existingEl;
                        }
                    }
                }
            }

            // Tier 3: clone from source.
            return newChild.cloneNode(true);
        });

        // Positional patching: skip nodes already in the right spot.
        let cursor: Node | null = target.firstChild;
        for (const child of resolved) {
            if (child === cursor) {
                cursor = cursor.nextSibling;
            } else {
                target.insertBefore(child, cursor);
            }
        }

        // Drop leftover existing nodes — but preserve external scripts
        // (with `src`) since their effects can be referenced by other
        // code even after their tag is gone.
        while (cursor) {
            const next: Node | null = cursor.nextSibling;
            const isExternalScript =
                cursor.nodeName === 'SCRIPT' &&
                (cursor as Element).getAttribute('src') !== null;
            if (!isExternalScript) {
                target.removeChild(cursor);
            }
            cursor = next;
        }
    }

    private syncAttributes(target: Element, source: Element): void {
        const newAttrs = new Set<string>();
        for (const attr of Array.from(source.attributes)) {
            newAttrs.add(attr.name);
            if (target.getAttribute(attr.name) !== attr.value) {
                target.setAttribute(attr.name, attr.value);
            }
        }
        const toRemove: string[] = [];
        for (const attr of Array.from(target.attributes)) {
            if (!newAttrs.has(attr.name)) toRemove.push(attr.name);
        }
        for (const name of toRemove) target.removeAttribute(name);
    }

    private objToNode(obj: NodeObj | null): Node | null {
        if (!obj) return null;
        if ('data' in obj) {
            if (obj.nodeName === '#text') {
                return document.createTextNode(obj.data ?? '');
            }
            if (obj.nodeName === '#comment') {
                return document.createComment(obj.data ?? '');
            }
            return null;
        }
        return this.objToElement(obj);
    }

    private objToElement(obj: NodeObjElement): Element {
        const node = document.createElement(obj.nodeName);
        if (obj.attributes) {
            for (const [name, value] of Object.entries(obj.attributes)) {
                node.setAttribute(name, value);
            }
        }
        if (obj.childNodes) {
            for (const child of obj.childNodes) {
                const childNode = this.objToNode(child);
                if (childNode) node.appendChild(childNode);
            }
        }
        return node;
    }

    /**
     * Build a fast equality key. For leaf elements (no element
     * children) include attributes + textContent. For nested elements
     * fall back to outerHTML.
     */
    private nodeKey(node: Node): string {
        if (node.nodeType === Node.TEXT_NODE) {
            return '#t:' + (node as Text).data;
        }
        if (node.nodeType === Node.ELEMENT_NODE) {
            const el = node as Element;
            if (!el.firstElementChild) {
                let key = el.nodeName;
                for (const attr of Array.from(el.attributes)) {
                    key += '\0' + attr.name + '=' + attr.value;
                }
                if (el.firstChild) key += '\0' + el.textContent;
                return key;
            }
            return el.outerHTML;
        }
        return '#' + node.nodeType + ':' + ((node as CharacterData).data ?? '');
    }

    /** Shallow key: tag + id (when present). Doesn't include children. */
    private shallowKey(node: Element): string {
        const id = node.getAttribute('id');
        return id ? node.nodeName + '#' + id : node.nodeName;
    }
}

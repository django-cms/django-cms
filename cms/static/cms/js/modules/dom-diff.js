/* eslint-env browser */
/* global DOMParser */
/*
 * Copyright https://github.com/django-cms/django-cms
 * Simple DOM diffing replacement using native browser APIs
 * Replaces diff-dom
 */

/**
 * Converts a DOM node to a plain object representation
 * @param {Node} node - DOM node to convert
 * @returns {Object} Object representation of the node
 */
export function nodeToObj(node) {
    if (!node || !node.nodeType) {
        return null;
    }

    if (node.nodeType === Node.TEXT_NODE) {
        return {
            nodeName: '#text',
            data: node.data
        };
    }

    if (node.nodeType === Node.COMMENT_NODE) {
        return {
            nodeName: '#comment',
            data: node.data
        };
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
        const obj = {
            nodeName: node.nodeName,
            attributes: {},
            childNodes: []
        };

        // Copy attributes
        for (const attr of node.attributes) {
            obj.attributes[attr.name] = attr.value;
        }

        // Copy child nodes (skip unsupported node types)
        for (const child of node.childNodes) {
            const childObj = nodeToObj(child);

            if (childObj) {
                obj.childNodes.push(childObj);
            }
        }

        return obj;
    }

    return null;
}

/**
 * Simple DOM differ that uses native browser APIs
 * This is a lightweight replacement for DiffDOM
 */
export class DiffDOM {
    constructor() {
        // DOMParser is supported by all browsers in our Browserslist; we can rely on it.
        this.parser = new DOMParser();
    }

    /**
     * Calculate diff between old node and new HTML/object
     * Note: This is a simplified version that doesn't return a diff object
     * Instead, we'll apply changes directly in the apply() method
     *
     * @param {Node} oldNode - Current DOM node
     * @param {string|Object} newContent - New HTML string or node object
     * @returns {Object} Diff information
     */
    diff(oldNode, newContent) {
        let newNode;

        if (typeof newContent === 'string') {
            // Parse HTML string via DOMParser; unwrap the outer container (div) and use its children
            const doc = this.parser.parseFromString(newContent, 'text/html');

            newNode = doc.body.firstChild || doc.head.firstChild;
        } else if (typeof newContent === 'object' && newContent.nodeName) {
            // Convert object to DOM node
            newNode = this._objToNode(newContent);
        } else {
            newNode = newContent;
        }

        return {
            oldNode,
            newNode
        };
    }

    /**
     * Apply diff to update the DOM
     * @param {Node} target - Target node to update
     * @param {Object} diff - Diff object from diff()
     */
    apply(target, diff) {
        const { newNode } = diff;

        if (!newNode) {
            return;
        }

        this._syncChildren(target, newNode);
    }

    /**
     * Recursively sync children of an existing element with those of a new element.
     * Uses two-tier matching:
     *   1. Exact match (outerHTML) — reuse the existing DOM node as-is.
     *   2. Shallow match (same tag + attributes) — keep the outer element, recurse into children.
     *   3. No match — clone the new node.
     * This ensures unchanged nested scripts are never re-executed, even when an
     * ancestor element has changed.
     * @param {Node} target - Existing DOM element whose children will be updated
     * @param {Node} source - New DOM element whose children are the desired state
     * @private
     */
    _syncChildren(target, source) {
        const newChildren = source.childNodes ? Array.from(source.childNodes) : [];
        const existingChildren = Array.from(target.childNodes);

        // Build exact-key index (outerHTML for elements, content for text/comments)
        const existingByExactKey = new Map();

        existingChildren.forEach((child, i) => {
            const key = this._nodeKey(child);

            if (!existingByExactKey.has(key)) {
                existingByExactKey.set(key, []);
            }
            existingByExactKey.get(key).push(i);
        });

        // Build shallow-key index (tag + attributes only, for element nodes)
        const existingByShallowKey = new Map();

        existingChildren.forEach((child, i) => {
            if (child.nodeType === Node.ELEMENT_NODE) {
                const key = this._shallowKey(child);

                if (!existingByShallowKey.has(key)) {
                    existingByShallowKey.set(key, []);
                }
                existingByShallowKey.get(key).push(i);
            }
        });

        const usedIndices = new Set();

        const resolvedChildren = newChildren.map(newChild => {
            // Tier 1: exact match — reuse as-is
            const exactKey = this._nodeKey(newChild);
            const exactCandidates = existingByExactKey.get(exactKey);

            if (exactCandidates) {
                for (let j = 0; j < exactCandidates.length; j++) {
                    const idx = exactCandidates[j];

                    if (!usedIndices.has(idx)) {
                        usedIndices.add(idx);
                        exactCandidates.splice(j, 1);
                        return existingChildren[idx];
                    }
                }
            }

            // Tier 2: shallow match (element nodes only, except <script>) — sync attributes & recurse.
            // Scripts are excluded: a changed script must be cloned so the browser re-executes it.
            if (newChild.nodeType === Node.ELEMENT_NODE && newChild.nodeName !== 'SCRIPT') {
                const shallowKey = this._shallowKey(newChild);
                const shallowCandidates = existingByShallowKey.get(shallowKey);

                if (shallowCandidates) {
                    for (let j = 0; j < shallowCandidates.length; j++) {
                        const idx = shallowCandidates[j];

                        if (!usedIndices.has(idx)) {
                            usedIndices.add(idx);
                            shallowCandidates.splice(j, 1);
                            const existingEl = existingChildren[idx];

                            this._syncAttributes(existingEl, newChild);
                            this._syncChildren(existingEl, newChild);
                            return existingEl;
                        }
                    }
                }
            }

            // Tier 3: no match — clone
            return newChild.cloneNode(true);
        });

        // Remove existing children that have no match in the new content
        existingChildren.forEach((child, i) => {
            if (!usedIndices.has(i)) {
                target.removeChild(child);
            }
        });

        // Append in correct order (appendChild moves existing nodes without re-execution)
        resolvedChildren.forEach(child => {
            target.appendChild(child);
        });
    }

    /**
     * Sync attributes from source element to target element.
     * Adds/updates attributes present on source, removes those absent from source.
     * @param {Element} target
     * @param {Element} source
     * @private
     */
    _syncAttributes(target, source) {
        const newAttrs = new Set();

        for (const attr of source.attributes) {
            newAttrs.add(attr.name);
            if (target.getAttribute(attr.name) !== attr.value) {
                target.setAttribute(attr.name, attr.value);
            }
        }

        // Remove attributes not present in source
        const toRemove = [];

        for (const attr of target.attributes) {
            if (!newAttrs.has(attr.name)) {
                toRemove.push(attr.name);
            }
        }
        toRemove.forEach(name => target.removeAttribute(name));
    }

    /**
     * Convert object representation back to DOM node
     * @param {Object} obj - Object representation
     * @returns {Node} DOM node
     * @private
     */
    _objToNode(obj) {
        if (!obj) {
            return null;
        }

        if (obj.nodeName === '#text') {
            return document.createTextNode(obj.data || '');
        }

        if (obj.nodeName === '#comment') {
            return document.createComment(obj.data || '');
        }

        return this._objToElement(obj);
    }

    /**
     * Convert an element object representation to a DOM element.
     * @param {Object} obj - Object with nodeName, attributes, childNodes
     * @returns {Element}
     * @private
     */
    _objToElement(obj) {
        const node = document.createElement(obj.nodeName);

        if (obj.attributes) {
            for (const [name, value] of Object.entries(obj.attributes)) {
                node.setAttribute(name, value);
            }
        }

        if (obj.childNodes) {
            for (const child of obj.childNodes) {
                const childNode = this._objToNode(child);

                if (childNode) {
                    node.appendChild(childNode);
                }
            }
        }

        return node;
    }

    /**
     * Generate a string key for a DOM node for fast equality lookup.
     * Includes the full subtree (outerHTML) for element nodes.
     * @param {Node} node
     * @returns {string}
     * @private
     */
    _nodeKey(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return '#text:' + node.data;
        }
        if (node.nodeType === Node.ELEMENT_NODE) {
            return node.outerHTML;
        }
        return '#' + node.nodeType + ':' + (node.data || '');
    }

    /**
     * Generate a shallow key for an element node: tag name (+ id if present).
     * Does NOT include children or other attributes, so two elements with the
     * same tag (and id) but different content/attributes produce the same key.
     * The id is included to prevent unrelated elements of the same tag from
     * being incorrectly paired.
     * @param {Node} node - Must be an ELEMENT_NODE
     * @returns {string}
     * @private
     */
    _shallowKey(node) {
        const id = node.getAttribute('id');

        return id ? node.nodeName + '#' + id : node.nodeName;
    }
}

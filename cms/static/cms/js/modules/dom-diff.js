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

        const newChildren = newNode.childNodes ? Array.from(newNode.childNodes) : [];

        // Match new children against existing ones to reuse identical DOM nodes.
        // This prevents re-execution of <script> elements that haven't changed.
        // Uses a key-based lookup (O(n)) instead of pairwise comparison (O(n²)).
        const existingChildren = Array.from(target.childNodes);
        const existingByKey = new Map();

        existingChildren.forEach((child, i) => {
            const key = this._nodeKey(child);

            if (!existingByKey.has(key)) {
                existingByKey.set(key, []);
            }
            existingByKey.get(key).push(i);
        });

        const usedIndices = new Set();

        const resolvedChildren = newChildren.map(newChild => {
            const key = this._nodeKey(newChild);
            const candidates = existingByKey.get(key);

            if (candidates) {
                for (let j = 0; j < candidates.length; j++) {
                    const idx = candidates[j];

                    if (!usedIndices.has(idx)) {
                        usedIndices.add(idx);
                        candidates.splice(j, 1);
                        return existingChildren[idx];
                    }
                }
            }
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

        const node = document.createElement(obj.nodeName);

        // Set attributes
        if (obj.attributes) {
            for (const [name, value] of Object.entries(obj.attributes)) {
                node.setAttribute(name, value);
            }
        }

        // Add child nodes
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
}

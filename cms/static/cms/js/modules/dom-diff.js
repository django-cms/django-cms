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

        // Copy child nodes
        for (const child of node.childNodes) {
            obj.childNodes.push(nodeToObj(child));
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
            // Parse HTML string
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

        // Clear existing content
        while (target.firstChild) {
            target.removeChild(target.firstChild);
        }

        // Add new content
        if (newNode.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
            // Clone all children from fragment
            while (newNode.firstChild) {
                target.appendChild(newNode.firstChild);
            }
        } else if (newNode.childNodes) {
            // Copy all child nodes
            for (const child of Array.from(newNode.childNodes)) {
                target.appendChild(child.cloneNode(true));
            }
        }
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
}

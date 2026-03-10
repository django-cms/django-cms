/*
 * Copyright https://github.com/divio/django-cms
 * Tests for dom-diff module (native browser API replacement for diff-dom)
 */

/* global describe, it, expect, beforeEach, afterEach */

'use strict';

const { DiffDOM, nodeToObj } = require('../../../static/cms/js/modules/dom-diff');

describe('DiffDOM', function() {
    let dd;
    let container;

    beforeEach(function() {
        dd = new DiffDOM();
        container = document.createElement('div');
        document.body.appendChild(container);
    });

    afterEach(function() {
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
    });

    describe('nodeToObj', function() {
        it('converts a text node to object', function() {
            const textNode = document.createTextNode('Hello World');
            const obj = nodeToObj(textNode);

            expect(obj.nodeName).toBe('#text');
            expect(obj.data).toBe('Hello World');
        });

        it('converts an element node to object', function() {
            const div = document.createElement('div');
            div.setAttribute('id', 'test');
            div.setAttribute('class', 'example');
            div.innerHTML = '<span>Text</span>';

            const obj = nodeToObj(div);

            expect(obj.nodeName).toBe('DIV');
            expect(obj.attributes.id).toBe('test');
            expect(obj.attributes.class).toBe('example');
            expect(obj.childNodes.length).toBe(1);
            expect(obj.childNodes[0].nodeName).toBe('SPAN');
        });

        it('converts a comment node to object', function() {
            var comment = document.createComment(' a comment ');
            var obj = nodeToObj(comment);

            expect(obj.nodeName).toBe('#comment');
            expect(obj.data).toBe(' a comment ');
        });

        it('preserves comments inside elements', function() {
            var div = document.createElement('div');
            div.appendChild(document.createComment('before'));
            div.appendChild(document.createElement('p'));
            div.appendChild(document.createComment('after'));

            var obj = nodeToObj(div);

            // All three children should be present, no nulls
            expect(obj.childNodes.length).toBe(3);
            expect(obj.childNodes[0].nodeName).toBe('#comment');
            expect(obj.childNodes[0].data).toBe('before');
            expect(obj.childNodes[1].nodeName).toBe('P');
            expect(obj.childNodes[2].nodeName).toBe('#comment');
            expect(obj.childNodes[2].data).toBe('after');
        });

        it('handles nested elements', function() {
            const div = document.createElement('div');
            div.innerHTML = '<ul><li>Item 1</li><li>Item 2</li></ul>';

            const obj = nodeToObj(div);

            expect(obj.nodeName).toBe('DIV');
            expect(obj.childNodes.length).toBe(1);
            expect(obj.childNodes[0].nodeName).toBe('UL');
            expect(obj.childNodes[0].childNodes.length).toBe(2);
        });
    });

    describe('diff and apply', function() {
        it('applies simple HTML string to empty container', function() {
            const diff = dd.diff(container, '<div><p>Hello</p></div>');
            dd.apply(container, diff);

            expect(container.children.length).toBe(1);
            expect(container.children[0].tagName).toBe('P');
            expect(container.children[0].textContent).toBe('Hello');
        });

        it('replaces existing content with new HTML', function() {
            container.innerHTML = '<p>Old content</p>';

            const diff = dd.diff(container, '<div><span>New content</span></div>');
            dd.apply(container, diff);

            expect(container.children.length).toBe(1);
            expect(container.children[0].tagName).toBe('SPAN');
            expect(container.children[0].textContent).toBe('New content');
        });

        it('handles multiple child elements', function() {
            const diff = dd.diff(container, '<div><p>First</p><p>Second</p><p>Third</p></div>');
            dd.apply(container, diff);

            expect(container.children.length).toBe(3);
            expect(container.children[0].textContent).toBe('First');
            expect(container.children[1].textContent).toBe('Second');
            expect(container.children[2].textContent).toBe('Third');
        });

        it('preserves attributes when applying diff', function() {
            const html = '<div><a href="/test" class="link" data-id="123">Link</a></div>';
            const diff = dd.diff(container, html);
            dd.apply(container, diff);

            const link = container.querySelector('a');
            expect(link).not.toBeNull();
            expect(link.getAttribute('href')).toBe('/test');
            expect(link.getAttribute('class')).toBe('link');
            expect(link.getAttribute('data-id')).toBe('123');
            expect(link.textContent).toBe('Link');
        });

        it('handles complex nested structures', function() {
            const html = `<div>
                <div class="header">
                    <h1>Title</h1>
                    <nav>
                        <ul>
                            <li><a href="#">Home</a></li>
                            <li><a href="#">About</a></li>
                        </ul>
                    </nav>
                </div>
                <div class="content">
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </div>
            </div>`;

            const diff = dd.diff(container, html);
            dd.apply(container, diff);

            expect(container.querySelector('.header')).not.toBeNull();
            expect(container.querySelector('.content')).not.toBeNull();
            expect(container.querySelector('h1').textContent).toBe('Title');
            expect(container.querySelectorAll('li').length).toBe(2);
            expect(container.querySelectorAll('.content p').length).toBe(2);
        });

        it('handles script tags correctly', function() {
            const html = '<div><script>console.log("test");</script><p>Content</p></div>';
            const diff = dd.diff(container, html);
            dd.apply(container, diff);

            expect(container.querySelector('script')).not.toBeNull();
            expect(container.querySelector('p')).not.toBeNull();
        });

        it('clears container when applying empty content', function() {
            container.innerHTML = '<p>Old</p><p>Content</p>';

            const diff = dd.diff(container, '<div></div>');
            dd.apply(container, diff);

            expect(container.children.length).toBe(0);
        });

        it('works with nodeToObj conversion', function() {
            const original = document.createElement('div');
            original.innerHTML = '<span class="test">Text content</span>';

            const obj = nodeToObj(original);
            const diff = dd.diff(container, obj);
            dd.apply(container, diff);

            expect(container.querySelector('span')).not.toBeNull();
            expect(container.querySelector('span').className).toBe('test');
            expect(container.querySelector('span').textContent).toBe('Text content');
        });

        it('preserves comment nodes through round-trip', function() {
            var original = document.createElement('div');
            original.appendChild(document.createComment(' server-rendered '));
            original.appendChild(document.createElement('p'));
            original.appendChild(document.createComment(' end '));

            var obj = nodeToObj(original);
            var diff = dd.diff(container, obj);
            dd.apply(container, diff);

            // Comments should survive the nodeToObj -> _objToNode -> apply round-trip
            expect(container.childNodes.length).toBe(3);
            expect(container.childNodes[0].nodeType).toBe(Node.COMMENT_NODE);
            expect(container.childNodes[0].data).toBe(' server-rendered ');
            expect(container.childNodes[1].nodeName).toBe('P');
            expect(container.childNodes[2].nodeType).toBe(Node.COMMENT_NODE);
            expect(container.childNodes[2].data).toBe(' end ');
        });

        it('preserves text nodes with whitespace', function() {
            const html = '<div><p>  Text with   spaces  </p></div>';
            const diff = dd.diff(container, html);
            dd.apply(container, diff);

            expect(container.querySelector('p').textContent).toBe('  Text with   spaces  ');
        });

        it('handles special characters in text', function() {
            const html = '<div><p>&lt;script&gt;alert("xss")&lt;/script&gt;</p></div>';
            const diff = dd.diff(container, html);
            dd.apply(container, diff);

            expect(container.querySelector('p').textContent).toContain('<script>');
            expect(container.querySelector('p').textContent).toContain('</script>');
        });
    });

    describe('real-world use cases from cms.structureboard', function() {
        it('simulates updating a plugin container', function() {
            // Initial state: empty container
            const pluginContainer = document.createElement('div');
            pluginContainer.className = 'cms-plugin';
            document.body.appendChild(pluginContainer);

            // Simulate server response with new plugin content
            const serverHTML = `<div>
                <div class="cms-plugin-wrapper">
                    <div class="cms-plugin-content">
                        <h2>New Plugin</h2>
                        <p>Updated content from server</p>
                    </div>
                </div>
            </div>`;

            const diff = dd.diff(pluginContainer, serverHTML);
            dd.apply(pluginContainer, diff);

            expect(pluginContainer.querySelector('.cms-plugin-wrapper')).not.toBeNull();
            expect(pluginContainer.querySelector('h2').textContent).toBe('New Plugin');
            expect(pluginContainer.querySelector('p').textContent).toBe('Updated content from server');

            pluginContainer.parentNode.removeChild(pluginContainer);
        });

        it('simulates updating document head metadata', function() {
            // Create a mock head element
            const mockHead = document.createElement('div');
            mockHead.innerHTML = `
                <title>Old Title</title>
                <meta name="description" content="Old description">
            `;

            // New head content from server
            const newHeadObj = {
                nodeName: 'HEAD',
                attributes: {},
                childNodes: [
                    {
                        nodeName: 'TITLE',
                        attributes: {},
                        childNodes: [
                            {
                                nodeName: '#text',
                                data: 'New Title'
                            }
                        ]
                    },
                    {
                        nodeName: 'META',
                        attributes: {
                            name: 'description',
                            content: 'New description'
                        },
                        childNodes: []
                    },
                    {
                        nodeName: 'LINK',
                        attributes: {
                            rel: 'stylesheet',
                            href: '/static/new.css'
                        },
                        childNodes: []
                    }
                ]
            };

            const diff = dd.diff(mockHead, newHeadObj);
            dd.apply(mockHead, diff);

            expect(mockHead.querySelector('title').textContent).toBe('New Title');
            expect(mockHead.querySelector('meta[name="description"]').getAttribute('content')).toBe('New description');
            expect(mockHead.querySelector('link[rel="stylesheet"]').getAttribute('href')).toBe('/static/new.css');
        });

        it('handles forms with input elements', function() {
            const formHTML = `<div>
                <form id="test-form" action="/submit" method="post">
                    <input type="text" name="username" value="testuser" required>
                    <input type="email" name="email" placeholder="email@example.com">
                    <textarea name="message">Default message</textarea>
                    <select name="country">
                        <option value="de">Germany</option>
                        <option value="us" selected>USA</option>
                    </select>
                    <button type="submit">Submit</button>
                </form>
            </div>`;

            const diff = dd.diff(container, formHTML);
            dd.apply(container, diff);

            const form = container.querySelector('form');
            expect(form.getAttribute('action')).toBe('/submit');
            expect(form.getAttribute('method')).toBe('post');

            const usernameInput = container.querySelector('input[name="username"]');
            expect(usernameInput.getAttribute('value')).toBe('testuser');
            expect(usernameInput.hasAttribute('required')).toBe(true);

            const textarea = container.querySelector('textarea');
            expect(textarea.textContent).toBe('Default message');

            const select = container.querySelector('select');
            expect(select.querySelectorAll('option').length).toBe(2);
        });
    });

    describe('edge cases and error handling', function() {
        it('handles null or undefined gracefully', function() {
            expect(function() {
                nodeToObj(null);
            }).not.toThrow();
        });

        it('handles malformed HTML', function() {
            // Parser should handle malformed HTML gracefully
            const malformedHTML = '<div><p>Unclosed paragraph<div>Nested</div>';
            const diff = dd.diff(container, malformedHTML);

            expect(function() {
                dd.apply(container, diff);
            }).not.toThrow();
        });

        it('does not re-execute identical script elements', function() {
            // Set up container with a script that sets a global counter
            var script = document.createElement('script');
            script.textContent = 'window.__domDiffTestCounter = (window.__domDiffTestCounter || 0) + 1;';
            container.appendChild(script);

            // Script executed once on initial insert
            expect(window.__domDiffTestCounter).toBe(1);

            // Build a new node with an identical script
            var wrapper = document.createElement('div');
            var identicalScript = document.createElement('script');
            identicalScript.textContent = 'window.__domDiffTestCounter = (window.__domDiffTestCounter || 0) + 1;';
            wrapper.appendChild(identicalScript);

            var diff = dd.diff(container, nodeToObj(wrapper));
            dd.apply(container, diff);

            // Counter should still be 1 — the identical script was reused, not re-executed
            expect(window.__domDiffTestCounter).toBe(1);

            delete window.__domDiffTestCounter;
        });

        it('executes new script elements that differ from existing ones', function() {
            var script = document.createElement('script');
            script.textContent = 'window.__domDiffNewCounter = 1;';
            container.appendChild(script);

            expect(window.__domDiffNewCounter).toBe(1);

            // Apply diff with a different script
            var wrapper = document.createElement('div');
            var newScript = document.createElement('script');
            newScript.textContent = 'window.__domDiffNewCounter = 42;';
            wrapper.appendChild(newScript);

            var diff = dd.diff(container, nodeToObj(wrapper));
            dd.apply(container, diff);

            // New script should have executed
            expect(window.__domDiffNewCounter).toBe(42);

            delete window.__domDiffNewCounter;
        });

        it('handles SVG elements', function() {
            const svgHTML = `<div>
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red" />
                </svg>
            </div>`;

            const diff = dd.diff(container, svgHTML);
            dd.apply(container, diff);

            expect(container.querySelector('svg')).not.toBeNull();
            expect(container.querySelector('circle')).not.toBeNull();
        });
    });
});

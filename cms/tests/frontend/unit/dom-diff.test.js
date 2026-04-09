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

        it('reuses unchanged nodes (same DOM reference) and removes changed ones', function() {
            // Set up container with three children
            var meta = document.createElement('meta');
            meta.setAttribute('name', 'description');
            meta.setAttribute('content', 'Original');
            meta.marker = 'meta'; // Custom property to identify this node

            var link = document.createElement('link');
            link.setAttribute('rel', 'stylesheet');
            link.setAttribute('href', '/static/style.css');

            var title = document.createElement('title');
            title.textContent = 'Old Title';

            container.appendChild(meta);
            container.appendChild(link);
            container.appendChild(title);

            // Keep references to the original DOM nodes
            var originalMeta = container.childNodes[0];
            var originalLink = container.childNodes[1];


            // Build new content: link unchanged, meta changed, title removed, script added
            var wrapper = document.createElement('div');

            var newMeta = document.createElement('meta');
            newMeta.setAttribute('name', 'description');
            newMeta.setAttribute('content', 'Updated');
            wrapper.appendChild(newMeta);

            var sameLinkCopy = document.createElement('link');
            sameLinkCopy.setAttribute('rel', 'stylesheet');
            sameLinkCopy.setAttribute('href', '/static/style.css');
            wrapper.appendChild(sameLinkCopy);

            var newScript = document.createElement('script');
            newScript.setAttribute('src', '/static/app.js');
            wrapper.appendChild(newScript);

            var diff = dd.diff(container, nodeToObj(wrapper));
            dd.apply(container, diff);

            // Link was unchanged — must be the exact same DOM node (not a clone)
            expect(container.childNodes.length).toBe(3);
            expect(container.childNodes[1]).toBe(originalLink);

            // Meta had its content attribute changed — with recursive diffing the
            // outer element is reused (shallow match on tag + name attr) and the
            // attribute is synced in place.
            expect(container.childNodes[0]).toBe(originalMeta);
            expect(container.childNodes[0].getAttribute('content')).toBe('Updated');
            expect(container.childNodes[0].marker).toBe('meta'); // Custom property preserved

            // Title was removed
            expect(container.querySelector('title')).toBeNull();

            // Script was added
            expect(container.querySelector('script')).not.toBeNull();
            expect(container.querySelector('script').getAttribute('src')).toBe('/static/app.js');
        });

        it('removes all unmatched nodes even when keys collide', function() {
            // Multiple identical whitespace text nodes — a common case in <head>
            var p1 = document.createElement('p');
            p1.textContent = 'Keep';
            p1.marker = 'marked'; // Custom property to identify this node
            var p2 = document.createElement('p');
            p2.textContent = 'Remove';

            container.appendChild(document.createTextNode('\n'));
            container.appendChild(p1);
            container.appendChild(document.createTextNode('\n'));
            container.appendChild(p2);
            container.appendChild(document.createTextNode('\n'));

            var originalP1 = p1;

            // New content: only one <p> and two text nodes
            var wrapper = document.createElement('div');
            wrapper.appendChild(document.createTextNode('\n'));
            var pKeep = document.createElement('p');
            pKeep.textContent = 'Keep';
            wrapper.appendChild(pKeep);
            wrapper.appendChild(document.createTextNode('\n'));

            var diff = dd.diff(container, nodeToObj(wrapper));
            dd.apply(container, diff);

            // Should have exactly 3 children: text, p, text
            expect(container.childNodes.length).toBe(3);
            expect(container.childNodes[1].textContent).toBe('Keep');
            expect(container.childNodes[1]).toBe(originalP1);

            // "Remove" paragraph must be gone
            expect(container.querySelector('p:last-of-type').textContent).toBe('Keep');
            expect(container.querySelector('p:last-of-type').marker).toBe('marked');
        });

        it('does not re-execute nested scripts when outer element changes', function() {
            // Set up container with a div wrapping a script
            var wrapper = document.createElement('div');
            wrapper.setAttribute('class', 'plugin');
            var script = document.createElement('script');
            script.textContent = 'window.__nestedScriptCounter = (window.__nestedScriptCounter || 0) + 1;';
            wrapper.appendChild(script);
            var p = document.createElement('p');
            p.textContent = 'Old text';
            wrapper.appendChild(p);
            container.appendChild(wrapper);

            // Script executed once on initial insert
            expect(window.__nestedScriptCounter).toBe(1);

            var originalScript = container.querySelector('script');
            var originalWrapper = container.firstChild;

            // Build new content: same div wrapper, same script, but paragraph text changed
            var newOuter = document.createElement('div');
            var newWrapper = document.createElement('div');
            newWrapper.setAttribute('class', 'plugin');
            var sameScript = document.createElement('script');
            sameScript.textContent = 'window.__nestedScriptCounter = (window.__nestedScriptCounter || 0) + 1;';
            newWrapper.appendChild(sameScript);
            var newP = document.createElement('p');
            newP.textContent = 'New text';
            newWrapper.appendChild(newP);
            newOuter.appendChild(newWrapper);

            var diff = dd.diff(container, nodeToObj(newOuter));
            dd.apply(container, diff);

            // Script should NOT have re-executed — counter still 1
            expect(window.__nestedScriptCounter).toBe(1);
            // Script should be the exact same DOM node
            expect(container.querySelector('script')).toBe(originalScript);
            // Outer wrapper should be preserved (shallow match, same tag + class synced)
            expect(container.firstChild).toBe(originalWrapper);
            // Paragraph text should be updated
            expect(container.querySelector('p').textContent).toBe('New text');

            delete window.__nestedScriptCounter;
        });

        it('preserves outer element when only inner content changes', function() {
            var outer = document.createElement('div');
            outer.setAttribute('class', 'outer');
            outer.marker = 'original-outer';
            var inner = document.createElement('span');
            inner.textContent = 'old';
            outer.appendChild(inner);
            container.appendChild(outer);

            var originalOuter = container.firstChild;

            // Build new content: same outer div, different inner text
            var newRoot = document.createElement('div');
            var newOuter = document.createElement('div');
            newOuter.setAttribute('class', 'outer');
            var newInner = document.createElement('span');
            newInner.textContent = 'new';
            newOuter.appendChild(newInner);
            newRoot.appendChild(newOuter);

            var diff = dd.diff(container, nodeToObj(newRoot));
            dd.apply(container, diff);

            // Outer element should be the same DOM node (preserved via shallow match)
            expect(container.firstChild).toBe(originalOuter);
            expect(container.firstChild.marker).toBe('original-outer');
            // Inner content should be updated
            expect(container.querySelector('span').textContent).toBe('new');
        });

        it('updates attributes on outer element while preserving it', function() {
            var outer = document.createElement('div');
            outer.setAttribute('class', 'old-class');
            outer.setAttribute('data-keep', 'yes');
            outer.marker = 'same-node';
            var inner = document.createElement('p');
            inner.textContent = 'content';
            outer.appendChild(inner);
            container.appendChild(outer);

            var originalOuter = container.firstChild;

            // Build new content: same div, different class, removed data-keep, added data-new
            var newRoot = document.createElement('div');
            var newOuter = document.createElement('div');
            newOuter.setAttribute('class', 'new-class');
            newOuter.setAttribute('data-new', 'added');
            var newInner = document.createElement('p');
            newInner.textContent = 'content';
            newOuter.appendChild(newInner);
            newRoot.appendChild(newOuter);

            var diff = dd.diff(container, nodeToObj(newRoot));
            dd.apply(container, diff);

            // Same DOM node preserved
            expect(container.firstChild).toBe(originalOuter);
            expect(container.firstChild.marker).toBe('same-node');
            // Attributes synced
            expect(container.firstChild.getAttribute('class')).toBe('new-class');
            expect(container.firstChild.getAttribute('data-new')).toBe('added');
            expect(container.firstChild.getAttribute('data-keep')).toBeNull();
        });

        it('does not re-execute deeply nested scripts', function() {
            // Three levels deep: container > div.a > div.b > script
            var a = document.createElement('div');
            a.setAttribute('class', 'a');
            var b = document.createElement('div');
            b.setAttribute('class', 'b');
            var script = document.createElement('script');
            script.textContent = 'window.__deepCounter = (window.__deepCounter || 0) + 1;';
            b.appendChild(script);
            a.appendChild(b);
            container.appendChild(a);

            expect(window.__deepCounter).toBe(1);
            var originalScript = container.querySelector('script');

            // Build new content: add a sibling to div.b, script unchanged
            var newRoot = document.createElement('div');
            var newA = document.createElement('div');
            newA.setAttribute('class', 'a');
            var newB = document.createElement('div');
            newB.setAttribute('class', 'b');
            var sameScript = document.createElement('script');
            sameScript.textContent = 'window.__deepCounter = (window.__deepCounter || 0) + 1;';
            newB.appendChild(sameScript);
            var extra = document.createElement('p');
            extra.textContent = 'added';
            newB.appendChild(extra);
            newA.appendChild(newB);
            newRoot.appendChild(newA);

            var diff = dd.diff(container, nodeToObj(newRoot));
            dd.apply(container, diff);

            // Script must not have re-executed
            expect(window.__deepCounter).toBe(1);
            expect(container.querySelector('script')).toBe(originalScript);
            // New paragraph should be present
            expect(container.querySelector('p').textContent).toBe('added');

            delete window.__deepCounter;
        });

        it('applies plain text string without losing content', function() {
            // When newContent is a plain string like 'hello', DOMParser produces
            // a text node as doc.body.firstChild. apply() must handle this and
            // set the target's textContent rather than clearing it. (#8556 related)
            container.innerHTML = '<p>Old</p>';

            var diff = dd.diff(container, 'hello');
            dd.apply(container, diff);

            expect(container.textContent).toBe('hello');
        });

        it('applies text-node object without losing content', function() {
            // When newContent is a #text object, _objToNode returns a text node.
            // apply() must handle this and preserve the text.
            container.innerHTML = '<p>Old</p>';

            var diff = dd.diff(container, { nodeName: '#text', data: 'from object' });
            dd.apply(container, diff);

            expect(container.textContent).toBe('from object');
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

import { describe, expect, it } from 'vitest';
import {
    DiffDOM,
    nodeToObj,
} from '../../frontend/modules/structureboard/parsers/diff';

describe('parsers/diff — nodeToObj', () => {
    it('serialises a simple element with attributes', () => {
        const div = document.createElement('div');
        div.id = 'a';
        div.setAttribute('data-x', '1');
        div.textContent = 'hi';
        const obj = nodeToObj(div);
        expect(obj).toEqual({
            nodeName: 'DIV',
            attributes: { id: 'a', 'data-x': '1' },
            childNodes: [{ nodeName: '#text', data: 'hi' }],
        });
    });

    it('serialises text and comment leaves', () => {
        expect(nodeToObj(document.createTextNode('hello'))).toEqual({
            nodeName: '#text',
            data: 'hello',
        });
        expect(nodeToObj(document.createComment('note'))).toEqual({
            nodeName: '#comment',
            data: 'note',
        });
    });

    it('returns null for null/undefined', () => {
        expect(nodeToObj(null)).toBeNull();
        expect(nodeToObj(undefined)).toBeNull();
    });

    it('round-trips nested elements', () => {
        const root = document.createElement('section');
        root.innerHTML = `<p>one</p><p>two</p>`;
        const obj = nodeToObj(root);
        expect(obj).not.toBeNull();
        if (obj && 'childNodes' in obj) {
            expect(obj.childNodes).toHaveLength(2);
        }
    });
});

describe('parsers/diff — DiffDOM.diff + apply', () => {
    it('returns the parsed new node from an HTML string', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        const result = dd.diff(target, '<span>hi</span>');
        expect(result.newNode).not.toBeNull();
        expect((result.newNode as Element).tagName).toBe('SPAN');
    });

    it('apply replaces children to match', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = '<p>old</p>';
        const newRoot = document.createElement('div');
        newRoot.innerHTML = '<p>new</p>';
        dd.apply(target, { oldNode: target, newNode: newRoot });
        expect(target.innerHTML).toBe('<p>new</p>');
    });

    it('apply is a no-op when innerHTML matches', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = '<p>same</p>';
        const child = target.firstChild!;
        const newRoot = document.createElement('div');
        newRoot.innerHTML = '<p>same</p>';
        dd.apply(target, { oldNode: target, newNode: newRoot });
        // Same DOM node — no replacement.
        expect(target.firstChild).toBe(child);
    });

    it('apply preserves identical leaf children (tier 1 exact match)', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = '<p>keep</p><span>old</span>';
        const keep = target.querySelector('p')!;
        const newRoot = document.createElement('div');
        newRoot.innerHTML = '<p>keep</p><span>new</span>';
        dd.apply(target, { oldNode: target, newNode: newRoot });
        // The <p> is reused, the <span> is updated/cloned.
        expect(target.querySelector('p')).toBe(keep);
        expect(target.querySelector('span')?.textContent).toBe('new');
    });

    it('apply syncs attributes on shallow-key match', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = '<section id="hero" data-x="1">old</section>';
        const sec = target.querySelector('section')!;
        const newRoot = document.createElement('div');
        newRoot.innerHTML = '<section id="hero" data-x="2">new</section>';
        dd.apply(target, { oldNode: target, newNode: newRoot });
        // Shallow match (tag + id) → outer node retained, attributes synced.
        expect(target.querySelector('section')).toBe(sec);
        expect(sec.getAttribute('data-x')).toBe('2');
        expect(sec.textContent).toBe('new');
    });

    it('apply removes attributes absent from source', () => {
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = '<section id="x" data-stale="yes"></section>';
        const newRoot = document.createElement('div');
        newRoot.innerHTML = '<section id="x"></section>';
        dd.apply(target, { oldNode: target, newNode: newRoot });
        const sec = target.querySelector('section')!;
        expect(sec.hasAttribute('data-stale')).toBe(false);
    });

    it('apply preserves external scripts even when removed', () => {
        // External scripts (with src) should NOT be removed by tier 3 cleanup.
        const dd = new DiffDOM();
        const target = document.createElement('div');
        target.innerHTML = `
            <script src="/keep.js"></script>
            <p>old</p>
        `;
        const ext = target.querySelector('script')!;
        const newRoot = document.createElement('div');
        newRoot.innerHTML = `<p>new</p>`;
        dd.apply(target, { oldNode: target, newNode: newRoot });
        // External script preserved.
        expect(target.contains(ext)).toBe(true);
    });

    it('handles text-only target', () => {
        const dd = new DiffDOM();
        const target = document.createTextNode('old');
        const newNode = document.createTextNode('new');
        dd.apply(target, { oldNode: target, newNode });
        expect(target.textContent).toBe('new');
    });
});

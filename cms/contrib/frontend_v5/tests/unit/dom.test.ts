import { beforeEach, describe, expect, it } from 'vitest';
import { $, $$, addClass, closest, html, removeClass, toggleClass } from '../../frontend/modules/dom';

describe('dom', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="root">
                <ul class="list">
                    <li class="item one" data-id="1">first</li>
                    <li class="item two" data-id="2">second</li>
                    <li class="item three" data-id="3">third</li>
                </ul>
            </div>
        `;
    });

    describe('$', () => {
        it('returns the first matching element', () => {
            const item = $<HTMLLIElement>('.item');
            expect(item).not.toBeNull();
            expect(item?.dataset.id).toBe('1');
        });

        it('returns null when no match', () => {
            expect($('.nope')).toBeNull();
        });

        it('scopes to a given root', () => {
            const list = $('.list')!;
            const found = $('.item.two', list);
            expect(found?.textContent).toBe('second');
        });
    });

    describe('$$', () => {
        it('returns a real array of matches', () => {
            const items = $$('.item');
            expect(items).toBeInstanceOf(Array);
            expect(items).toHaveLength(3);
            expect(items.map((el) => el.dataset.id)).toEqual(['1', '2', '3']);
        });

        it('returns an empty array when no match', () => {
            expect($$('.nope')).toEqual([]);
        });

        it('scopes to a given root', () => {
            const list = $('.list')!;
            expect($$('.item', list)).toHaveLength(3);
        });
    });

    describe('closest', () => {
        it('finds an ancestor matching the selector', () => {
            const item = $('.item.two')!;
            const list = closest(item, '.list');
            expect(list).not.toBeNull();
            expect(list?.classList.contains('list')).toBe(true);
        });

        it('returns null for null input', () => {
            expect(closest(null, '.list')).toBeNull();
        });

        it('returns null when no ancestor matches', () => {
            const item = $('.item.two')!;
            expect(closest(item, '.does-not-exist')).toBeNull();
        });
    });

    describe('addClass / removeClass / toggleClass', () => {
        it('adds and removes single classes', () => {
            const el = $('.item.one')!;
            addClass(el, 'highlighted');
            expect(el.classList.contains('highlighted')).toBe(true);
            removeClass(el, 'highlighted');
            expect(el.classList.contains('highlighted')).toBe(false);
        });

        it('adds and removes multiple classes at once', () => {
            const el = $('.item.one')!;
            addClass(el, 'a', 'b', 'c');
            expect(el.classList.contains('a')).toBe(true);
            expect(el.classList.contains('b')).toBe(true);
            expect(el.classList.contains('c')).toBe(true);
            removeClass(el, 'a', 'c');
            expect(el.classList.contains('a')).toBe(false);
            expect(el.classList.contains('b')).toBe(true);
            expect(el.classList.contains('c')).toBe(false);
        });

        it('ignores empty class tokens', () => {
            const el = $('.item.one')!;
            const before = el.className;
            addClass(el, '');
            removeClass(el, '');
            expect(el.className).toBe(before);
        });

        it('toggles a class and returns the new state', () => {
            const el = $('.item.one')!;
            expect(toggleClass(el, 'active')).toBe(true);
            expect(el.classList.contains('active')).toBe(true);
            expect(toggleClass(el, 'active')).toBe(false);
            expect(el.classList.contains('active')).toBe(false);
        });

        it('toggleClass respects the `force` argument', () => {
            const el = $('.item.one')!;
            expect(toggleClass(el, 'active', true)).toBe(true);
            expect(toggleClass(el, 'active', true)).toBe(true);
            expect(toggleClass(el, 'active', false)).toBe(false);
            expect(toggleClass(el, 'active', false)).toBe(false);
        });
    });

    describe('html', () => {
        it('parses a single root element', () => {
            const el = html<HTMLDivElement>('<div class="x">hi</div>');
            expect(el.tagName).toBe('DIV');
            expect(el.className).toBe('x');
            expect(el.textContent).toBe('hi');
        });

        it('trims surrounding whitespace before parsing', () => {
            const el = html('   <span>ok</span>   ');
            expect(el.tagName).toBe('SPAN');
        });

        it('throws when the input has multiple roots', () => {
            expect(() => html('<div></div><div></div>')).toThrow(/expected exactly 1/);
        });

        it('throws when the input is empty', () => {
            expect(() => html('   ')).toThrow(/expected exactly 1/);
        });
    });
});

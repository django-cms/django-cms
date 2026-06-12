import { beforeEach, describe, expect, it } from 'vitest';
import {
    setExpanded,
    setGroupRole,
    setLevel,
    setPosInSet,
    setSelected,
    setSetSize,
    setTreeItemRole,
    setTreeRole,
} from '../../frontend/modules/tree/aria';

describe('tree aria', () => {
    let el: HTMLElement;

    beforeEach(() => {
        el = document.createElement('div');
    });

    it('setTreeRole / setGroupRole / setTreeItemRole', () => {
        setTreeRole(el);
        expect(el.getAttribute('role')).toBe('tree');
        setGroupRole(el);
        expect(el.getAttribute('role')).toBe('group');
        setTreeItemRole(el);
        expect(el.getAttribute('role')).toBe('treeitem');
    });

    describe('setExpanded', () => {
        it('sets aria-expanded="true" on an expandable, expanded item', () => {
            setExpanded(el, true, true);
            expect(el.getAttribute('aria-expanded')).toBe('true');
        });

        it('sets aria-expanded="false" on an expandable, collapsed item', () => {
            setExpanded(el, true, false);
            expect(el.getAttribute('aria-expanded')).toBe('false');
        });

        it('REMOVES aria-expanded entirely on a leaf (not expandable)', () => {
            // Pre-populate to ensure removal works.
            el.setAttribute('aria-expanded', 'false');
            setExpanded(el, false, false);
            expect(el.hasAttribute('aria-expanded')).toBe(false);
        });

        it('removes aria-expanded on a leaf even if expanded=true is passed', () => {
            el.setAttribute('aria-expanded', 'true');
            setExpanded(el, false, true);
            expect(el.hasAttribute('aria-expanded')).toBe(false);
        });
    });

    it('setSelected', () => {
        setSelected(el, true);
        expect(el.getAttribute('aria-selected')).toBe('true');
        setSelected(el, false);
        expect(el.getAttribute('aria-selected')).toBe('false');
    });

    describe('setLevel', () => {
        it('sets a 1-based level', () => {
            setLevel(el, 1);
            expect(el.getAttribute('aria-level')).toBe('1');
            setLevel(el, 5);
            expect(el.getAttribute('aria-level')).toBe('5');
        });

        it('throws on level < 1', () => {
            expect(() => setLevel(el, 0)).toThrow(/level must be >= 1/);
            expect(() => setLevel(el, -1)).toThrow(/level must be >= 1/);
        });
    });

    describe('setSetSize', () => {
        it('sets the sibling-set size', () => {
            setSetSize(el, 7);
            expect(el.getAttribute('aria-setsize')).toBe('7');
        });

        it('throws on size < 1', () => {
            expect(() => setSetSize(el, 0)).toThrow(/size must be >= 1/);
        });
    });

    describe('setPosInSet', () => {
        it('sets a 1-based position', () => {
            setPosInSet(el, 1);
            expect(el.getAttribute('aria-posinset')).toBe('1');
            setPosInSet(el, 4);
            expect(el.getAttribute('aria-posinset')).toBe('4');
        });

        it('throws on position < 1', () => {
            expect(() => setPosInSet(el, 0)).toThrow(/position must be >= 1/);
        });
    });
});

import { describe, expect, it } from 'vitest';
import {
    getId,
    getIds,
    parseDragareaId,
    parseDragbarId,
    parseDraggableId,
    parsePlaceholderId,
    parsePluginId,
} from '../../frontend/modules/structureboard/parsers/ids';

function el(...classes: string[]): Element {
    const node = document.createElement('div');
    for (const c of classes) node.classList.add(c);
    return node;
}

describe('parsers/ids — getId', () => {
    it('reads cms-plugin-{id}', () => {
        expect(getId(el('cms-plugin', 'cms-plugin-42'))).toBe(42);
    });

    it('reads cms-draggable-{id}', () => {
        expect(getId(el('cms-draggable', 'cms-draggable-9'))).toBe(9);
    });

    it('reads cms-placeholder-{id}', () => {
        expect(getId(el('cms-placeholder', 'cms-placeholder-7'))).toBe(7);
    });

    it('reads cms-dragbar-{id}', () => {
        expect(getId(el('cms-dragbar', 'cms-dragbar-3'))).toBe(3);
    });

    it('reads cms-dragarea-{id}', () => {
        expect(getId(el('cms-dragarea', 'cms-dragarea-12'))).toBe(12);
    });

    it('returns undefined for elements with no matching class', () => {
        expect(getId(el('cms-foo'))).toBeUndefined();
        expect(getId(el())).toBeUndefined();
    });

    it('handles null/undefined input', () => {
        expect(getId(null)).toBeUndefined();
        expect(getId(undefined)).toBeUndefined();
    });

    it('does not depend on class order (legacy fragility fix)', () => {
        // Legacy `getId` read `class.split(' ')[1]` — fragile.
        // Our port walks the full classList.
        expect(getId(el('extra-class', 'cms-plugin', 'cms-plugin-99'))).toBe(99);
    });
});

describe('parsers/ids — getIds', () => {
    it('maps over an iterable, dropping misses', () => {
        const list = [
            el('cms-draggable', 'cms-draggable-1'),
            el('cms-other'),
            el('cms-draggable', 'cms-draggable-2'),
        ];
        expect(getIds(list)).toEqual([1, 2]);
    });

    it('works with NodeList', () => {
        const root = document.createElement('div');
        root.innerHTML = `
            <div class="cms-plugin cms-plugin-5"></div>
            <div class="cms-plugin cms-plugin-6"></div>
        `;
        expect(getIds(root.querySelectorAll('.cms-plugin'))).toEqual([5, 6]);
    });
});

describe('parsers/ids — kind-specific shortcuts', () => {
    it('parseDraggableId only matches cms-draggable-{id}', () => {
        expect(parseDraggableId(el('cms-draggable', 'cms-draggable-1'))).toBe(1);
        expect(parseDraggableId(el('cms-plugin', 'cms-plugin-1'))).toBeUndefined();
    });

    it('parseDragareaId only matches cms-dragarea-{id}', () => {
        expect(parseDragareaId(el('cms-dragarea', 'cms-dragarea-7'))).toBe(7);
        expect(parseDragareaId(el('cms-dragbar', 'cms-dragbar-7'))).toBeUndefined();
    });

    it('parseDragbarId only matches cms-dragbar-{id}', () => {
        expect(parseDragbarId(el('cms-dragbar', 'cms-dragbar-3'))).toBe(3);
        expect(parseDragbarId(el('cms-dragarea', 'cms-dragarea-3'))).toBeUndefined();
    });

    it('parsePlaceholderId only matches cms-placeholder-{id}', () => {
        expect(parsePlaceholderId(el('cms-placeholder', 'cms-placeholder-2'))).toBe(2);
    });

    it('parsePluginId only matches cms-plugin-{id}', () => {
        expect(parsePluginId(el('cms-plugin', 'cms-plugin-42'))).toBe(42);
    });

    it('returns undefined on null', () => {
        expect(parseDraggableId(null)).toBeUndefined();
        expect(parseDragareaId(null)).toBeUndefined();
    });
});

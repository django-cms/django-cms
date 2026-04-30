import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    clickToHighlightHandler,
    highlightPluginContent,
    highlightPluginStructure,
    removeHighlightPluginContent,
} from '../../frontend/modules/plugins/ui/highlight';

describe('highlight — highlightPluginContent', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        // Force getBoundingClientRect to return a non-zero rect so the
        // overlay gets created (jsdom returns zeroes by default).
        Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
            configurable: true,
            value: function () {
                return { left: 10, top: 20, width: 100, height: 50, right: 110, bottom: 70, x: 10, y: 20, toJSON: () => ({}) };
            },
        });
    });
    afterEach(() => {
        vi.useRealTimers();
        document.body.innerHTML = '';
    });

    it('appends an overlay element matching the plugin id', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-42"></div>`;
        highlightPluginContent(42, { successTimeout: 0 });
        expect(document.querySelector('.cms-plugin-overlay-42')).not.toBeNull();
    });

    it('does nothing when no matching plugin is on the page', () => {
        highlightPluginContent(99, { successTimeout: 0 });
        expect(document.querySelector('.cms-plugin-overlay-99')).toBeNull();
    });

    it('schedules removal after delay + successTimeout', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-42"></div>`;
        highlightPluginContent(42, { successTimeout: 100, delay: 200 });
        expect(document.querySelector('.cms-plugin-overlay-42')).not.toBeNull();
        // delay + transition time
        vi.advanceTimersByTime(400);
        expect(document.querySelector('.cms-plugin-overlay-42')).toBeNull();
    });

    it('ignores elements that have only the cms-plugin-<id> class without cms-plugin', () => {
        // Stray markup carrying a `cms-plugin-<id>`-shaped token but
        // not the `cms-plugin` parent class must NOT trigger an
        // overlay. Mirrors the legacy `cms.structureboard.js`
        // convention of using the compound `.cms-plugin.cms-plugin-<id>`.
        document.body.innerHTML = `<div class="cms-plugin-55"></div>`;
        highlightPluginContent(55, { successTimeout: 0 });
        expect(document.querySelector('.cms-plugin-overlay-55')).toBeNull();
    });

    it('skips <template> markers when bracketed plugin content is unprocessed', () => {
        // Before `processTemplateGroup` runs, a plugin's only DOM
        // representation is a pair of `<template class="cms-plugin
        // cms-plugin-<id> cms-plugin-start/end">` markers anchored at
        // (0, 0). If those slip into the bbox, the overlay stretches
        // from the top-left of the page across the whole content area
        // — which lands on top of the structure board in condensed
        // mode and looks like a stray drag preview.
        // Stub getBoundingClientRect so templates report (1px tall,
        // origin) — a real-browser quirk we want to defend against.
        const realRect = HTMLElement.prototype.getBoundingClientRect;
        Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
            configurable: true,
            value: function () {
                if (this.tagName === 'TEMPLATE') {
                    return { left: 0, top: 0, width: 0, height: 1, right: 0, bottom: 1, x: 0, y: 0, toJSON: () => ({}) };
                }
                return { left: 500, top: 300, width: 200, height: 100, right: 700, bottom: 400, x: 500, y: 300, toJSON: () => ({}) };
            },
        });

        document.body.innerHTML = `
            <template class="cms-plugin cms-plugin-77 cms-plugin-start"></template>
            <div class="cms-plugin cms-plugin-77">content</div>
            <template class="cms-plugin cms-plugin-77 cms-plugin-end"></template>
        `;
        highlightPluginContent(77, { successTimeout: 0 });
        const overlay = document.querySelector<HTMLElement>('.cms-plugin-overlay-77');
        expect(overlay).not.toBeNull();
        // Overlay should be anchored at (500, 300), not (0, 0).
        expect(overlay!.style.left).toBe('500px');
        expect(overlay!.style.top).toBe('300px');

        Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
            configurable: true,
            value: realRect,
        });
    });

    it('marks see-through and prominent classes when requested', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-7"></div>`;
        highlightPluginContent(7, {
            successTimeout: 0,
            seeThrough: true,
            prominent: true,
        });
        const overlay = document.querySelector('.cms-plugin-overlay-7');
        expect(overlay?.classList.contains('cms-plugin-overlay-see-through')).toBe(true);
        expect(overlay?.classList.contains('cms-plugin-overlay-prominent')).toBe(true);
    });
});

describe('highlight — removeHighlightPluginContent', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('removes overlays with successTimeout=0 only', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-overlay cms-plugin-overlay-1" data-success-timeout="0"></div>
            <div class="cms-plugin-overlay cms-plugin-overlay-1" data-success-timeout="200"></div>
        `;
        removeHighlightPluginContent(1);
        const overlays = document.querySelectorAll('.cms-plugin-overlay-1');
        expect(overlays.length).toBe(1);
        expect((overlays[0] as HTMLElement).dataset.successTimeout).toBe('200');
    });
});

describe('highlight — highlightPluginStructure', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
        document.body.innerHTML = '';
    });

    it('adds the success class + child overlay, removes after delay', () => {
        document.body.innerHTML = `<div id="dr" class="cms-draggable"></div>`;
        const el = document.getElementById('dr') as HTMLElement;
        highlightPluginStructure(el, { successTimeout: 100, delay: 200 });
        expect(el.classList.contains('cms-draggable-success')).toBe(true);
        expect(el.querySelector('.cms-dragitem-success')).not.toBeNull();
        vi.advanceTimersByTime(400);
        expect(el.querySelector('.cms-dragitem-success')).toBeNull();
        expect(el.classList.contains('cms-draggable-success')).toBe(false);
    });
});

describe('highlight — clickToHighlightHandler', () => {
    afterEach(() => {
        delete (window as { CMS?: unknown }).CMS;
    });

    it('is a no-op when not in structure mode', () => {
        const sb = { _showAndHighlightPlugin: vi.fn() };
        (window as unknown as { CMS: { settings: { mode: string }; API: { StructureBoard: typeof sb } } }).CMS = {
            settings: { mode: 'edit' },
            API: { StructureBoard: sb },
        };
        clickToHighlightHandler();
        expect(sb._showAndHighlightPlugin).not.toHaveBeenCalled();
    });

    it('asks structureboard to highlight when in structure mode', () => {
        const sb = { _showAndHighlightPlugin: vi.fn() };
        (window as unknown as { CMS: { settings: { mode: string }; API: { StructureBoard: typeof sb } } }).CMS = {
            settings: { mode: 'structure' },
            API: { StructureBoard: sb },
        };
        clickToHighlightHandler();
        expect(sb._showAndHighlightPlugin).toHaveBeenCalledWith(200, true);
    });
});

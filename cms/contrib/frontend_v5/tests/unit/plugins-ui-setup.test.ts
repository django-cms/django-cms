import { afterEach, describe, expect, it } from 'vitest';
import {
    extractContentWrappers,
    processTemplateGroup,
    setupContainer,
} from '../../frontend/modules/plugins/ui/setup';

describe('setupContainer — single match', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('returns the lone element when only one match exists', () => {
        document.body.innerHTML = `<div class="cms-plugin-1"><p>hi</p></div>`;
        const result = setupContainer('cms-plugin-1');
        expect(result).toHaveLength(1);
        expect(result[0]?.tagName).toBe('DIV');
    });

    it('returns a fresh <div> when nothing matches (clipboard fallback)', () => {
        const result = setupContainer('cms-plugin-missing');
        expect(result).toHaveLength(1);
        expect(result[0]?.tagName).toBe('DIV');
        // Not attached to the document.
        expect(result[0]?.parentNode).toBeNull();
    });

    it('placeholder containers without templates return all matches', () => {
        // Static placeholder rendered twice — no template wrapping.
        document.body.innerHTML = `
            <div class="cms-placeholder-3">a</div>
            <div class="cms-placeholder-3">b</div>
        `;
        const result = setupContainer('cms-placeholder-3');
        // The "multiple matches" branch only triggers for cms-plugin-*;
        // for placeholders, the single-or-many fallback returns all.
        expect(result).toHaveLength(2);
    });
});

describe('setupContainer — multi-render plugin (template-bracketed)', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('expands a single bracketed group, dropping the template tags', () => {
        document.body.innerHTML = `
            <template class="cms-plugin cms-plugin-4711 cms-plugin-start"></template>
            <p>Hello</p>
            <template class="cms-plugin cms-plugin-4711 cms-plugin-end"></template>
        `;
        const result = setupContainer('cms-plugin-4711');
        // <template> tags are gone, the <p> is wrapped/tagged.
        expect(result).toHaveLength(1);
        const el = result[0]!;
        expect(el.tagName).toBe('P');
        expect(el.classList.contains('cms-plugin')).toBe(true);
        expect(el.classList.contains('cms-plugin-4711')).toBe(true);
        expect(el.classList.contains('cms-plugin-start')).toBe(true);
        expect(el.classList.contains('cms-plugin-end')).toBe(true);
        expect(document.querySelectorAll('template').length).toBe(0);
    });

    it('handles multiple bracketed groups (header + footer renders)', () => {
        document.body.innerHTML = `
            <template class="cms-plugin cms-plugin-4711 cms-plugin-start"></template>
            <a>Header</a>
            <template class="cms-plugin cms-plugin-4711 cms-plugin-end"></template>
            <hr>
            <template class="cms-plugin cms-plugin-4711 cms-plugin-start"></template>
            <a>Footer</a>
            <template class="cms-plugin cms-plugin-4711 cms-plugin-end"></template>
        `;
        const result = setupContainer('cms-plugin-4711');
        expect(result).toHaveLength(2);
        expect(result[0]!.textContent?.trim()).toBe('Header');
        expect(result[1]!.textContent?.trim()).toBe('Footer');
        expect(document.querySelectorAll('template').length).toBe(0);
    });

    it('wraps stray text nodes in <cms-plugin> elements', () => {
        document.body.innerHTML = `<div id="root"><template class="cms-plugin cms-plugin-9 cms-plugin-start"></template>raw text<template class="cms-plugin cms-plugin-9 cms-plugin-end"></template></div>`;
        const result = setupContainer('cms-plugin-9');
        expect(result).toHaveLength(1);
        expect(result[0]!.tagName).toBe('CMS-PLUGIN');
        expect(result[0]!.textContent).toBe('raw text');
        expect(result[0]!.classList.contains('cms-plugin-text-node')).toBe(true);
    });

    it('skips pure whitespace and comments', () => {
        document.body.innerHTML = `<div id="root"><template class="cms-plugin cms-plugin-9 cms-plugin-start"></template>   <!-- comment -->\n<p>real</p><template class="cms-plugin cms-plugin-9 cms-plugin-end"></template></div>`;
        const result = setupContainer('cms-plugin-9');
        expect(result).toHaveLength(1);
        expect(result[0]!.tagName).toBe('P');
        expect(result[0]!.textContent).toBe('real');
    });

    it('falls back to all matches when wrappers are not <template>', () => {
        // Multiple cms-plugin-* matches but no <template> markers —
        // legacy renders this for some inline static content.
        document.body.innerHTML = `
            <span class="cms-plugin cms-plugin-2">A</span>
            <span class="cms-plugin cms-plugin-2">B</span>
        `;
        const result = setupContainer('cms-plugin-2');
        expect(result).toHaveLength(2);
        expect(result.every((el) => el.tagName === 'SPAN')).toBe(true);
    });
});

describe('extractContentWrappers', () => {
    it('groups a flat list at every cms-plugin-start', () => {
        const a = document.createElement('div');
        a.classList.add('cms-plugin-start');
        const b = document.createElement('div');
        const c = document.createElement('div');
        c.classList.add('cms-plugin-start');
        const d = document.createElement('div');
        const result = extractContentWrappers([a, b, c, d]);
        expect(result).toEqual([[a, b], [c, d]]);
    });

    it('treats the first element as a group start even without the class', () => {
        const a = document.createElement('div');
        const b = document.createElement('div');
        const result = extractContentWrappers([a, b]);
        expect(result).toEqual([[a, b]]);
    });

    it('returns an empty array for empty input', () => {
        expect(extractContentWrappers([])).toEqual([]);
    });
});

describe('processTemplateGroup', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('returns [] when the first item is not a <template>', () => {
        const div = document.createElement('div');
        document.body.appendChild(div);
        expect(processTemplateGroup([div], 'cms-plugin-1')).toEqual([]);
    });

    it('preserves shared classes from the start <template>', () => {
        document.body.innerHTML = `<div id="root"><template class="cms-plugin cms-plugin-9 cms-plugin-start cms-special"></template><p>A</p><p>B</p><template class="cms-plugin cms-plugin-9 cms-plugin-end"></template></div>`;
        const root = document.getElementById('root')!;
        const start = root.querySelector('template')!;
        const result = processTemplateGroup([start], 'cms-plugin-9');
        expect(result).toHaveLength(2);
        // Every survivor gets the shared classes (start removed).
        expect(result[0]!.classList.contains('cms-plugin')).toBe(true);
        expect(result[0]!.classList.contains('cms-plugin-9')).toBe(true);
        expect(result[0]!.classList.contains('cms-special')).toBe(true);
        // First gets cms-plugin-start, last gets cms-plugin-end.
        expect(result[0]!.classList.contains('cms-plugin-start')).toBe(true);
        expect(result[1]!.classList.contains('cms-plugin-end')).toBe(true);
    });
});

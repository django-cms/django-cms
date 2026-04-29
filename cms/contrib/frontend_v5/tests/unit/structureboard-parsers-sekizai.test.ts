import { describe, expect, it } from 'vitest';
import { planSekizaiUpdate } from '../../frontend/modules/structureboard/parsers/sekizai';

describe('parsers/sekizai — planSekizaiUpdate', () => {
    it('returns empty plan for missing/empty chunk', () => {
        expect(planSekizaiUpdate('css', undefined, [])).toEqual({
            toInsert: [],
            scriptCount: 0,
        });
        expect(planSekizaiUpdate('css', '', [])).toEqual({
            toInsert: [],
            scriptCount: 0,
        });
    });

    it('plans insertion of new <link> tags (css block)', () => {
        const chunk = `
            <link rel="stylesheet" href="/static/cms/a.css">
            <link rel="stylesheet" href="/static/cms/b.css">
        `;
        const plan = planSekizaiUpdate('css', chunk, []);
        expect(plan.toInsert).toHaveLength(2);
        expect(plan.scriptCount).toBe(0);
        expect((plan.toInsert[0] as HTMLLinkElement).getAttribute('href')).toBe(
            '/static/cms/a.css',
        );
    });

    it('skips elements already present', () => {
        const existing = document.createElement('link');
        existing.setAttribute('rel', 'stylesheet');
        existing.setAttribute('href', '/static/cms/a.css');
        const chunk = `
            <link rel="stylesheet" href="/static/cms/a.css">
            <link rel="stylesheet" href="/static/cms/b.css">
        `;
        const plan = planSekizaiUpdate('css', chunk, [existing]);
        expect(plan.toInsert).toHaveLength(1);
        expect((plan.toInsert[0] as HTMLLinkElement).getAttribute('href')).toBe(
            '/static/cms/b.css',
        );
    });

    it('counts <script> tags in the js block', () => {
        const chunk = `
            <script src="/static/a.js"></script>
            <script src="/static/b.js"></script>
        `;
        const plan = planSekizaiUpdate('js', chunk, []);
        expect(plan.toInsert).toHaveLength(2);
        expect(plan.scriptCount).toBe(2);
    });

    it('does not execute scripts during parse (uses inert template)', () => {
        // If the parser executed scripts, this global would be set.
        const chunk = `<script>(window as any).__sekizaiTest = true</script>`;
        delete (window as { __sekizaiTest?: boolean }).__sekizaiTest;
        planSekizaiUpdate('js', chunk, []);
        expect((window as { __sekizaiTest?: boolean }).__sekizaiTest).toBeUndefined();
    });

    it('css selector includes <style> and <meta>', () => {
        const chunk = `
            <style>body { color: red; }</style>
            <meta name="generator" content="cms">
        `;
        const plan = planSekizaiUpdate('css', chunk, []);
        // 1 style + 1 meta
        expect(plan.toInsert).toHaveLength(2);
    });
});

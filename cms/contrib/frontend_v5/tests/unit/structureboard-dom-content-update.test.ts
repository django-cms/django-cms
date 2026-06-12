import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    applyContentBridge,
    applySingleContent,
    applySekizai,
    findNextElement,
} from '../../frontend/modules/structureboard/dom/content-update';
import {
    _resetForTest as _resetBodySwapForTest,
    getPendingScriptCount,
} from '../../frontend/modules/structureboard/dom/body-swap';
import type { PluginInstance, PluginOptions } from '../../frontend/modules/plugins/types';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    _instances?: PluginInstance[];
    _plugins?: Array<[string, PluginOptions]>;
}

function setupCms(): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {},
        settings: {},
        _instances: [],
        _plugins: [],
    };
}

function getCms(): CmsTestable {
    return (window as unknown as { CMS: CmsTestable }).CMS;
}

beforeEach(() => {
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    setupCms();
    _resetBodySwapForTest();
});

afterEach(() => {
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetBodySwapForTest();
});

// ────────────────────────────────────────────────────────────────────
// applySingleContent
// ────────────────────────────────────────────────────────────────────

describe('content-update — applySingleContent', () => {
    it('returns true (refresh needed) when pluginIds is empty', () => {
        expect(applySingleContent({ html: '<div>x</div>' })).toBe(true);
    });

    it('returns true when html is undefined', () => {
        expect(applySingleContent({ pluginIds: [7] })).toBe(true);
    });

    it('inserts new HTML before the start marker and removes old non-template plugin nodes', () => {
        // Real CMS markup wraps content in <template> markers; the
        // legacy `:not(template)` predicate skips those. To exercise
        // the removal branch, the OLD content here is a plain div
        // carrying `.cms-plugin-7`, and the NEW HTML uses template
        // markers (server-rendered shape) so it survives.
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7 cms-plugin-start" id="anchor">old start</div>
            <div class="cms-plugin cms-plugin-7" id="continuation">old continuation</div>
            <script data-cms-plugin id="cms-plugin-7" type="application/json">{}</script>
        `;
        const result = applySingleContent({
            pluginIds: [7],
            html:
                '<template class="cms-plugin cms-plugin-7 cms-plugin-start"></template>' +
                '<div id="newContent">new</div>' +
                '<template class="cms-plugin cms-plugin-7 cms-plugin-end"></template>',
        });
        expect(result).toBe(false);
        // Old plain-div nodes removed
        expect(document.getElementById('anchor')).toBeNull();
        expect(document.getElementById('continuation')).toBeNull();
        // New (template-wrapped) content survived
        expect(document.getElementById('newContent')).not.toBeNull();
        // Script blob removed too
        expect(document.querySelector('script#cms-plugin-7')).toBeNull();
    });

    it('skips .cms-plugin nodes inside <template> (legacy :not(template))', () => {
        document.body.innerHTML = `
            <template>
                <div class="cms-plugin cms-plugin-7 cms-plugin-start" id="inTpl">do not touch</div>
            </template>
            <div class="cms-plugin cms-plugin-7 cms-plugin-start" id="real">old</div>
        `;
        applySingleContent({
            pluginIds: [7],
            html: '<div class="cms-plugin cms-plugin-7 cms-plugin-start" id="new">new</div>',
        });
        // Template descendant preserved
        expect(
            document.querySelector('template')!.content.querySelector('#inTpl'),
        ).not.toBeNull();
    });

    it('falls back to findNextElement when no start marker exists', () => {
        document.body.innerHTML = `
            <div class="cms-placeholder cms-placeholder-1" id="ph"></div>
        `;
        const result = applySingleContent({
            pluginIds: [7],
            // Use template markers so the new HTML survives the
            // post-insert :not(template) removal pass.
            html:
                '<template class="cms-plugin cms-plugin-7 cms-plugin-start"></template>' +
                '<div id="newContent">new</div>' +
                '<template class="cms-plugin cms-plugin-7 cms-plugin-end"></template>',
            position: 1,
            placeholder_id: 1,
        });
        expect(result).toBe(false);
        // New content inserted before placeholder.
        expect(document.getElementById('newContent')).not.toBeNull();
        // Placeholder still present, after the new content.
        const ph = document.getElementById('ph')!;
        expect(ph).not.toBeNull();
    });

    it('returns true when nothing can be anchored', () => {
        document.body.innerHTML = '';
        expect(
            applySingleContent({
                pluginIds: [7],
                html: '<div></div>',
                position: 1,
                placeholder_id: 99,
            }),
        ).toBe(true);
    });

    it('forces position lookup when insert: true even with existing marker', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7 cms-plugin-start" id="existing">existing</div>
            <div class="cms-placeholder cms-placeholder-1" id="ph"></div>
        `;
        applySingleContent({
            pluginIds: [7],
            html: '<div class="cms-plugin cms-plugin-7 cms-plugin-start">via insert</div>',
            insert: true,
            position: 1,
            placeholder_id: 1,
        });
        // Existing marker should still be removed; new HTML placed before placeholder
        expect(document.getElementById('existing')).toBeNull();
    });
});

// ────────────────────────────────────────────────────────────────────
// findNextElement
// ────────────────────────────────────────────────────────────────────

describe('content-update — findNextElement', () => {
    it('finds the next plugin marker by position within the placeholder', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-8 cms-plugin-start"></div>
            <div class="cms-placeholder cms-placeholder-1"></div>
        `;
        const cms = getCms();
        cms._instances!.push(
            {
                options: {
                    type: 'plugin',
                    plugin_id: 7,
                    placeholder_id: 1,
                    position: 1,
                } as PluginOptions,
            },
            {
                options: {
                    type: 'plugin',
                    plugin_id: 8,
                    placeholder_id: 1,
                    position: 2,
                } as PluginOptions,
            },
        );
        const next = findNextElement(2, 1, [7]);
        expect(next).not.toBeNull();
        expect((next as Element).classList.contains('cms-plugin-8')).toBe(true);
    });

    it('falls back to the placeholder element when no later plugin matches', () => {
        document.body.innerHTML = `
            <div class="cms-placeholder cms-placeholder-1" id="ph"></div>
        `;
        const next = findNextElement(1, 1, []);
        expect(next).not.toBeNull();
        expect((next as Element).id).toBe('ph');
    });

    it('excludes plugin ids in the excluded list', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-8 cms-plugin-start" id="m8"></div>
            <div class="cms-placeholder cms-placeholder-1" id="ph"></div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: {
                type: 'plugin',
                plugin_id: 8,
                placeholder_id: 1,
                position: 5,
            } as PluginOptions,
        });
        // Excluding plugin 8 → fall back to placeholder
        const next = findNextElement(5, 1, [8]);
        expect((next as Element).id).toBe('ph');
    });
});

// ────────────────────────────────────────────────────────────────────
// applyContentBridge
// ────────────────────────────────────────────────────────────────────

describe('content-update — applyContentBridge', () => {
    it('returns true when data is null/undefined/empty', () => {
        expect(applyContentBridge(undefined)).toBe(true);
        expect(applyContentBridge(null)).toBe(true);
        expect(applyContentBridge({})).toBe(true);
        expect(applyContentBridge({ content: [] })).toBe(true);
    });

    it('returns true when source_placeholder_id has no plugins left', () => {
        // No instances in placeholder 5 → bridge bails to full refresh
        expect(
            applyContentBridge({
                source_placeholder_id: 5,
                content: [
                    {
                        pluginIds: [7],
                        html: '<div></div>',
                    },
                ],
            }),
        ).toBe(true);
    });

    it('returns false when content can be applied successfully', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7 cms-plugin-start" id="anchor">old</div>
        `;
        const result = applyContentBridge({
            content: [
                {
                    pluginIds: [7],
                    html: '<div class="cms-plugin cms-plugin-7 cms-plugin-start">new</div>',
                },
            ],
        });
        expect(result).toBe(false);
    });

    it('returns true if any single content entry can\'t be applied', () => {
        const result = applyContentBridge({
            content: [
                {
                    pluginIds: [7],
                    html: '<div></div>',
                    position: 1,
                    placeholder_id: 999, // not present
                },
            ],
        });
        expect(result).toBe(true);
    });
});

// ────────────────────────────────────────────────────────────────────
// applySekizai
// ────────────────────────────────────────────────────────────────────

describe('content-update — applySekizai', () => {
    it('appends new <link> tags into <head> for the css block', () => {
        document.head.innerHTML = '<link rel="stylesheet" href="/a.css">';
        applySekizai(
            'css',
            '<link rel="stylesheet" href="/a.css"><link rel="stylesheet" href="/b.css">',
        );
        const links = document.head.querySelectorAll('link');
        expect(links.length).toBe(2);
        // /a.css already present → not re-added
        expect((links[1] as HTMLLinkElement).href).toContain('b.css');
    });

    it('re-clones <script src> tags so the browser re-executes them', () => {
        document.body.innerHTML = '';
        applySekizai('js', '<script src="/new.js"></script>');
        const scripts = document.body.querySelectorAll('script');
        expect(scripts.length).toBe(1);
        // src= scripts increment the body-swap refcount
        expect(getPendingScriptCount()).toBe(1);
    });

    it('inserts inline <script> blocks without incrementing refcount', () => {
        document.body.innerHTML = '';
        applySekizai('js', '<script>console.log("inline")</script>');
        expect(document.body.querySelectorAll('script').length).toBe(1);
        expect(getPendingScriptCount()).toBe(0);
    });

    it('skips already-present elements (legacy elementPresent)', () => {
        document.body.innerHTML = '<script src="/keep.js"></script>';
        applySekizai('js', '<script src="/keep.js"></script>');
        // Same src → considered present → not re-added
        expect(document.body.querySelectorAll('script').length).toBe(1);
        expect(getPendingScriptCount()).toBe(0);
    });
});

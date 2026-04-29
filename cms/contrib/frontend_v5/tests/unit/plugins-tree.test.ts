import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    initializeTree,
    refreshPlugins,
    updateRegistry,
} from '../../frontend/modules/plugins/tree';
import {
    _resetRegistryForTest,
    getAllDescriptors,
} from '../../frontend/modules/plugins/registry';
import { _resetGlobalHandlersForTest } from '../../frontend/modules/plugins/ui/global-handlers';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
}

function setupCms(): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: { request: { language: 'en' } },
        settings: {},
        _instances: [],
        _plugins: [],
    };
}

function script(id: string, attr: string, payload: object): string {
    return `<script type="application/json" id="${id}" data-cms-${attr}>${JSON.stringify(payload)}</script>`;
}

describe('tree — initializeTree', () => {
    beforeEach(() => {
        setupCms();
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('scans data-cms-{plugin,placeholder,general} scripts', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-placeholder cms-placeholder-7"></div>
            <div class="cms-render-model cms-plugin-cms-page-name-2"></div>
            ${script('cms-plugin-1', 'plugin', {
                type: 'plugin',
                plugin_id: 1,
                placeholder_id: 7,
                plugin_type: 'TextPlugin',
            })}
            ${script('cms-placeholder-7', 'placeholder', {
                type: 'placeholder',
                placeholder_id: 7,
            })}
            ${script('cms-plugin-cms-page-name-2', 'general', {
                type: 'generic',
                plugin_id: 'cms-page-name-2',
            })}
        `;
        const instances = initializeTree();
        expect(instances.length).toBe(3);
        expect(getAllDescriptors().length).toBe(3);
        const types = instances.map((i) => i.options.type).sort();
        expect(types).toEqual(['generic', 'placeholder', 'plugin']);
    });

    it('skips malformed JSON descriptors without crashing', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-9"></div>
            <script type="application/json" id="cms-plugin-9" data-cms-plugin>not-json</script>
        `;
        expect(() => initializeTree()).not.toThrow();
    });
});

describe('tree — refreshPlugins', () => {
    beforeEach(() => {
        setupCms();
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('appends newly-rendered generic descriptors', () => {
        document.body.innerHTML = `
            ${script('cms-plugin-1', 'plugin', {
                type: 'plugin',
                plugin_id: 1,
                placeholder_id: 7,
            })}
        `;
        initializeTree();
        // Then a generic appears (e.g. front-end editable field added).
        document.body.insertAdjacentHTML(
            'beforeend',
            `<div class="cms-plugin cms-plugin-cms-page-99"></div>` +
                script('cms-plugin-cms-page-99', 'general', {
                    type: 'generic',
                    plugin_id: 'cms-page-99',
                }),
        );
        refreshPlugins();
        expect(getAllDescriptors().some(([k]) => k === 'cms-plugin-cms-page-99')).toBe(true);
    });

    it('does not duplicate generics on repeated calls', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-cms-page-1"></div>
            ${script('cms-plugin-cms-page-1', 'general', {
                type: 'generic',
                plugin_id: 'cms-page-1',
            })}
        `;
        initializeTree();
        refreshPlugins();
        refreshPlugins();
        const generics = getAllDescriptors().filter(
            ([, o]) => o.type === 'generic',
        );
        expect(generics.length).toBe(1);
    });
});

describe('tree — updateRegistry', () => {
    beforeEach(() => {
        setupCms();
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        _resetRegistryForTest();
        _resetGlobalHandlersForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('appends a new plugin when its id is unseen', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-42"></div>`;
        updateRegistry([
            {
                type: 'plugin',
                plugin_id: 42,
                placeholder_id: 7,
                plugin_type: 'PicturePlugin',
            },
        ]);
        expect(getAllDescriptors().length).toBe(1);
        expect(getAllDescriptors()[0]?.[0]).toBe('cms-plugin-42');
    });

    it('replaces an existing plugin descriptor', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-42"></div>`;
        updateRegistry([
            {
                type: 'plugin',
                plugin_id: 42,
                placeholder_id: 7,
                plugin_name: 'Old',
            },
        ]);
        updateRegistry([
            {
                type: 'plugin',
                plugin_id: 42,
                placeholder_id: 7,
                plugin_name: 'New',
            },
        ]);
        expect(getAllDescriptors().length).toBe(1);
        expect(getAllDescriptors()[0]?.[1]?.plugin_name).toBe('New');
    });
});

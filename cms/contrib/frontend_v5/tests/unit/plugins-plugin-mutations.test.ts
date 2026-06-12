import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Plugin, _registerForTest } from '../../frontend/modules/plugins/plugin';
import {
    _resetRegistryForTest,
    setDescriptors,
} from '../../frontend/modules/plugins/registry';
import * as request from '../../frontend/modules/request';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    API?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
    Modal?: unknown;
}

function setupCms(extras: Record<string, unknown> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            csrf: 'test-csrf',
            request: { language: 'en' },
            clipboard: { id: 99 },
            lang: { success: 'OK', error: 'Err: ' },
            ...((extras.config as Record<string, unknown>) ?? {}),
        },
        settings: { mode: 'edit' },
        API: { locked: false, ...((extras.API as Record<string, unknown>) ?? {}) },
        _instances: [],
        _plugins: [],
        ...extras,
    };
}

function plugin(opts: Partial<ConstructorParameters<typeof Plugin>[1]> = {}): Plugin {
    document.body.innerHTML = `<div class="cms-plugin cms-plugin-1"></div>`;
    const inst = new Plugin('cms-plugin-1', {
        type: 'plugin',
        plugin_id: 1,
        placeholder_id: 7,
        plugin_type: 'TextPlugin',
        plugin_name: 'Text',
        urls: {
            edit_plugin: '/edit/1/',
            delete_plugin: '/delete/1/',
            copy_plugin: '/copy/',
            move_plugin: '/move/',
            add_plugin: '/add/',
        },
        position: 1,
        ...opts,
    });
    _registerForTest(inst);
    return inst;
}

describe('Plugin.copyPlugin', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('POSTs to copy_plugin with the right payload', async () => {
        const post = vi.spyOn(request, 'post').mockResolvedValue({});
        const p = plugin();
        await p.copyPlugin();
        expect(post).toHaveBeenCalledOnce();
        const [url, body] = post.mock.calls[0]!;
        expect(url).toContain('/copy/');
        const params = new URLSearchParams(body as URLSearchParams);
        expect(params.get('source_placeholder_id')).toBe('7');
        expect(params.get('source_plugin_id')).toBe('1');
        expect(params.get('target_placeholder_id')).toBe('99'); // clipboard
    });

    it('skips when CMS.API.locked is already set', async () => {
        const post = vi.spyOn(request, 'post').mockResolvedValue({});
        setupCms({ API: { locked: true } });
        const p = plugin();
        await p.copyPlugin();
        expect(post).not.toHaveBeenCalled();
    });

    it('with sourceLanguage flips to PASTE invalidate', async () => {
        vi.spyOn(request, 'post').mockResolvedValue({ ok: true });
        const invalidate = vi.fn();
        setupCms({ API: { StructureBoard: { invalidateState: invalidate } } });
        const p = plugin();
        await p.copyPlugin(undefined, 'de');
        expect(invalidate).toHaveBeenCalledOnce();
        expect(invalidate.mock.calls[0]?.[0]).toBe('PASTE');
    });
});

describe('Plugin.cutPlugin', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('POSTs cut payload + dispatches CUT', async () => {
        const post = vi.spyOn(request, 'post').mockResolvedValue({});
        const invalidate = vi.fn();
        setupCms({ API: { StructureBoard: { invalidateState: invalidate } } });
        const p = plugin();
        await p.cutPlugin();
        const [url, body] = post.mock.calls[0]!;
        expect(url).toContain('/move/');
        const params = new URLSearchParams(body as URLSearchParams);
        expect(params.get('placeholder_id')).toBe('99');
        expect(params.get('plugin_id')).toBe('1');
        expect(invalidate).toHaveBeenCalledWith('CUT', expect.any(Object));
    });
});

describe('Plugin.movePlugin', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
        vi.restoreAllMocks();
    });

    it('reads placeholder/parent from the live DOM', async () => {
        const post = vi.spyOn(request, 'post').mockResolvedValue({});
        const invalidate = vi.fn();
        setupCms({ API: { StructureBoard: { invalidateState: invalidate } } });
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-dragarea cms-dragarea-12">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-1"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const p = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            placeholder_id: 7,
            position: 5,
            urls: { move_plugin: '/move/' },
        });
        _registerForTest(p);
        await p.movePlugin();
        const params = new URLSearchParams(post.mock.calls[0]?.[1] as URLSearchParams);
        expect(params.get('plugin_id')).toBe('1');
        expect(params.get('plugin_parent')).toBe('99');
        // Cross-placeholder move ⇒ placeholder_id present.
        expect(params.get('placeholder_id')).toBe('12');
        // updatePluginPositions has rewritten options.position from the
        // live DOM order: dragarea-12 → [99 (root), 1 (nested)] → 1 is 2nd.
        expect(params.get('target_position')).toBe('2');
        expect(invalidate).toHaveBeenCalledWith('MOVE', expect.any(Object));
    });
});

describe('Plugin.addPlugin', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('opens a modal with the right add URL when CMS.Modal exists', () => {
        const opens: Array<{ url?: string }> = [];
        class FakeModal {
            open(opts: { url?: string }) {
                opens.push(opts);
            }
        }
        setupCms();
        (window as unknown as { CMS: CmsTestable }).CMS.Modal = FakeModal;
        const p = plugin();
        p.addPlugin('TextPlugin', 'Text', undefined, true);
        expect(opens.length).toBe(1);
        expect(opens[0]?.url).toContain('/add/');
        expect(opens[0]?.url).toContain('placeholder_id=7');
        expect(opens[0]?.url).toContain('plugin_type=TextPlugin');
    });

    it('is a no-op when CMS.Modal is missing', () => {
        const p = plugin();
        expect(() => p.addPlugin('TextPlugin', 'Text')).not.toThrow();
    });
});

describe('Plugin._getPluginAddPosition', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('placeholder: returns count + 1', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-7">
                <div class="cms-draggable cms-draggable-1"></div>
                <div class="cms-draggable cms-draggable-2"></div>
            </div>
        `;
        const p = new Plugin('cms-plugin-x', {
            type: 'placeholder',
            placeholder_id: 7,
        });
        _registerForTest(p);
        expect(p._getPluginAddPosition()).toBe(3);
    });

    it('plugin without children: position + 1', () => {
        const p = plugin({ position: 5 });
        expect(p._getPluginAddPosition()).toBe(6);
    });
});

describe('Plugin._getPluginBreadcrumbs', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('walks up via plugin_parent', () => {
        setDescriptors([
            ['cms-plugin-10', {
                type: 'plugin',
                plugin_id: 10,
                plugin_name: 'Outer',
                plugin_parent: null,
                urls: { edit_plugin: '/edit/10/' },
            }],
            ['cms-plugin-11', {
                type: 'plugin',
                plugin_id: 11,
                plugin_name: 'Middle',
                plugin_parent: 10,
                urls: { edit_plugin: '/edit/11/' },
            }],
        ]);
        const p = plugin({ plugin_parent: 11 });
        const crumbs = p._getPluginBreadcrumbs();
        expect(crumbs.map((c) => c.title)).toEqual(['Outer', 'Middle', 'Text']);
    });
});

describe('Plugin._setSettings', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('merges new options + writes to instance', () => {
        const p = plugin();
        p._setSettings(p.options, { plugin_name: 'Renamed' });
        expect(p.options.plugin_name).toBe('Renamed');
        expect(p.options.plugin_id).toBe(1);
    });
});

describe('Plugin._checkIfPasteAllowed', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('returns false when no clipboard draggable exists', () => {
        const p = plugin();
        // Append the dropdown after construction so the plugin()
        // helper's innerHTML reset doesn't wipe it.
        const dd = document.createElement('div');
        dd.id = 'dd';
        dd.className = 'cms-submenu-dropdown';
        dd.innerHTML = `
            <div class="cms-submenu-item">
                <a data-rel="paste"></a>
                <span class="cms-submenu-item-paste-tooltip-empty"></span>
            </div>
        `;
        document.body.appendChild(dd);
        p.ui.dropdown = dd;
        expect(p._checkIfPasteAllowed()).toBe(false);
        const item = dd.querySelector('.cms-submenu-item') as HTMLElement;
        expect(item.classList.contains('cms-submenu-item-disabled')).toBe(true);
    });
});

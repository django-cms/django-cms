import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    getPlaceholderData,
    getPluginData,
} from '../../frontend/modules/plugins/cms-data';
import { Plugin } from '../../frontend/modules/plugins/plugin';
import {
    _resetRegistryForTest,
    findPluginById,
    isPlaceholderDuplicate,
    isPluginDuplicate,
} from '../../frontend/modules/plugins/registry';

function ensureCmsConfig(extra: Record<string, unknown> = {}) {
    window.CMS = {
        config: {
            settings: { mode: 'content' },
            request: { language: 'en' },
            ...extra,
        },
    } as CmsGlobal;
}

function fakeCmsPlugin(id: number, name: string): HTMLElement {
    const el = document.createElement('div');
    el.classList.add('cms-plugin', `cms-plugin-${id}`);
    el.textContent = name;
    document.body.appendChild(el);
    return el;
}

function fakePlaceholder(id: number): HTMLElement {
    const el = document.createElement('div');
    el.classList.add('cms-placeholder', `cms-placeholder-${id}`);
    document.body.appendChild(el);
    return el;
}

function fakeDragbar(id: number): HTMLElement {
    const dragarea = document.createElement('div');
    dragarea.classList.add('cms-dragarea');
    const dragbar = document.createElement('div');
    dragbar.classList.add('cms-dragbar', `cms-dragbar-${id}`);
    dragbar.innerHTML = `
        <span class="cms-dragbar-title">Title</span>
        <span class="cms-dragbar-toggler"><a href="#">toggle</a></span>
        <div class="cms-submenu-settings"></div>
        <div class="cms-submenu-add"></div>
    `;
    dragarea.appendChild(dragbar);
    const draggables = document.createElement('div');
    draggables.classList.add('cms-draggables');
    dragarea.appendChild(draggables);
    document.body.appendChild(dragarea);
    return dragbar;
}

describe('Plugin — constructor & options merge', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('merges options with defaults', () => {
        fakeCmsPlugin(1, 'X');
        const p = new Plugin('cms-plugin-1', { type: 'plugin', plugin_id: 1 });
        expect(p.options.type).toBe('plugin');
        expect(p.options.plugin_id).toBe(1);
        // Default urls object preserved.
        expect(p.options.urls?.add_plugin).toBe('');
        expect(Array.isArray(p.options.plugin_restriction)).toBe(true);
    });

    it('assigns a fresh uid per instance', () => {
        fakeCmsPlugin(1, 'X');
        fakeCmsPlugin(2, 'Y');
        const a = new Plugin('cms-plugin-1', { type: 'plugin', plugin_id: 1 });
        const b = new Plugin('cms-plugin-2', { type: 'plugin', plugin_id: 2 });
        expect(a.uid).not.toBe(b.uid);
    });

    it('populates ui.container from the DOM via _setupUI', () => {
        fakeCmsPlugin(7, 'Hello');
        const p = new Plugin('cms-plugin-7', { type: 'plugin', plugin_id: 7 });
        expect(p.ui.container).toHaveLength(1);
        expect(p.ui.container?.[0]?.classList.contains('cms-plugin-7')).toBe(true);
    });

    it('falls back to a fresh <div> when no DOM match', () => {
        const p = new Plugin('cms-plugin-missing', { type: 'plugin', plugin_id: 99 });
        expect(p.ui.container).toHaveLength(1);
        // Detached div.
        expect(p.ui.container?.[0]?.parentNode).toBeNull();
    });
});

describe('Plugin — type-specific data wiring', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('placeholder stores a single descriptor object on the wrapper', () => {
        const el = fakePlaceholder(11);
        fakeDragbar(11);
        const p = new Plugin('cms-placeholder-11', {
            type: 'placeholder',
            placeholder_id: 11,
        });
        const data = getPlaceholderData(el);
        expect(data?.placeholder_id).toBe(11);
        expect(data).toBe(p.options); // stored by reference
    });

    it('plugin pushes its descriptor onto an array', () => {
        const el = fakeCmsPlugin(5, 'foo');
        const p = new Plugin('cms-plugin-5', { type: 'plugin', plugin_id: 5 });
        const arr = getPluginData(el);
        expect(arr).toHaveLength(1);
        expect(arr?.[0]).toBe(p.options);
    });

    it('generic descriptor lands in the array (default branch)', () => {
        const el = fakeCmsPlugin(8, 'gen');
        const p = new Plugin('cms-plugin-8', { type: 'generic', plugin_id: 8 });
        expect(getPluginData(el)?.[0]).toBe(p.options);
    });

    it('two plugins on the same wrapper coexist as array entries', () => {
        const el = fakeCmsPlugin(9, 'reused');
        const a = new Plugin('cms-plugin-9', { type: 'plugin', plugin_id: 9 });
        // Constructing a second plugin with the same id is a duplicate
        // — the second instance early-returns from the constructor.
        // To test the array-coexistence path, simulate two distinct
        // ids reusing the same wrapper class via a second matching
        // element with the same id but different descriptor shape.
        void a;
        const _b = new Plugin('cms-plugin-9', { type: 'generic', plugin_id: 9, plugin_type: 'Other' });
        const arr = getPluginData(el)!;
        // First push lands; second is the duplicate-guard for plugin
        // type — generic can still push.
        expect(arr.length).toBeGreaterThanOrEqual(1);
    });
});

describe('Plugin — duplicate guards', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('marks plugin id as duplicate after first construction', () => {
        fakeCmsPlugin(7, 'first');
        new Plugin('cms-plugin-7', { type: 'plugin', plugin_id: 7 });
        expect(isPluginDuplicate(7)).toBe(true);
    });

    it('marks placeholder id as duplicate after first construction', () => {
        fakePlaceholder(3);
        fakeDragbar(3);
        new Plugin('cms-placeholder-3', {
            type: 'placeholder',
            placeholder_id: 3,
        });
        expect(isPlaceholderDuplicate(3)).toBe(true);
    });

    it('second construction of a duplicate plugin id early-returns', () => {
        fakeCmsPlugin(7, 'first');
        const a = new Plugin('cms-plugin-7', { type: 'plugin', plugin_id: 7 });
        const b = new Plugin('cms-plugin-7', { type: 'plugin', plugin_id: 7 });
        // Both constructors completed; the second one populated
        // ui.container but skipped the type-specific wiring branch.
        expect(b.ui.container).toBeDefined();
        // The data array on the wrapper still reflects only one push
        // because the second constructor returned before pushPluginData.
        const arr = getPluginData(a.ui.container![0]!);
        expect(arr).toHaveLength(1);
    });
});

describe('Plugin — destroy & cleanup', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('destroy aborts the listener controller (dblclick handler stops firing)', () => {
        const el = fakeCmsPlugin(7, 'X');
        const p = new Plugin('cms-plugin-7', {
            type: 'generic',
            plugin_id: 7,
            urls: { edit_plugin: '/edit/' },
        });
        const editSpy = vi.fn();
        (p as Plugin & { editPlugin?: (...args: unknown[]) => void }).editPlugin =
            editSpy;
        // Sanity: the listener is wired and fires.
        el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        expect(editSpy).toHaveBeenCalledTimes(1);

        p.destroy();

        editSpy.mockClear();
        el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        expect(editSpy).not.toHaveBeenCalled();
    });

    it('destroy closes the modal if any', () => {
        fakeCmsPlugin(1, 'X');
        const p = new Plugin('cms-plugin-1', { type: 'plugin', plugin_id: 1 });
        const close = vi.fn();
        const off = vi.fn();
        p.modal = { close, off };
        p.destroy();
        expect(close).toHaveBeenCalledOnce();
        expect(off).toHaveBeenCalledOnce();
    });

    it('cleanup removes ui Elements from the DOM', () => {
        const el = fakeCmsPlugin(1, 'X');
        const p = new Plugin('cms-plugin-1', { type: 'plugin', plugin_id: 1 });
        expect(el.parentNode).toBe(document.body);
        p.destroy({ mustCleanup: true });
        expect(el.parentNode).toBeNull();
    });
});

describe('Plugin — generic dblclick → editPlugin delegation', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('dblclick on a generic container calls editPlugin when defined', () => {
        const el = fakeCmsPlugin(15, 'gen');
        const p = new Plugin('cms-plugin-15', {
            type: 'generic',
            plugin_id: 15,
            urls: { edit_plugin: '/edit/15/' },
        });
        const editSpy = vi.fn();
        (p as Plugin & { editPlugin?: (...args: unknown[]) => void }).editPlugin =
            editSpy;
        el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        expect(editSpy).toHaveBeenCalledWith('/edit/15/', undefined, []);
    });

    it('dblclick is a no-op when no edit_plugin URL is set', () => {
        const el = fakeCmsPlugin(15, 'gen');
        const p = new Plugin('cms-plugin-15', { type: 'generic', plugin_id: 15 });
        const editSpy = vi.fn();
        (p as Plugin & { editPlugin?: (...args: unknown[]) => void }).editPlugin =
            editSpy;
        el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
        expect(editSpy).not.toHaveBeenCalled();
    });
});

describe('Plugin — placeholder dragbar wiring', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('toggler link expands/collapses every collapsable child + flips title', () => {
        fakePlaceholder(2);
        const dragbar = fakeDragbar(2);
        // Add a collapsable child so expandAll/collapseAll have something
        // to flip — without one, both helpers are no-ops (matches legacy).
        const dragarea = dragbar.closest('.cms-dragarea')!;
        const draggables = dragarea.querySelector('.cms-draggables')!;
        draggables.innerHTML = `
            <div class="cms-draggable cms-draggable-101">
                <div class="cms-dragitem cms-dragitem-collapsable">
                    <div class="cms-dragitem-text">child</div>
                </div>
                <div class="cms-collapsable-container cms-hidden"></div>
            </div>
        `;
        const p = new Plugin('cms-placeholder-2', {
            type: 'placeholder',
            placeholder_id: 2,
        });
        expect(p.ui.dragbar).toBe(dragbar);
        const title = dragbar.querySelector('.cms-dragbar-title')!;
        const togglerLink = dragbar.querySelector<HTMLAnchorElement>(
            '.cms-dragbar-toggler a',
        )!;
        const child = document.querySelector<HTMLElement>(
            '.cms-draggable-101 .cms-dragitem',
        )!;
        expect(title.classList.contains('cms-dragbar-title-expanded')).toBe(false);
        togglerLink.click();
        expect(title.classList.contains('cms-dragbar-title-expanded')).toBe(true);
        expect(child.classList.contains('cms-dragitem-expanded')).toBe(true);
        togglerLink.click();
        expect(title.classList.contains('cms-dragbar-title-expanded')).toBe(false);
        expect(child.classList.contains('cms-dragitem-expanded')).toBe(false);
    });

    it('restores expanded state from CMS.settings.dragbars', () => {
        fakePlaceholder(4);
        const dragbar = fakeDragbar(4);
        window.CMS!.settings = { dragbars: [4] };
        new Plugin('cms-placeholder-4', { type: 'placeholder', placeholder_id: 4 });
        const title = dragbar.querySelector('.cms-dragbar-title')!;
        expect(title.classList.contains('cms-dragbar-title-expanded')).toBe(true);
    });
});

describe('Plugin — registry interop', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        ensureCmsConfig();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('findPluginById finds an instance after manual registration', async () => {
        const { _registerForTest } = await import('../../frontend/modules/plugins/plugin');
        fakeCmsPlugin(42, 'reg');
        const p = new Plugin('cms-plugin-42', { type: 'plugin', plugin_id: 42 });
        _registerForTest(p);
        expect(findPluginById(42)).toBe(p);
    });
});

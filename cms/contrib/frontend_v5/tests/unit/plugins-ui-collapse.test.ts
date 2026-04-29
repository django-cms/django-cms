import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    collapseAll,
    expandAll,
    setupCollapsable,
    toggleCollapsable,
    updatePlaceholderCollapseState,
} from '../../frontend/modules/plugins/ui/collapse';
import {
    setExpandMode,
    _resetGlobalHandlersForTest,
} from '../../frontend/modules/plugins/ui/global-handlers';
import { getCmsSettings } from '../../frontend/modules/plugins/cms-globals';
import type { PluginInstance } from '../../frontend/modules/plugins/types';

interface CmsTestable {
    settings?: Record<string, unknown>;
    _plugins?: Array<[string, Record<string, unknown>]>;
}

function makePlugin(overrides: Partial<PluginInstance['options']> = {}): PluginInstance {
    return {
        options: {
            type: 'plugin',
            plugin_id: 1,
            placeholder_id: 7,
            ...overrides,
        },
    };
}

/**
 * Build a single-plugin draggable fixture with a collapsable
 * `dragitem` and a `cms-collapsable-container`.
 */
function fixture(opts: { expanded?: boolean; nested?: boolean } = {}) {
    const expandedCls = opts.expanded ? ' cms-dragitem-expanded' : '';
    const containerHidden = opts.expanded ? '' : ' cms-hidden';
    const nested = opts.nested
        ? `
            <div class="cms-draggable cms-draggable-2">
                <div class="cms-dragitem cms-dragitem-collapsable cms-dragitem-expanded">
                    <div class="cms-dragitem-text">child</div>
                </div>
                <div class="cms-collapsable-container"></div>
            </div>
        `
        : '';
    document.body.innerHTML = `
        <div class="cms-dragarea cms-dragarea-7">
            <div class="cms-dragbar cms-dragbar-7">
                <span class="cms-dragbar-title">Title</span>
            </div>
            <div class="cms-draggables">
                <div class="cms-draggable cms-draggable-1">
                    <div class="cms-dragitem cms-dragitem-collapsable${expandedCls}">
                        <div class="cms-dragitem-text">click me</div>
                    </div>
                    <div class="cms-collapsable-container${containerHidden}">${nested}</div>
                </div>
            </div>
        </div>
    `;
    return {
        draggable: document.querySelector<HTMLElement>('.cms-draggable-1')!,
        dragitem: document.querySelector<HTMLElement>(
            '.cms-draggable-1 > .cms-dragitem',
        )!,
        text: document.querySelector<HTMLElement>(
            '.cms-draggable-1 > .cms-dragitem > .cms-dragitem-text',
        )!,
        container: document.querySelector<HTMLElement>(
            '.cms-draggable-1 > .cms-collapsable-container',
        )!,
        dragbarTitle: document.querySelector<HTMLElement>('.cms-dragbar-title')!,
    };
}

describe('collapse — setupCollapsable + click toggle', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsTestable }).CMS;
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsTestable }).CMS;
        _resetGlobalHandlersForTest();
    });

    it('clicking the dragitem text toggles expanded state', () => {
        const { dragitem, text, container } = fixture();
        const plugin = makePlugin();
        setupCollapsable(plugin);
        text.dispatchEvent(new Event('click', { bubbles: true }));
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(true);
        expect(container.classList.contains('cms-hidden')).toBe(false);

        text.dispatchEvent(new Event('click', { bubbles: true }));
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(false);
        expect(container.classList.contains('cms-hidden')).toBe(true);
    });

    it('writes plugin id into CMS.settings.states on expand', () => {
        const { text } = fixture();
        const plugin = makePlugin();
        setupCollapsable(plugin);
        text.dispatchEvent(new Event('click', { bubbles: true }));
        const settings = getCmsSettings();
        expect(settings.states).toContain(1);
    });

    it('does nothing on a non-collapsable dragitem', () => {
        const { dragitem, text } = fixture();
        dragitem.classList.remove('cms-dragitem-collapsable');
        const plugin = makePlugin();
        setupCollapsable(plugin);
        text.dispatchEvent(new Event('click', { bubbles: true }));
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(false);
    });

    it('aborts when the AbortSignal fires', () => {
        const { text, dragitem } = fixture();
        const ctrl = new AbortController();
        setupCollapsable(makePlugin(), ctrl.signal);
        ctrl.abort();
        text.dispatchEvent(new Event('click', { bubbles: true }));
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(false);
    });
});

describe('collapse — toggleCollapsable with shift held', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsTestable }).CMS;
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsTestable }).CMS;
        _resetGlobalHandlersForTest();
    });

    it('expanding with shift expands every nested collapsable too', () => {
        const { dragitem } = fixture({ nested: true });
        const nested = document.querySelector<HTMLElement>(
            '.cms-draggable-2 .cms-dragitem',
        )!;
        // Start with both collapsed.
        nested.classList.remove('cms-dragitem-expanded');
        setExpandMode(true);
        toggleCollapsable(makePlugin(), dragitem);
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(true);
        expect(nested.classList.contains('cms-dragitem-expanded')).toBe(true);
    });

    it('collapsing with shift collapses every nested expanded item too', () => {
        const { dragitem } = fixture({ expanded: true, nested: true });
        const nested = document.querySelector<HTMLElement>(
            '.cms-draggable-2 .cms-dragitem',
        )!;
        setExpandMode(true);
        toggleCollapsable(makePlugin(), dragitem);
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(false);
        expect(nested.classList.contains('cms-dragitem-expanded')).toBe(false);
    });
});

describe('collapse — expandAll / collapseAll', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsTestable }).CMS;
    });

    it('expandAll expands every collapsable in the dragarea + flips title', () => {
        const { dragitem, dragbarTitle } = fixture({ nested: true });
        const nested = document.querySelector<HTMLElement>(
            '.cms-draggable-2 .cms-dragitem',
        )!;
        nested.classList.remove('cms-dragitem-expanded');
        expandAll(makePlugin(), dragbarTitle);
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(true);
        expect(nested.classList.contains('cms-dragitem-expanded')).toBe(true);
        expect(dragbarTitle.classList.contains('cms-dragbar-title-expanded')).toBe(true);
    });

    it('collapseAll collapses every expanded item + clears title', () => {
        const { dragitem, dragbarTitle } = fixture({ expanded: true, nested: true });
        dragbarTitle.classList.add('cms-dragbar-title-expanded');
        collapseAll(makePlugin(), dragbarTitle);
        expect(dragitem.classList.contains('cms-dragitem-expanded')).toBe(false);
        expect(dragbarTitle.classList.contains('cms-dragbar-title-expanded')).toBe(false);
    });
});

describe('collapse — updatePlaceholderCollapseState', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsTestable }).CMS;
    });

    it('marks dragbar expanded when every closed plugin is a leaf', () => {
        // Two-plugin placeholder; plugin 1 is the parent (open), plugin 2 a leaf (closed).
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-7">
                <span class="cms-dragbar-title">Title</span>
            </div>
        `;
        (window as unknown as { CMS: CmsTestable }).CMS = {
            settings: { states: [1] },
            _plugins: [
                ['cms-plugin-1', { type: 'plugin', placeholder_id: 7, plugin_id: 1 }],
                ['cms-plugin-2', {
                    type: 'plugin',
                    placeholder_id: 7,
                    plugin_id: 2,
                    plugin_parent: 1,
                }],
            ],
        };
        updatePlaceholderCollapseState(makePlugin());
        const title = document.querySelector('.cms-dragbar-title');
        expect(title?.classList.contains('cms-dragbar-title-expanded')).toBe(true);
    });

    it('clears dragbar when a parent is still closed', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-7">
                <span class="cms-dragbar-title cms-dragbar-title-expanded">Title</span>
            </div>
        `;
        (window as unknown as { CMS: CmsTestable }).CMS = {
            settings: { states: [], dragbars: [7] },
            _plugins: [
                ['cms-plugin-1', { type: 'plugin', placeholder_id: 7, plugin_id: 1 }],
                ['cms-plugin-2', {
                    type: 'plugin',
                    placeholder_id: 7,
                    plugin_id: 2,
                    plugin_parent: 1,
                }],
            ],
        };
        updatePlaceholderCollapseState(makePlugin());
        const title = document.querySelector('.cms-dragbar-title');
        expect(title?.classList.contains('cms-dragbar-title-expanded')).toBe(false);
    });

    it('is a no-op for non-plugin descriptors', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-7">
                <span class="cms-dragbar-title">Title</span>
            </div>
        `;
        updatePlaceholderCollapseState(makePlugin({ type: 'placeholder' }));
        const title = document.querySelector('.cms-dragbar-title');
        expect(title?.classList.contains('cms-dragbar-title-expanded')).toBe(false);
    });
});

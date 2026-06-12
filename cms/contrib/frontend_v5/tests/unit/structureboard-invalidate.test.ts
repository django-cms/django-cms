import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { invalidateState } from '../../frontend/modules/structureboard/invalidate';
import {
    STORAGE_KEY,
    _resetForTest as _resetPropagateForTest,
} from '../../frontend/modules/structureboard/network/propagate';
import type { PluginInstance, PluginOptions } from '../../frontend/modules/plugins/types';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: { states?: Array<number | string> };
    _instances?: PluginInstance[];
    _plugins?: Array<[string, PluginOptions]>;
}

function setupCms(): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {},
        settings: { states: [] },
        _instances: [],
        _plugins: [],
    };
}

function getCms(): CmsTestable {
    return (window as unknown as { CMS: CmsTestable }).CMS;
}

beforeEach(() => {
    document.body.innerHTML = '';
    setupCms();
    _resetPropagateForTest();
    localStorage.clear();
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetPropagateForTest();
    localStorage.clear();
    vi.restoreAllMocks();
});

describe('invalidateState — dispatch', () => {
    it('routes ADD to handleAddPlugin', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        invalidateState(
            'ADD',
            {
                placeholder_id: 1,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"></div>',
                    plugins: [{ type: 'plugin', plugin_id: 7 } as PluginOptions],
                },
            },
            { propagate: false },
        );
        expect(document.querySelector('.cms-draggable-7')).not.toBeNull();
    });

    it('routes EDIT to handleEditPlugin', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">old</div></div>
        `;
        invalidateState(
            'EDIT',
            {
                plugin_id: 7,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">new</div></div>',
                    plugins: [],
                },
            },
            { propagate: false },
        );
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent,
        ).toBe('new');
    });

    it('routes CHANGE to handleEditPlugin (legacy aliases)', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">old</div></div>
        `;
        invalidateState(
            'CHANGE',
            {
                plugin_id: 7,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">changed</div></div>',
                    plugins: [],
                },
            },
            { propagate: false },
        );
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent,
        ).toBe('changed');
    });

    it('routes DELETE to handleDeletePlugin', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        invalidateState('DELETE', { plugin_id: 7 }, { propagate: false });
        expect(document.querySelector('.cms-draggable-7')).toBeNull();
    });

    it('routes CLEAR_PLACEHOLDER to handleClearPlaceholder', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        invalidateState(
            'CLEAR_PLACEHOLDER',
            { placeholder_id: 1 },
            { propagate: false },
        );
        expect(document.querySelector('.cms-draggable-7')).toBeNull();
    });

    it('routes MOVE and PASTE to handleMovePlugin', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">old</div></div>
                </div>
            </div>
        `;
        invalidateState(
            'MOVE',
            {
                plugin_id: 7,
                placeholder_id: 1,
                html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">moved</div></div>',
                plugins: [],
            },
            { propagate: false },
        );
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent,
        ).toBe('moved');
    });

    it('routes COPY to handleCopyPlugin', () => {
        document.body.innerHTML = `<div class="cms-clipboard-containers"></div>`;
        invalidateState(
            'COPY',
            {
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [{ type: 'plugin', plugin_id: 7 } as PluginOptions],
            },
            { propagate: false },
        );
        expect(
            document.querySelector('.cms-clipboard-containers .cms-draggable-7'),
        ).not.toBeNull();
    });

    it('routes CUT to handleCutPlugin', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
            <div class="cms-clipboard-containers"></div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        invalidateState(
            'CUT',
            {
                plugin_id: 7,
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [{ type: 'plugin', plugin_id: 7 } as PluginOptions],
            },
            { propagate: false },
        );
        expect(document.querySelector('.cms-dragarea-1 .cms-draggable-7')).toBeNull();
        expect(
            document.querySelector('.cms-clipboard-containers .cms-draggable-7'),
        ).not.toBeNull();
    });
});

describe('invalidateState — propagation', () => {
    it('writes to localStorage by default', () => {
        document.body.innerHTML = `<div class="cms-clipboard-containers"></div>`;
        invalidateState('COPY', { html: '<div></div>', plugins: [] });
        expect(localStorage.getItem(STORAGE_KEY)).not.toBeNull();
    });

    it('skips propagation when propagate: false', () => {
        document.body.innerHTML = `<div class="cms-clipboard-containers"></div>`;
        invalidateState(
            'COPY',
            { html: '<div></div>', plugins: [] },
            { propagate: false },
        );
        expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
});

describe('invalidateState — onContentRefresh', () => {
    it('fires onContentRefresh for visible-content actions', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        const refresh = vi.fn();
        invalidateState(
            'ADD',
            {
                placeholder_id: 1,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"></div>',
                    plugins: [],
                },
            },
            { propagate: false, onContentRefresh: refresh },
        );
        expect(refresh).toHaveBeenCalledOnce();
        const args = refresh.mock.calls[0]!;
        expect(args[0]).toBe('ADD');
    });

    it('does NOT fire onContentRefresh for COPY (clipboard-only change)', () => {
        document.body.innerHTML = `<div class="cms-clipboard-containers"></div>`;
        const refresh = vi.fn();
        invalidateState(
            'COPY',
            { html: '<div></div>', plugins: [] },
            { propagate: false, onContentRefresh: refresh },
        );
        expect(refresh).not.toHaveBeenCalled();
    });
});

describe('invalidateState — fallback', () => {
    it('calls onFullReload for undefined / null / empty action', () => {
        const reload = vi.fn();
        invalidateState(undefined, {}, { onFullReload: reload });
        invalidateState(null, {}, { onFullReload: reload });
        invalidateState('', {}, { onFullReload: reload });
        expect(reload).toHaveBeenCalledTimes(3);
    });

    it('does not propagate or refresh on fallback', () => {
        const refresh = vi.fn();
        invalidateState(
            undefined,
            {},
            { onFullReload: () => {}, onContentRefresh: refresh },
        );
        expect(refresh).not.toHaveBeenCalled();
        expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
});

describe('invalidateState — recalculatePluginPositions', () => {
    it('recomputes position for plugins in the affected placeholder', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-8"></div>
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        const cms = getCms();
        const plugin7: PluginInstance = {
            options: {
                type: 'plugin',
                plugin_id: 7,
                placeholder_id: 1,
                position: 99,
            } as PluginOptions,
        };
        const plugin8: PluginInstance = {
            options: {
                type: 'plugin',
                plugin_id: 8,
                placeholder_id: 1,
                position: 99,
            } as PluginOptions,
        };
        cms._instances!.push(plugin7, plugin8);
        invalidateState(
            'EDIT',
            {
                plugin_id: 7,
                placeholder_id: 1,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"></div>',
                    plugins: [],
                },
            },
            { propagate: false },
        );
        // Order in DOM: 8 then 7 → positions 1 and 2.
        expect(plugin8.options.position).toBe(1);
        expect(plugin7.options.position).toBe(2);
    });
});

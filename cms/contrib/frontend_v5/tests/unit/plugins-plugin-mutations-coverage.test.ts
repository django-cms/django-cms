/*
 * Coverage tests added in response to the Phase-2 audit. Cover paths
 * the original mutation-suite missed: pastePlugin, editPluginPostAjax,
 * _checkIfPasteAllowed restriction branch, withLock async-throw
 * release, _setPluginStructureEvents listener wiring.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Plugin, _registerForTest } from '../../frontend/modules/plugins/plugin';
import { _resetRegistryForTest } from '../../frontend/modules/plugins/registry';
import { setPlaceholderData } from '../../frontend/modules/plugins/cms-data';
import { withLock } from '../../frontend/modules/plugins/mutations';
import { getCmsLocked } from '../../frontend/modules/plugins/cms-globals';
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
            csrf: 'csrf',
            request: { language: 'en' },
            clipboard: { id: 99 },
            lang: { success: 'OK', error: 'Err: ' },
        },
        settings: { mode: 'edit' },
        API: { locked: false, ...((extras.API as Record<string, unknown>) ?? {}) },
        _instances: [],
        _plugins: [],
        ...extras,
    };
}

describe('withLock — async error path', () => {
    beforeEach(() => setupCms());
    afterEach(() => {
        delete (window as { CMS?: unknown }).CMS;
    });

    it('releases the lock when the inner fn throws', async () => {
        await expect(
            withLock(async () => {
                throw new Error('boom');
            }),
        ).rejects.toThrow('boom');
        expect(getCmsLocked()).toBe(false);
    });

    it('returns undefined when already locked', async () => {
        setupCms({ API: { locked: true } });
        const result = await withLock(async () => 'ran');
        expect(result).toBeUndefined();
    });
});

describe('Plugin.editPluginPostAjax', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('forwards URL + breadcrumb into editPlugin', () => {
        const opens: Array<Record<string, unknown>> = [];
        class FakeModal {
            open(opts: Record<string, unknown>) {
                opens.push(opts);
            }
        }
        setupCms();
        (window as unknown as { CMS: CmsTestable }).CMS.Modal = FakeModal;
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-1"></div>`;
        const p = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            plugin_name: 'Edit Me',
        });
        p.editPluginPostAjax(null, {
            url: '/edit/post/1/',
            breadcrumb: [{ title: 'A', url: '/a/' }],
        });
        expect(opens.length).toBe(1);
        // Helpers.updateUrlWithPath appends `?cms_path=` to the URL.
        expect(opens[0]?.url).toMatch(/^\/edit\/post\/1\//);
        expect(opens[0]?.title).toBe('Edit Me');
        expect(opens[0]?.breadcrumbs).toEqual([{ title: 'A', url: '/a/' }]);
    });

    it('is a no-op when response has no url', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-1"></div>`;
        const p = new Plugin('cms-plugin-1', { type: 'plugin', plugin_id: 1 });
        expect(() => p.editPluginPostAjax(null, {})).not.toThrow();
    });
});

describe('Plugin._checkIfPasteAllowed — restriction branch', () => {
    beforeEach(() => {
        _resetRegistryForTest();
        setupCms();
    });
    afterEach(() => {
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
        document.body.innerHTML = '';
    });

    it('disables paste when clipboard plugin type is not in plugin_restriction', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-draggable cms-draggable-from-clipboard cms-draggable-9"></div>
            <div id="dd" class="cms-submenu-dropdown">
                <div class="cms-submenu-item">
                    <a data-rel="paste"></a>
                    <span class="cms-submenu-item-paste-tooltip-restricted"></span>
                </div>
            </div>
        `;
        const clipboard = document.querySelector<HTMLElement>(
            '.cms-draggable-from-clipboard',
        )!;
        // Clipboard data: it's a TextPlugin.
        setPlaceholderData(clipboard, {
            type: 'plugin',
            plugin_id: 9,
            plugin_type: 'TextPlugin',
        });
        const p = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            plugin_type: 'ColumnPlugin',
            plugin_restriction: ['LinkPlugin'], // Text not allowed
        });
        p.ui.dropdown = document.getElementById('dd') as HTMLElement;
        expect(p._checkIfPasteAllowed()).toBe(false);
        const item = document.querySelector('.cms-submenu-item') as HTMLElement;
        expect(item.classList.contains('cms-submenu-item-disabled')).toBe(true);
        const tooltip = document.querySelector(
            '.cms-submenu-item-paste-tooltip-restricted',
        ) as HTMLElement;
        expect(tooltip.style.display).toBe('block');
    });

    it('allows paste when clipboard type matches restriction', () => {
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-draggable cms-draggable-from-clipboard cms-draggable-9"></div>
            <div id="dd" class="cms-submenu-dropdown">
                <div class="cms-submenu-item cms-submenu-item-disabled">
                    <a data-rel="paste" tabindex="-1" aria-disabled="true"></a>
                </div>
            </div>
        `;
        const clipboard = document.querySelector<HTMLElement>(
            '.cms-draggable-from-clipboard',
        )!;
        setPlaceholderData(clipboard, {
            type: 'plugin',
            plugin_id: 9,
            plugin_type: 'TextPlugin',
        });
        const p = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            plugin_type: 'ColumnPlugin',
            plugin_restriction: ['TextPlugin'],
        });
        p.ui.dropdown = document.getElementById('dd') as HTMLElement;
        expect(p._checkIfPasteAllowed()).toBe(true);
        const item = document.querySelector('.cms-submenu-item') as HTMLElement;
        expect(item.classList.contains('cms-submenu-item-disabled')).toBe(false);
        const link = document.querySelector('a') as HTMLAnchorElement;
        expect(link.hasAttribute('tabindex')).toBe(false);
    });
});

describe('Plugin.pastePlugin', () => {
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

    it('clones the clipboard draggable into the destination + calls source.movePlugin with move_a_copy', async () => {
        const post = vi.spyOn(request, 'post').mockResolvedValue({});
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-draggable cms-draggable-from-clipboard cms-draggable-9"></div>
            <div class="cms-dragarea cms-dragarea-7">
                <div class="cms-dragbar cms-dragbar-7"></div>
                <div class="cms-draggables" id="dest"></div>
            </div>
        `;
        // Source (clipboard) plugin instance, registered.
        const source = new Plugin('cms-plugin-9', {
            type: 'plugin',
            plugin_id: 9,
            placeholder_id: 99, // clipboard
            urls: { move_plugin: '/move/' },
        });
        _registerForTest(source);
        // Destination plugin instance.
        const dest = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            placeholder_id: 7,
        });
        dest.ui.draggables = document.getElementById('dest') as HTMLElement;
        dest.pastePlugin();
        // Clone appended.
        const dropZone = document.getElementById('dest')!;
        expect(
            dropZone.querySelector('.cms-draggable-9'),
        ).not.toBeNull();
        // Source.movePlugin called → POST issued.
        await new Promise((r) => setTimeout(r, 0));
        expect(post).toHaveBeenCalled();
        const params = new URLSearchParams(
            post.mock.calls[0]?.[1] as URLSearchParams,
        );
        expect(params.get('plugin_id')).toBe('9');
        expect(params.get('move_a_copy')).toBe('true');
    });

    it('is a no-op when no clipboard draggable is on the page', () => {
        document.body.innerHTML = `<div class="cms-plugin cms-plugin-1"></div>`;
        const dest = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            placeholder_id: 7,
        });
        expect(() => dest.pastePlugin()).not.toThrow();
    });
});

describe('Plugin._setPluginStructureEvents — listener wiring', () => {
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

    it('cms-plugins-update fires movePlugin', async () => {
        vi.spyOn(request, 'post').mockResolvedValue({});
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-1"></div>
            <div class="cms-dragarea cms-dragarea-7">
                <div class="cms-dragbar cms-dragbar-7"></div>
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-1">
                        <div class="cms-dragitem"><div class="cms-dragitem-text">x</div></div>
                        <div class="cms-draggables"></div>
                    </div>
                </div>
            </div>
        `;
        const p = new Plugin('cms-plugin-1', {
            type: 'plugin',
            plugin_id: 1,
            placeholder_id: 7,
            urls: { move_plugin: '/move/' },
        });
        _registerForTest(p);
        p._setPluginStructureEvents();
        const draggable = document.querySelector('.cms-draggable-1') as HTMLElement;
        const moveSpy = vi.spyOn(p, 'movePlugin').mockResolvedValue();
        draggable.dispatchEvent(
            new CustomEvent('cms-plugins-update', { detail: {} }),
        );
        expect(moveSpy).toHaveBeenCalledOnce();
    });
});

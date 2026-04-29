import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { handleAddPlugin } from '../../frontend/modules/structureboard/handlers/add';
import { handleEditPlugin } from '../../frontend/modules/structureboard/handlers/edit';
import { handleDeletePlugin } from '../../frontend/modules/structureboard/handlers/delete';
import { handleClearPlaceholder } from '../../frontend/modules/structureboard/handlers/clear';
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
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
});

// ────────────────────────────────────────────────────────────────────
// handleAddPlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleAddPlugin', () => {
    it('appends to the placeholder when no plugin_parent is given', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleAddPlugin({
            placeholder_id: 1,
            structure: {
                html: '<div class="cms-draggable cms-draggable-7">new</div>',
                plugins: [
                    {
                        type: 'plugin',
                        plugin_id: 7,
                        placeholder_id: 1,
                    } as PluginOptions,
                ],
            },
        });
        const list = document.querySelector('.cms-dragarea-1 > .cms-draggables')!;
        expect(list.children.length).toBe(1);
        expect(
            (list.children[0] as HTMLElement).classList.contains('cms-draggable-7'),
        ).toBe(true);
    });

    it('replaces the parent draggable when plugin_parent is given (nested add)', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99" id="parent">
                        <div class="cms-dragitem">old parent</div>
                    </div>
                </div>
            </div>
        `;
        handleAddPlugin({
            placeholder_id: 1,
            plugin_parent: 99,
            structure: {
                html: `
                    <div class="cms-draggable cms-draggable-99" id="parent">
                        <div class="cms-dragitem">new parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7"></div>
                        </div>
                    </div>
                `,
                plugins: [
                    {
                        type: 'plugin',
                        plugin_id: 7,
                        placeholder_id: 1,
                    } as PluginOptions,
                ],
            },
        });
        // Parent is replaced; child draggable is now visible.
        expect(document.querySelector('.cms-draggable-7')).not.toBeNull();
        expect(
            document.querySelector('.cms-draggable-99 .cms-dragitem')!.textContent,
        ).toContain('new parent');
    });

    it('writes plugin descriptors into the registry', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleAddPlugin({
            placeholder_id: 1,
            structure: {
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [
                    {
                        type: 'plugin',
                        plugin_id: 7,
                        placeholder_id: 1,
                    } as PluginOptions,
                ],
            },
        });
        const cms = getCms();
        expect(cms._plugins!.length).toBe(1);
        expect(cms._plugins![0]![0]).toBe('cms-plugin-7');
        expect(cms._instances!.length).toBe(1);
    });

    it('updates dragarea-empty class via actualizePlaceholders', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1 cms-dragarea-empty">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleAddPlugin({
            placeholder_id: 1,
            structure: {
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [],
            },
        });
        expect(
            document
                .querySelector('.cms-dragarea-1')!
                .classList.contains('cms-dragarea-empty'),
        ).toBe(false);
    });

    it('plugin_parent === "" treated as root add (legacy: empty string)', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleAddPlugin({
            placeholder_id: 1,
            plugin_parent: '',
            structure: {
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [],
            },
        });
        expect(document.querySelector('.cms-draggable-7')).not.toBeNull();
    });
});

// ────────────────────────────────────────────────────────────────────
// handleEditPlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleEditPlugin', () => {
    it('replaces the edited draggable when no plugin_parent', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-dragitem">old</div>
            </div>
        `;
        handleEditPlugin({
            plugin_id: 7,
            structure: {
                html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">new</div></div>',
                plugins: [
                    {
                        type: 'plugin',
                        plugin_id: 7,
                    } as PluginOptions,
                ],
            },
        });
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent,
        ).toBe('new');
    });

    it('replaces the parent draggable when plugin_parent is given', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-99">
                <div class="cms-dragitem">parent</div>
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">old child</div>
                    </div>
                </div>
            </div>
        `;
        handleEditPlugin({
            plugin_id: 7,
            plugin_parent: 99,
            structure: {
                html: `
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-dragitem">parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7">
                                <div class="cms-dragitem">new child</div>
                            </div>
                        </div>
                    </div>
                `,
                plugins: [],
            },
        });
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent!.trim(),
        ).toBe('new child');
    });

    it('updates the registry with the new descriptors', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7"></div>
        `;
        // Pre-seed registry with stale descriptor.
        const cms = getCms();
        cms._plugins!.push([
            'cms-plugin-7',
            { type: 'plugin', plugin_id: 7, name: 'old' } as PluginOptions,
        ]);
        handleEditPlugin({
            plugin_id: 7,
            structure: {
                html: '<div class="cms-draggable cms-draggable-7"></div>',
                plugins: [
                    {
                        type: 'plugin',
                        plugin_id: 7,
                        name: 'new',
                    } as PluginOptions,
                ],
            },
        });
        expect(cms._plugins!.length).toBe(1);
        expect((cms._plugins![0]![1] as PluginOptions).name).toBe('new');
    });
});

// ────────────────────────────────────────────────────────────────────
// handleDeletePlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleDeletePlugin', () => {
    function preSeed(): void {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">x</div>
                    </div>
                </div>
            </div>
            <div class="cms-plugin cms-plugin-7">rendered</div>
            <script data-cms-plugin id="cms-plugin-7" type="application/json">{}</script>
        `;
        const cms = getCms();
        cms._plugins!.push([
            'cms-plugin-7',
            { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        ]);
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
    }

    it('removes the draggable, rendered content, and script blob (no content data)', () => {
        preSeed();
        handleDeletePlugin({ plugin_id: 7 });
        expect(document.querySelector('.cms-draggable-7')).toBeNull();
        expect(document.querySelector('.cms-plugin-7')).toBeNull();
        expect(document.getElementById('cms-plugin-7')).toBeNull();
    });

    it('keeps rendered content when data.structure.content is present', () => {
        preSeed();
        handleDeletePlugin({
            plugin_id: 7,
            structure: { content: [{ pluginIds: [7], html: '<div>updated</div>' }] },
        });
        expect(document.querySelector('.cms-draggable-7')).toBeNull();
        // .cms-plugin-7 still in DOM (data-bridge will swap)
        expect(document.querySelector('.cms-plugin-7')).not.toBeNull();
        // Script blob always removed
        expect(document.getElementById('cms-plugin-7')).toBeNull();
    });

    it('keeps rendered content when data.content is present (cut payload)', () => {
        preSeed();
        handleDeletePlugin({
            plugin_id: 7,
            content: [{ pluginIds: [7], html: '<div>cut</div>' }],
        });
        expect(document.querySelector('.cms-plugin-7')).not.toBeNull();
    });

    it('drops the registry entries', () => {
        preSeed();
        handleDeletePlugin({ plugin_id: 7 });
        const cms = getCms();
        expect(cms._plugins!.length).toBe(0);
        expect(cms._instances!.length).toBe(0);
    });

    it('also drops registry entries for nested children', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-8">
                                <div class="cms-dragitem">child</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const cms = getCms();
        cms._plugins!.push(
            [
                'cms-plugin-7',
                { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
            ],
            [
                'cms-plugin-8',
                {
                    type: 'plugin',
                    plugin_id: 8,
                    placeholder_id: 1,
                    plugin_parent: 7,
                } as PluginOptions,
            ],
        );
        cms._instances!.push(
            { options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions },
            { options: { type: 'plugin', plugin_id: 8, placeholder_id: 1 } as PluginOptions },
        );

        handleDeletePlugin({ plugin_id: 7 });
        expect(cms._plugins!.length).toBe(0);
        expect(cms._instances!.length).toBe(0);
    });

    it('updates parent collapsible status after delete', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-dragitem cms-dragitem-collapsable">parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        handleDeletePlugin({ plugin_id: 7 });
        // Parent's draggables list is now empty → not collapsable
        expect(
            document
                .querySelector('.cms-draggable-99 > .cms-dragitem')!
                .classList.contains('cms-dragitem-collapsable'),
        ).toBe(false);
    });

    it('refreshes placeholder empty state', () => {
        preSeed();
        handleDeletePlugin({ plugin_id: 7 });
        expect(
            document.querySelector('.cms-dragarea-1')!.classList.contains('cms-dragarea-empty'),
        ).toBe(true);
    });

    it('returns void without throwing when plugin_id is missing', () => {
        expect(() => handleDeletePlugin({})).not.toThrow();
    });
});

// ────────────────────────────────────────────────────────────────────
// handleClearPlaceholder
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleClearPlaceholder', () => {
    it('removes every draggable in the placeholder', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                    <div class="cms-draggable cms-draggable-8"></div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-9"></div>
                </div>
            </div>
        `;
        const cms = getCms();
        cms._instances!.push(
            { options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions },
            { options: { type: 'plugin', plugin_id: 8, placeholder_id: 1 } as PluginOptions },
            { options: { type: 'plugin', plugin_id: 9, placeholder_id: 2 } as PluginOptions },
        );
        cms._plugins!.push(
            ['cms-plugin-7', { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions],
            ['cms-plugin-8', { type: 'plugin', plugin_id: 8, placeholder_id: 1 } as PluginOptions],
            ['cms-plugin-9', { type: 'plugin', plugin_id: 9, placeholder_id: 2 } as PluginOptions],
        );
        handleClearPlaceholder({ placeholder_id: 1 });
        expect(document.querySelector('.cms-dragarea-1 .cms-draggable')).toBeNull();
        expect(document.querySelector('.cms-draggable-9')).not.toBeNull();
    });

    it('drops the registry entries for the cleared placeholder only', () => {
        const cms = getCms();
        cms._instances!.push(
            { options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions },
            { options: { type: 'plugin', plugin_id: 9, placeholder_id: 2 } as PluginOptions },
        );
        cms._plugins!.push(
            ['cms-plugin-7', { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions],
            ['cms-plugin-9', { type: 'plugin', plugin_id: 9, placeholder_id: 2 } as PluginOptions],
        );
        handleClearPlaceholder({ placeholder_id: 1 });
        expect(cms._instances!.length).toBe(1);
        expect(cms._plugins!.length).toBe(1);
        expect(cms._plugins![0]![0]).toBe('cms-plugin-9');
    });

    it('keeps rendered content + scripts (full refresh follows)', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
            <div class="cms-plugin cms-plugin-7">rendered</div>
            <script data-cms-plugin id="cms-plugin-7" type="application/json">{}</script>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        cms._plugins!.push([
            'cms-plugin-7',
            { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        ]);
        handleClearPlaceholder({ placeholder_id: 1 });
        expect(document.querySelector('.cms-plugin-7')).not.toBeNull();
        expect(document.getElementById('cms-plugin-7')).not.toBeNull();
    });

    it('marks the placeholder as empty', () => {
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
        handleClearPlaceholder({ placeholder_id: 1 });
        expect(
            document.querySelector('.cms-dragarea-1')!.classList.contains('cms-dragarea-empty'),
        ).toBe(true);
    });

    it('handles a placeholder with no plugins', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        expect(() => handleClearPlaceholder({ placeholder_id: 1 })).not.toThrow();
    });

    it('coerces string placeholder_id to number', () => {
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        handleClearPlaceholder({ placeholder_id: '1' });
        expect(cms._instances!.length).toBe(0);
    });

    it('skips non-plugin instances (placeholder/generic)', () => {
        const cms = getCms();
        cms._instances!.push(
            { options: { type: 'placeholder', placeholder_id: 1 } as PluginOptions },
            { options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions },
        );
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        handleClearPlaceholder({ placeholder_id: 1 });
        // placeholder instance preserved, plugin instance gone
        expect(cms._instances!.length).toBe(1);
        expect(cms._instances![0]!.options.type).toBe('placeholder');
    });
});

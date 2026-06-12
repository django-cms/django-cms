import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { handleMovePlugin } from '../../frontend/modules/structureboard/handlers/move';
import { handleCopyPlugin } from '../../frontend/modules/structureboard/handlers/copy';
import { handleCutPlugin } from '../../frontend/modules/structureboard/handlers/cut';
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
// handleMovePlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleMovePlugin (nested)', () => {
    it('replaces the parent draggable with the server response', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-dragitem">old parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7">
                                <div class="cms-dragitem">child</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            plugin_parent: 99,
            html: `
                <div class="cms-draggable cms-draggable-99">
                    <div class="cms-dragitem">new parent</div>
                    <div class="cms-draggables">
                        <div class="cms-draggable cms-draggable-7">
                            <div class="cms-dragitem">moved</div>
                        </div>
                    </div>
                </div>
            `,
            plugins: [],
        });
        expect(
            document
                .querySelector('.cms-draggable-99 > .cms-dragitem')!
                .textContent!.trim(),
        ).toBe('new parent');
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent!.trim(),
        ).toBe('moved');
    });

    it('removes a stale leftover draggable outside the new parent', () => {
        // Plugin 7 is in placeholder 1's tree but the new parent (99)
        // is in a different placeholder. Stale .cms-draggable-7 should
        // be removed before the parent replacement.
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7" id="stale">
                        <div class="cms-dragitem">stale</div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-dragitem">parent</div>
                    </div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            plugin_parent: 99,
            html: `
                <div class="cms-draggable cms-draggable-99">
                    <div class="cms-dragitem">parent</div>
                    <div class="cms-draggables">
                        <div class="cms-draggable cms-draggable-7">
                            <div class="cms-dragitem">moved</div>
                        </div>
                    </div>
                </div>
            `,
            plugins: [],
        });
        // Stale gone, new draggable inside new parent
        expect(document.getElementById('stale')).toBeNull();
        expect(
            document.querySelector('.cms-draggable-99 .cms-draggable-7'),
        ).not.toBeNull();
    });

    it('does NOT remove a stale leftover that is from the clipboard', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7 cms-draggable-from-clipboard" id="clip"></div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99">
                        <div class="cms-dragitem">parent</div>
                    </div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            plugin_parent: 99,
            html: `
                <div class="cms-draggable cms-draggable-99">
                    <div class="cms-dragitem">parent</div>
                    <div class="cms-draggables">
                        <div class="cms-draggable cms-draggable-7"></div>
                    </div>
                </div>
            `,
            plugins: [],
        });
        // Clipboard original preserved
        expect(document.getElementById('clip')).not.toBeNull();
    });
});

describe('handlers — handleMovePlugin (top-level)', () => {
    it('replaces the dragged draggable with the server response', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">old</div>
                    </div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 1,
            html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">new</div></div>',
            plugins: [],
        });
        expect(
            document.querySelector('.cms-draggable-7 .cms-dragitem')!.textContent,
        ).toBe('new');
    });

    it('relocates the draggable across placeholders when not in target', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">x</div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 2,
            plugin_order: [7],
            html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">moved</div></div>',
            plugins: [],
        });
        const dst = document.querySelector('.cms-dragarea-2 > .cms-draggables')!;
        expect(dst.children.length).toBe(1);
        expect(
            (dst.children[0] as HTMLElement).classList.contains('cms-draggable-7'),
        ).toBe(true);
    });

    it('reorders within the same placeholder when DOM order diverges from data.plugin_order', () => {
        // External update: another tab moved plugin 7 in front of 8.
        // Locally DOM still has order [8, 7]; data.plugin_order = [7, 8].
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-8"><div class="cms-dragitem">8</div></div>
                    <div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">7</div></div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 1,
            plugin_order: [7, 8],
            html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">7</div></div>',
            plugins: [],
        });
        const list = document.querySelector('.cms-dragarea-1 > .cms-draggables')!;
        expect(
            (list.children[0] as HTMLElement).classList.contains('cms-draggable-7'),
        ).toBe(true);
        expect(
            (list.children[1] as HTMLElement).classList.contains('cms-draggable-8'),
        ).toBe(true);
    });

    it('clones from clipboard during cross-placeholder paste (clipboard original preserved)', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7 cms-draggable-from-clipboard">
                        <div class="cms-dragitem">clip</div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 1,
            plugin_order: [7],
            html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">pasted</div></div>',
            plugins: [],
        });
        // Clipboard original still there
        expect(
            document.querySelector('.cms-clipboard-containers .cms-draggable-7'),
        ).not.toBeNull();
        // Destination has the replacement
        expect(
            document.querySelector('.cms-dragarea-1 .cms-draggable-7'),
        ).not.toBeNull();
    });

    it('appends to target_placeholder_id when no source draggable exists (cross-language paste)', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 999, // non-existent
            target_placeholder_id: 2,
            html: '<div class="cms-draggable cms-draggable-7"><div class="cms-dragitem">x</div></div>',
            plugins: [],
        });
        expect(
            document.querySelector('.cms-dragarea-2 .cms-draggable-7'),
        ).not.toBeNull();
    });

    it('updates the registry with the new plugin descriptors', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 1,
            html: '<div class="cms-draggable cms-draggable-7"></div>',
            plugins: [
                { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
            ],
        });
        expect(getCms()._plugins!.length).toBe(1);
    });

    it('refreshes placeholder empty state after move', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
        handleMovePlugin({
            plugin_id: 7,
            placeholder_id: 2,
            plugin_order: [7],
            html: '<div class="cms-draggable cms-draggable-7"></div>',
            plugins: [],
        });
        expect(
            document
                .querySelector('.cms-dragarea-1')!
                .classList.contains('cms-dragarea-empty'),
        ).toBe(true);
        expect(
            document
                .querySelector('.cms-dragarea-2')!
                .classList.contains('cms-dragarea-empty'),
        ).toBe(false);
    });
});

// ────────────────────────────────────────────────────────────────────
// handleCopyPlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleCopyPlugin', () => {
    it('replaces .cms-clipboard-containers innerHTML with data.html', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers">
                <div class="cms-draggables"><div>old</div></div>
            </div>
        `;
        handleCopyPlugin({
            html: '<div class="cms-draggables"><div class="cms-draggable cms-draggable-7"></div></div>',
            plugins: [{ type: 'plugin', plugin_id: 7 } as PluginOptions],
        });
        expect(
            document.querySelector('.cms-clipboard-containers .cms-draggable-7'),
        ).not.toBeNull();
    });

    it('pushes the copied descriptor into the registry', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers"></div>
        `;
        handleCopyPlugin({
            html: '<div></div>',
            plugins: [{ type: 'plugin', plugin_id: 42 } as PluginOptions],
        });
        const cms = getCms();
        expect(cms._plugins!.length).toBe(1);
        expect(cms._plugins![0]![0]).toBe('cms-plugin-42');
    });

    it('dispatches cms-clipboard-update for the legacy/clipboard module', () => {
        let detail: unknown = null;
        document.addEventListener('cms-clipboard-update', (e) => {
            detail = (e as CustomEvent).detail;
        });
        handleCopyPlugin({
            html: '<div></div>',
            plugins: [{ type: 'plugin', plugin_id: 1 } as PluginOptions],
        });
        expect(detail).not.toBeNull();
    });
});

// ────────────────────────────────────────────────────────────────────
// handleCutPlugin
// ────────────────────────────────────────────────────────────────────

describe('handlers — handleCutPlugin', () => {
    it('combines delete + copy', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">x</div>
                    </div>
                </div>
            </div>
            <div class="cms-clipboard-containers">old</div>
        `;
        const cms = getCms();
        cms._instances!.push({
            options: { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        });
        cms._plugins!.push([
            'cms-plugin-7',
            { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
        ]);
        handleCutPlugin({
            plugin_id: 7,
            html: '<div class="cms-draggables"><div class="cms-draggable cms-draggable-7"></div></div>',
            plugins: [
                { type: 'plugin', plugin_id: 7, placeholder_id: 1 } as PluginOptions,
            ],
        });
        // Source placeholder draggable removed
        expect(
            document.querySelector('.cms-dragarea-1 .cms-draggable-7'),
        ).toBeNull();
        // Clipboard repopulated
        expect(
            document.querySelector('.cms-clipboard-containers .cms-draggable-7'),
        ).not.toBeNull();
        // Registry has the descriptor (re-added by COPY)
        expect(cms._plugins!.length).toBe(1);
    });
});

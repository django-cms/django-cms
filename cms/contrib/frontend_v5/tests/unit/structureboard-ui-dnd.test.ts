import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    canDrag,
    canDropAsChild,
    onDrop,
    setupStructureBoardDnd,
} from '../../frontend/modules/structureboard/ui/dnd';
import { setElementData } from '../../frontend/modules/core/element-data';
import {
    setPlaceholderData,
} from '../../frontend/modules/plugins/cms-data';
import type { PluginOptions } from '../../frontend/modules/plugins/types';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    API?: { locked?: boolean };
}

function setupCms(extras: Partial<CmsTestable> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {},
        settings: {},
        API: { locked: false },
        ...extras,
    };
}

beforeEach(() => {
    document.body.innerHTML = '';
    setupCms();
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
    vi.restoreAllMocks();
});

// ────────────────────────────────────────────────────────────────────
// canDrag
// ────────────────────────────────────────────────────────────────────

describe('ui/dnd — canDrag', () => {
    function fixture(html: string): HTMLElement {
        document.body.innerHTML = html;
        return document.querySelector<HTMLElement>('.cms-draggable')!;
    }

    it('allows drag for a normal draggable', () => {
        const item = fixture(`
            <div class="cms-dragarea">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `);
        expect(canDrag(item)).toBe(true);
    });

    it('blocks drag when the item itself has cms-drag-disabled', () => {
        const item = fixture(`
            <div class="cms-dragarea">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7 cms-drag-disabled"></div>
                </div>
            </div>
        `);
        expect(canDrag(item)).toBe(false);
    });

    it('blocks drag when an ancestor has cms-draggable-disabled', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-1 cms-draggable-disabled">
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7" id="child"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const child = document.getElementById('child') as HTMLElement;
        expect(canDrag(child)).toBe(false);
    });

    it('blocks drag when CMS.API.locked is true', () => {
        setupCms({ API: { locked: true } });
        const item = fixture(`
            <div class="cms-dragarea">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7"></div>
                </div>
            </div>
        `);
        expect(canDrag(item)).toBe(false);
    });
});

// ────────────────────────────────────────────────────────────────────
// canDropAsChild
// ────────────────────────────────────────────────────────────────────

describe('ui/dnd — canDropAsChild', () => {
    function makeDraggable(
        cls: string,
        data?: Partial<PluginOptions>,
    ): HTMLElement {
        const el = document.createElement('div');
        el.className = `cms-draggable ${cls}`;
        if (data) {
            // Plugin shape = array
            setElementData(el, 'cms', [data as PluginOptions]);
        }
        return el;
    }

    it('rejects when CMS.API.locked', () => {
        setupCms({ API: { locked: true } });
        const target = makeDraggable('cms-draggable-1');
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('rejects when target is in clipboard', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-1" id="target"></div>
                </div>
            </div>
        `;
        const target = document.getElementById('target') as HTMLElement;
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        setElementData(item, 'cms', [
            { type: 'plugin', plugin_type: 'TextPlugin' } as PluginOptions,
        ]);
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('rejects when target list has cms-drag-disabled', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables cms-drag-disabled">
                    <div class="cms-draggable cms-draggable-1" id="target"></div>
                </div>
            </div>
        `;
        const target = document.getElementById('target') as HTMLElement;
        setElementData(target, 'cms', [
            { type: 'plugin', plugin_type: 'GridPlugin' } as PluginOptions,
        ]);
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('rejects when item has no plugin descriptor', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
        });
        const item = makeDraggable('cms-draggable-7'); // no data
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('rejects when item type is not in target plugin_restriction', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
            plugin_restriction: ['ColumnPlugin'],
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('allows when item type matches target plugin_restriction', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
            plugin_restriction: ['TextPlugin', 'ImagePlugin'],
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        expect(canDropAsChild(target, item)).toBe(true);
    });

    it('allows when target has empty plugin_restriction (no constraint)', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
            plugin_restriction: [],
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
        });
        expect(canDropAsChild(target, item)).toBe(true);
    });

    it('rejects when target type is not in item plugin_parent_restriction', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'ColumnPlugin',
            plugin_parent_restriction: ['RowPlugin'],
        });
        expect(canDropAsChild(target, item)).toBe(false);
    });

    it('allows when target type is in item plugin_parent_restriction', () => {
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'RowPlugin',
            plugin_restriction: ['ColumnPlugin'],
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'ColumnPlugin',
            plugin_parent_restriction: ['RowPlugin'],
        });
        expect(canDropAsChild(target, item)).toBe(true);
    });

    it('drops the special "0" entry from plugin_parent_restriction', () => {
        // Legacy treats "0" as a marker (PlaceholderPlugin parent
        // restriction quirk). Filter it out before applying the rule.
        const target = makeDraggable('cms-draggable-1', {
            type: 'plugin',
            plugin_type: 'GridPlugin',
        });
        const item = makeDraggable('cms-draggable-7', {
            type: 'plugin',
            plugin_type: 'TextPlugin',
            plugin_parent_restriction: ['0'],
        });
        // "0" filtered → effectively no restriction → allowed
        expect(canDropAsChild(target, item)).toBe(true);
    });

    it('falls back to placeholder data when target has no plugin descriptor', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-1" id="target"></div>
                </div>
            </div>
            <div class="cms-placeholder cms-placeholder-1" id="ph"></div>
        `;
        const target = document.getElementById('target') as HTMLElement;
        // Target has no data on it — fallback should look up the placeholder.
        const placeholder = document.getElementById('ph') as HTMLElement;
        setPlaceholderData(placeholder, {
            type: 'placeholder',
            plugin_type: 'PlaceholderPlugin',
            plugin_restriction: ['TextPlugin'],
        });
        const item = document.createElement('div');
        item.className = 'cms-draggable cms-draggable-7';
        setElementData(item, 'cms', [
            { type: 'plugin', plugin_type: 'TextPlugin' } as PluginOptions,
        ]);
        expect(canDropAsChild(target, item)).toBe(true);

        // Other plugin type → blocked by placeholder restriction.
        setElementData(item, 'cms', [
            { type: 'plugin', plugin_type: 'ImagePlugin' } as PluginOptions,
        ]);
        expect(canDropAsChild(target, item)).toBe(false);
    });
});

// ────────────────────────────────────────────────────────────────────
// onDrop
// ────────────────────────────────────────────────────────────────────

describe('ui/dnd — onDrop', () => {
    function buildTwoPlaceholders(): {
        item: HTMLElement;
        listA: HTMLElement;
        listB: HTMLElement;
    } {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables" id="listA">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem">drag 7</div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables" id="listB">
                    <div class="cms-draggable cms-draggable-8">
                        <div class="cms-dragitem">drag 8</div>
                    </div>
                </div>
            </div>
        `;
        return {
            item: document.querySelector<HTMLElement>('.cms-draggable-7')!,
            listA: document.getElementById('listA') as HTMLElement,
            listB: document.getElementById('listB') as HTMLElement,
        };
    }

    it('child kind: appends item into reference’s children list', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables" id="listA">
                    <div class="cms-draggable cms-draggable-1" id="parent">
                        <div class="cms-dragitem">parent</div>
                        <div class="cms-draggables" id="parentChildren"></div>
                    </div>
                    <div class="cms-draggable cms-draggable-7" id="item">
                        <div class="cms-dragitem">item</div>
                    </div>
                </div>
            </div>
        `;
        const item = document.getElementById('item') as HTMLElement;
        const parent = document.getElementById('parent') as HTMLElement;
        onDrop({ item, kind: 'child', reference: parent, anchor: parent });
        const list = document.getElementById('parentChildren')!;
        expect(list.children.length).toBe(1);
        expect((list.children[0] as HTMLElement).id).toBe('item');
    });

    it('child kind: creates a children list if none exists', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-1" id="parent">
                        <div class="cms-dragitem">parent</div>
                    </div>
                    <div class="cms-draggable cms-draggable-7" id="item">
                        <div class="cms-dragitem">item</div>
                    </div>
                </div>
            </div>
        `;
        const item = document.getElementById('item') as HTMLElement;
        const parent = document.getElementById('parent') as HTMLElement;
        onDrop({ item, kind: 'child', reference: parent, anchor: parent });
        const list = parent.querySelector<HTMLElement>(
            ':scope > .cms-draggables',
        );
        expect(list).not.toBeNull();
        expect(list!.children.length).toBe(1);
    });

    it('sibling-before kind: inserts before reference', () => {
        const { item, listB } = buildTwoPlaceholders();
        const reference = listB.querySelector<HTMLElement>('.cms-draggable-8')!;
        onDrop({ item, kind: 'sibling-before', reference, anchor: reference });
        expect(listB.children.length).toBe(2);
        expect((listB.children[0] as HTMLElement).classList.contains('cms-draggable-7')).toBe(true);
        expect((listB.children[1] as HTMLElement).classList.contains('cms-draggable-8')).toBe(true);
    });

    it('sibling-after kind: inserts after reference', () => {
        const { item, listB } = buildTwoPlaceholders();
        const reference = listB.querySelector<HTMLElement>('.cms-draggable-8')!;
        onDrop({ item, kind: 'sibling-after', reference, anchor: reference });
        expect(listB.children.length).toBe(2);
        expect((listB.children[0] as HTMLElement).classList.contains('cms-draggable-8')).toBe(true);
        expect((listB.children[1] as HTMLElement).classList.contains('cms-draggable-7')).toBe(true);
    });

    it('cross-container move: dispatches cms-plugins-update on the moved item', () => {
        const { item, listB } = buildTwoPlaceholders();
        const handler = vi.fn();
        item.addEventListener('cms-plugins-update', handler);
        const reference = listB.querySelector<HTMLElement>('.cms-draggable-8')!;
        onDrop({ item, kind: 'sibling-after', reference, anchor: reference });
        expect(handler).toHaveBeenCalledOnce();
        const detail = (handler.mock.calls[0]?.[0] as CustomEvent).detail;
        expect(detail.id).toBe(7);
    });

    it('clipboard source: dispatches cms-paste-plugin-update instead', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers">
                <div class="cms-draggables" id="clip">
                    <div class="cms-draggable cms-draggable-7" id="item">
                        <div class="cms-dragitem">clip</div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables" id="dst">
                    <div class="cms-draggable cms-draggable-8">
                        <div class="cms-dragitem">x</div>
                    </div>
                </div>
            </div>
        `;
        const item = document.getElementById('item') as HTMLElement;
        const reference = document.querySelector<HTMLElement>('.cms-draggable-8')!;

        const pasteHandler = vi.fn();
        const moveHandler = vi.fn();
        item.addEventListener('cms-paste-plugin-update', pasteHandler);
        item.addEventListener('cms-plugins-update', moveHandler);

        onDrop({ item, kind: 'sibling-after', reference, anchor: reference });
        expect(pasteHandler).toHaveBeenCalledOnce();
        expect(moveHandler).not.toHaveBeenCalled();
    });

    it('detail includes previousParentPluginId when nested move', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99" id="parent">
                        <div class="cms-dragitem">parent</div>
                        <div class="cms-draggables">
                            <div class="cms-draggable cms-draggable-7" id="item">
                                <div class="cms-dragitem">item</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables" id="dst">
                    <div class="cms-draggable cms-draggable-8">
                        <div class="cms-dragitem">x</div>
                    </div>
                </div>
            </div>
        `;
        const item = document.getElementById('item') as HTMLElement;
        const reference = document.querySelector<HTMLElement>('.cms-draggable-8')!;
        const handler = vi.fn();
        item.addEventListener('cms-plugins-update', handler);

        onDrop({ item, kind: 'sibling-after', reference, anchor: reference });
        const detail = (handler.mock.calls[0]?.[0] as CustomEvent).detail;
        expect(detail.id).toBe(7);
        expect(detail.previousParentPluginId).toBe(99);
    });
});

// ────────────────────────────────────────────────────────────────────
// setupStructureBoardDnd
// ────────────────────────────────────────────────────────────────────

describe('ui/dnd — setupStructureBoardDnd', () => {
    it('returns a no-op handle when there are no participating containers', () => {
        const handle = setupStructureBoardDnd();
        expect(typeof handle.refresh).toBe('function');
        expect(typeof handle.destroy).toBe('function');
        // Should not throw
        handle.destroy();
    });

    it('refresh() rebuilds after structure change', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem"></div>
                    </div>
                </div>
            </div>
        `;
        const handle = setupStructureBoardDnd();
        // Add a new placeholder
        const second = document.createElement('div');
        second.className = 'cms-dragarea cms-dragarea-2';
        second.innerHTML = `
            <div class="cms-draggables">
                <div class="cms-draggable cms-draggable-8">
                    <div class="cms-dragitem"></div>
                </div>
            </div>
        `;
        document.body.appendChild(second);
        // Should not throw
        expect(() => handle.refresh()).not.toThrow();
        handle.destroy();
    });

    it('destroy() detaches event listeners', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">
                        <div class="cms-dragitem"></div>
                    </div>
                </div>
            </div>
        `;
        const handle = setupStructureBoardDnd();
        handle.destroy();
        // Calling destroy twice should be a no-op
        expect(() => handle.destroy()).not.toThrow();
    });
});

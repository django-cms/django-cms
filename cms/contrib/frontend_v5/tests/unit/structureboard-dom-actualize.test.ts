import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    actualizePlaceholders,
    actualizePluginCollapseStatus,
    actualizePluginsCollapsibleStatus,
    initializeDragItemsStates,
    insertDraggable,
    relocateDraggable,
    removeDraggable,
} from '../../frontend/modules/structureboard/dom/actualize';

interface CmsTestable {
    settings?: { states?: Array<number | string>; [k: string]: unknown };
    config?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
}

function setupCms(states: Array<number | string> = []): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {},
        settings: { states: [...states] },
        _instances: [],
        _plugins: [],
    };
}

beforeEach(() => {
    document.body.innerHTML = '';
    setupCms();
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
});

describe('dom/actualize — actualizePlaceholders', () => {
    function placeholderFixture(opts: {
        empty: boolean;
        withCopyAll?: boolean;
        clipboard?: boolean;
    }): HTMLElement {
        const wrapper = document.createElement('div');
        const cls = opts.clipboard
            ? 'cms-dragarea cms-clipboard-containers'
            : 'cms-dragarea';
        wrapper.innerHTML = `
            <div class="${cls} cms-dragarea-1">
                ${
                    opts.withCopyAll
                        ? `<div class="cms-dragbar">
                              <div class="cms-submenu-item">
                                  <a data-rel="copy">Copy all</a>
                              </div>
                           </div>`
                        : ''
                }
                <div class="cms-draggables">
                    ${
                        opts.empty
                            ? ''
                            : `<div class="cms-draggable cms-draggable-7">x</div>`
                    }
                </div>
            </div>
        `;
        const placeholder = wrapper.querySelector<HTMLElement>('.cms-dragarea')!;
        document.body.appendChild(placeholder);
        return placeholder;
    }

    it('adds cms-dragarea-empty when placeholder has no draggables', () => {
        const ph = placeholderFixture({ empty: true });
        actualizePlaceholders();
        expect(ph.classList.contains('cms-dragarea-empty')).toBe(true);
    });

    it('removes cms-dragarea-empty when placeholder has draggables', () => {
        const ph = placeholderFixture({ empty: false });
        ph.classList.add('cms-dragarea-empty'); // start in stale state
        actualizePlaceholders();
        expect(ph.classList.contains('cms-dragarea-empty')).toBe(false);
    });

    it('disables the copy-all submenu item when placeholder is empty', () => {
        const ph = placeholderFixture({ empty: true, withCopyAll: true });
        actualizePlaceholders();
        const copyAll = ph.querySelector('.cms-submenu-item')!;
        expect(copyAll.classList.contains('cms-submenu-item-disabled')).toBe(true);
        expect(copyAll.querySelector('a')!.getAttribute('aria-disabled')).toBe('true');
    });

    it('enables the copy-all submenu item when placeholder has plugins', () => {
        const ph = placeholderFixture({ empty: false, withCopyAll: true });
        const copyAll = ph.querySelector('.cms-submenu-item')!;
        copyAll.classList.add('cms-submenu-item-disabled');
        copyAll.querySelector('a')!.setAttribute('aria-disabled', 'true');
        actualizePlaceholders();
        expect(copyAll.classList.contains('cms-submenu-item-disabled')).toBe(false);
        expect(copyAll.querySelector('a')!.hasAttribute('aria-disabled')).toBe(false);
    });

    it('skips clipboard containers (the :not selector)', () => {
        const ph = placeholderFixture({ empty: true, clipboard: true });
        actualizePlaceholders();
        expect(ph.classList.contains('cms-dragarea-empty')).toBe(false);
    });

    it('moves the floating add-plugin-placeholder back to last child', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-add-plugin-placeholder">marker</div>
                    <div class="cms-draggable cms-draggable-7">x</div>
                    <div class="cms-draggable cms-draggable-8">y</div>
                </div>
            </div>
        `;
        actualizePlaceholders();
        const indicator = document.querySelector('.cms-add-plugin-placeholder')!;
        expect(indicator.parentElement!.lastElementChild).toBe(indicator);
    });
});

describe('dom/actualize — actualizePluginCollapseStatus', () => {
    function draggableWithChild(id: number): HTMLElement {
        const el = document.createElement('div');
        el.innerHTML = `
            <div class="cms-draggable cms-draggable-${id}">
                <div class="cms-dragitem"></div>
                <div class="cms-collapsable-container cms-hidden"></div>
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-99"></div>
                </div>
            </div>
        `;
        document.body.appendChild(el.firstElementChild!);
        return document.querySelector<HTMLElement>(`.cms-draggable-${id}`)!;
    }

    it('expands a draggable whose id is in CMS.settings.states', () => {
        setupCms([7]);
        const el = draggableWithChild(7);
        actualizePluginCollapseStatus(7);
        expect(
            el.querySelector('.cms-collapsable-container')!.classList.contains('cms-hidden'),
        ).toBe(false);
        expect(
            el.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded'),
        ).toBe(true);
    });

    it('does nothing when the id is NOT in states', () => {
        setupCms([99]);
        const el = draggableWithChild(7);
        actualizePluginCollapseStatus(7);
        expect(
            el.querySelector('.cms-collapsable-container')!.classList.contains('cms-hidden'),
        ).toBe(true);
        expect(
            el.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded'),
        ).toBe(false);
    });

    it('does nothing when the draggable has no children to expand', () => {
        setupCms([7]);
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-dragitem"></div>
            </div>
        `;
        actualizePluginCollapseStatus(7);
        const el = document.querySelector<HTMLElement>('.cms-draggable-7')!;
        expect(el.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded')).toBe(
            false,
        );
    });

    it('coerces id types when comparing (string vs number)', () => {
        setupCms(['7']);
        const el = draggableWithChild(7);
        actualizePluginCollapseStatus(7);
        expect(
            el.querySelector('.cms-collapsable-container')!.classList.contains('cms-hidden'),
        ).toBe(false);
    });

    it('returns early when the draggable element does not exist', () => {
        setupCms([7]);
        // Should not throw
        expect(() => actualizePluginCollapseStatus(7)).not.toThrow();
    });
});

describe('dom/actualize — actualizePluginsCollapsibleStatus', () => {
    it('adds cms-dragitem-collapsable when children exist', () => {
        document.body.innerHTML = `
            <div class="cms-draggable">
                <div class="cms-dragitem"></div>
                <div class="cms-draggables">
                    <div class="cms-draggable">child</div>
                </div>
            </div>
        `;
        const lists = document.querySelectorAll('.cms-draggables');
        actualizePluginsCollapsibleStatus(lists);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-collapsable'),
        ).toBe(true);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded'),
        ).toBe(true);
    });

    it('removes cms-dragitem-collapsable when children are gone', () => {
        document.body.innerHTML = `
            <div class="cms-draggable">
                <div class="cms-dragitem cms-dragitem-collapsable"></div>
                <div class="cms-draggables"></div>
            </div>
        `;
        const lists = document.querySelectorAll('.cms-draggables');
        actualizePluginsCollapsibleStatus(lists);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-collapsable'),
        ).toBe(false);
    });

    it('does NOT add cms-dragitem-expanded when all children are cms-hidden', () => {
        document.body.innerHTML = `
            <div class="cms-draggable">
                <div class="cms-dragitem"></div>
                <div class="cms-draggables">
                    <div class="cms-draggable cms-hidden">child</div>
                </div>
            </div>
        `;
        const lists = document.querySelectorAll('.cms-draggables');
        actualizePluginsCollapsibleStatus(lists);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-collapsable'),
        ).toBe(true);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded'),
        ).toBe(false);
    });
});

describe('dom/actualize — initializeDragItemsStates', () => {
    it('dedupes states while preserving order (Set-based, not legacy sort)', () => {
        setupCms([3, 1, 3, 2, 1]);
        initializeDragItemsStates();
        const states = (
            window as unknown as { CMS: { settings: { states: Array<number | string> } } }
        ).CMS.settings.states;
        expect(states).toEqual([3, 1, 2]);
    });

    it('expands draggables whose id is in states AND has nested children', () => {
        setupCms([7]);
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-dragitem"></div>
                <div class="cms-collapsable-container cms-hidden">
                    <div class="cms-draggable cms-draggable-99"></div>
                </div>
            </div>
        `;
        initializeDragItemsStates();
        expect(
            document
                .querySelector('.cms-collapsable-container')!
                .classList.contains('cms-hidden'),
        ).toBe(false);
        expect(
            document.querySelector('.cms-dragitem')!.classList.contains('cms-dragitem-expanded'),
        ).toBe(true);
    });

    it('skips ids whose collapsable-container has no nested draggables', () => {
        setupCms([7]);
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-dragitem"></div>
                <div class="cms-collapsable-container cms-hidden"></div>
            </div>
        `;
        initializeDragItemsStates();
        expect(
            document
                .querySelector('.cms-collapsable-container')!
                .classList.contains('cms-hidden'),
        ).toBe(true);
    });

    it('handles empty states array gracefully', () => {
        setupCms([]);
        expect(() => initializeDragItemsStates()).not.toThrow();
    });
});

describe('dom/actualize — insertDraggable', () => {
    it('appends new draggable HTML into the placeholder list', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        const inserted = insertDraggable(
            1,
            '<div class="cms-draggable cms-draggable-99">new</div>',
        );
        expect(inserted).not.toBeNull();
        expect(inserted!.classList.contains('cms-draggable-99')).toBe(true);
        expect(document.querySelectorAll('.cms-draggable').length).toBe(1);
    });

    it('returns null when the target placeholder is missing', () => {
        document.body.innerHTML = '';
        expect(insertDraggable(99, '<div></div>')).toBeNull();
    });

    it('returns null when the placeholder has no .cms-draggables list', () => {
        document.body.innerHTML = `<div class="cms-dragarea cms-dragarea-1"></div>`;
        expect(
            insertDraggable(1, '<div class="cms-draggable">x</div>'),
        ).toBeNull();
    });
});

describe('dom/actualize — relocateDraggable', () => {
    function multiPlaceholderFixture(): void {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">7</div>
                    <div class="cms-draggable cms-draggable-8">8</div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
    }

    it('moves the draggable from one placeholder to another (no order)', () => {
        multiPlaceholderFixture();
        const result = relocateDraggable(7, 2, undefined);
        expect(result).not.toBeNull();
        const dst = document.querySelector('.cms-dragarea-2 .cms-draggables')!;
        expect(dst.children.length).toBe(1);
        expect((dst.children[0] as HTMLElement).classList.contains('cms-draggable-7')).toBe(true);
    });

    it('uses pluginOrder to insert at the correct position', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-A">A</div>
                    <div class="cms-draggable cms-draggable-C">C</div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">7</div>
                </div>
            </div>
        `;
        // pluginOrder: B should land between A and C
        relocateDraggable(7, 1, ['A', 7, 'C']);
        const list = document.querySelector('.cms-dragarea-1 .cms-draggables')!;
        const ids = Array.from(list.children).map(
            (el) => (el as HTMLElement).className,
        );
        expect(ids[0]).toContain('cms-draggable-A');
        expect(ids[1]).toContain('cms-draggable-7');
        expect(ids[2]).toContain('cms-draggable-C');
    });

    it('inserts at the front when pluginOrder index is 0', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-A">A</div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">7</div>
                </div>
            </div>
        `;
        relocateDraggable(7, 1, [7, 'A']);
        const list = document.querySelector('.cms-dragarea-1 .cms-draggables')!;
        expect((list.children[0] as HTMLElement).classList.contains('cms-draggable-7')).toBe(true);
    });

    it('clones a clipboard original (leaves source in place)', () => {
        document.body.innerHTML = `
            <div class="cms-clipboard-containers cms-dragarea-clip">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7 cms-draggable-from-clipboard">7</div>
                </div>
            </div>
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
        const result = relocateDraggable(7, 2, undefined);
        expect(result).not.toBeNull();
        // Source still in clipboard
        expect(
            document.querySelectorAll(
                '.cms-clipboard-containers .cms-draggable-7',
            ).length,
        ).toBe(1);
        // Destination got a copy
        expect(
            document.querySelectorAll('.cms-dragarea-2 .cms-draggable-7').length,
        ).toBe(1);
    });

    it('returns null when the source plugin does not exist', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-2">
                <div class="cms-draggables"></div>
            </div>
        `;
        expect(relocateDraggable(99, 2, undefined)).toBeNull();
    });

    it('returns null when the target placeholder is missing', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables">
                    <div class="cms-draggable cms-draggable-7">7</div>
                </div>
            </div>
        `;
        expect(relocateDraggable(7, 99, undefined)).toBeNull();
    });
});

describe('dom/actualize — removeDraggable', () => {
    it('removes the draggable wrapper and reports the id', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">7</div>
        `;
        const removed = removeDraggable(7);
        expect(removed).toEqual([7]);
        expect(document.querySelector('.cms-draggable-7')).toBeNull();
    });

    it('reports descendant ids that were removed along with the wrapper', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-draggable cms-draggable-8">
                    <div class="cms-draggable cms-draggable-9"></div>
                </div>
            </div>
        `;
        const removed = removeDraggable(7);
        expect(removed).toContain(7);
        expect(removed).toContain(8);
        expect(removed).toContain(9);
        expect(document.querySelector('.cms-draggable')).toBeNull();
    });

    it('also removes rendered .cms-plugin-<id> nodes', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7"></div>
            <div class="cms-plugin cms-plugin-7">rendered</div>
            <div class="cms-plugin cms-plugin-7">rendered2</div>
            <div class="cms-plugin cms-plugin-99">other</div>
        `;
        removeDraggable(7);
        expect(document.querySelectorAll('.cms-plugin-7').length).toBe(0);
        expect(document.querySelectorAll('.cms-plugin-99').length).toBe(1);
    });

    it('removes the <script data-cms-plugin> JSON blob', () => {
        document.body.innerHTML = `
            <div class="cms-draggable cms-draggable-7"></div>
            <script data-cms-plugin id="cms-plugin-7" type="application/json">{}</script>
            <script data-cms-plugin id="cms-plugin-99" type="application/json">{}</script>
        `;
        removeDraggable(7);
        expect(document.getElementById('cms-plugin-7')).toBeNull();
        expect(document.getElementById('cms-plugin-99')).not.toBeNull();
    });

    it('returns the id even when the draggable does not exist', () => {
        const removed = removeDraggable(7);
        expect(removed).toEqual([7]);
    });
});

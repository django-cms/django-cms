import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    filterPluginsList,
    getPossibleChildClasses,
    removeAddPluginPlaceholder,
    setupAddPluginModal,
    setupQuickSearch,
    updateWithMostUsedPlugins,
} from '../../frontend/modules/plugins/ui/picker';
import { _resetRegistryForTest, bumpUsageCount } from '../../frontend/modules/plugins/registry';
import type { PluginInstance } from '../../frontend/modules/plugins/types';

/**
 * Build a placeholder fixture with an add-plugin trigger, sibling
 * picker (with a quicksearch row), and a server-rendered child-classes
 * template (`#cms-plugin-child-classes-{id}`) carrying the type list.
 */
function fixture(
    opts: {
        children?: string;
        restriction?: string[];
        placeholderId?: number;
    } = {},
) {
    const placeholderId = opts.placeholderId ?? 7;
    const children =
        opts.children ??
        `
            <div class="cms-submenu-item cms-submenu-item-title"><span>Generic</span></div>
            <div class="cms-submenu-item">
                <a href="#TextPlugin" data-rel="add">Text</a>
            </div>
            <div class="cms-submenu-item">
                <a href="#PicturePlugin" data-rel="add">Picture</a>
            </div>
            <div class="cms-submenu-item">
                <a href="#LinkPlugin" data-rel="add">Link</a>
            </div>
        `;
    document.body.innerHTML = `
        <div class="cms-dragarea cms-dragarea-${placeholderId}">
            <div class="cms-dragbar cms-dragbar-${placeholderId}">
                <button class="cms-submenu-add" id="trigger">+</button>
                <div class="cms-plugin-picker">
                    <div class="cms-quicksearch"><input type="search" /></div>
                </div>
            </div>
            <div class="cms-draggables"></div>
        </div>
        <template id="cms-plugin-child-classes-${placeholderId}-marker"></template>
        <div id="cms-plugin-child-classes-${placeholderId}" style="display:none">
            ${children}
        </div>
    `;
    return {
        trigger: document.getElementById('trigger') as HTMLElement,
        picker: document.querySelector<HTMLElement>('.cms-plugin-picker')!,
        dragarea: document.querySelector<HTMLElement>('.cms-dragarea')!,
        draggables: document.querySelector<HTMLElement>('.cms-draggables')!,
        placeholderId,
    };
}

function makePlugin(restriction?: string[]): PluginInstance & {
    addPlugin: ReturnType<typeof vi.fn>;
} {
    return {
        options: {
            type: 'placeholder',
            placeholder_id: 7,
            ...(restriction ? { plugin_restriction: restriction } : {}),
        },
        addPlugin: vi.fn(),
    };
}

describe('picker — getPossibleChildClasses', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        _resetRegistryForTest();
    });

    it('returns the cloned items from the server template', () => {
        const { trigger } = fixture();
        const items = getPossibleChildClasses(makePlugin(), trigger);
        // 1 title + 3 plugin rows.
        expect(items).toHaveLength(4);
        expect(items[0]?.classList.contains('cms-submenu-item-title')).toBe(true);
    });

    it('filters by plugin_restriction', () => {
        const { trigger } = fixture();
        const items = getPossibleChildClasses(
            makePlugin(['#TextPlugin']),
            trigger,
        );
        // Title + only the Text row.
        const links = items
            .map((i) => i.querySelector('a')?.getAttribute('href'))
            .filter(Boolean);
        expect(links).toEqual(['#TextPlugin']);
    });

    it('drops orphan section titles when restriction empties a section', () => {
        const { trigger } = fixture({
            children: `
                <div class="cms-submenu-item cms-submenu-item-title"><span>Section A</span></div>
                <div class="cms-submenu-item"><a href="#OnlyA" data-rel="add">Only A</a></div>
                <div class="cms-submenu-item cms-submenu-item-title"><span>Section B</span></div>
                <div class="cms-submenu-item"><a href="#OnlyB" data-rel="add">Only B</a></div>
            `,
        });
        const items = getPossibleChildClasses(
            makePlugin(['#OnlyA']),
            trigger,
        );
        const labels = items.map(
            (i) => i.querySelector('span')?.textContent ?? i.querySelector('a')?.textContent,
        );
        expect(labels).toEqual(['Section A', 'Only A']);
    });

    it('returns [] when no template exists for the placeholder', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-99">
                <button class="cms-submenu-add" id="t">+</button>
            </div>
        `;
        const items = getPossibleChildClasses(
            makePlugin(),
            document.getElementById('t') as HTMLElement,
        );
        expect(items).toEqual([]);
    });
});

describe('picker — updateWithMostUsedPlugins', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        _resetRegistryForTest();
    });

    it('is a no-op when picker has fewer items than the cap', () => {
        const { picker } = fixture(); // 3 selectable items
        const before = picker.querySelectorAll('.cms-submenu-item').length;
        updateWithMostUsedPlugins(picker);
        const after = picker.querySelectorAll('.cms-submenu-item').length;
        expect(after).toBe(before);
        expect(picker.querySelectorAll('[data-cms-most-used]').length).toBe(0);
    });

    it('inserts up to N most-used clones after the quicksearch row', () => {
        // Need >5 selectable items to trigger the most-used path.
        const { picker } = fixture({
            children: `
                <div class="cms-submenu-item"><a href="#A">A</a></div>
                <div class="cms-submenu-item"><a href="#B">B</a></div>
                <div class="cms-submenu-item"><a href="#C">C</a></div>
                <div class="cms-submenu-item"><a href="#D">D</a></div>
                <div class="cms-submenu-item"><a href="#E">E</a></div>
                <div class="cms-submenu-item"><a href="#F">F</a></div>
            `,
        });
        // Move the candidate items from the template into the picker
        // so updateWithMostUsedPlugins finds them by href.
        const items = document.querySelectorAll(
            '#cms-plugin-child-classes-7 .cms-submenu-item',
        );
        items.forEach((el) => picker.appendChild(el.cloneNode(true)));

        bumpUsageCount('#A');
        bumpUsageCount('#A');
        bumpUsageCount('#B');

        updateWithMostUsedPlugins(picker);

        const mostUsed = picker.querySelectorAll('[data-cms-most-used]');
        // 2 used items + 1 section title.
        expect(mostUsed.length).toBe(3);
        expect(
            mostUsed[0]?.classList.contains('cms-submenu-item-title'),
        ).toBe(true);
    });
});

describe('picker — filterPluginsList', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('hides items whose text does not contain the query', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-picker">
                <div class="cms-submenu-item cms-submenu-item-title"><span>Generic</span></div>
                <div class="cms-submenu-item"><a>Text Plugin</a></div>
                <div class="cms-submenu-item"><a>Picture Plugin</a></div>
                <div class="cms-submenu-item"><a>Link Plugin</a></div>
            </div>
        `;
        const list = document.querySelector<HTMLElement>('.cms-plugin-picker')!;
        filterPluginsList(list, 'pict');
        const items = Array.from(
            list.querySelectorAll<HTMLElement>('.cms-submenu-item'),
        );
        const visibleHrefs = items
            .filter(
                (el) =>
                    !el.classList.contains('cms-hidden') &&
                    !el.classList.contains('cms-submenu-item-title'),
            )
            .map((el) => el.textContent?.trim());
        expect(visibleHrefs).toEqual(['Picture Plugin']);
    });

    it('shows everything when the query is empty', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-picker">
                <div class="cms-submenu-item"><a>Text</a></div>
                <div class="cms-submenu-item cms-hidden"><a>Hidden</a></div>
            </div>
        `;
        const list = document.querySelector<HTMLElement>('.cms-plugin-picker')!;
        filterPluginsList(list, '');
        const items = Array.from(
            list.querySelectorAll<HTMLElement>('.cms-submenu-item'),
        );
        expect(items.every((el) => !el.classList.contains('cms-hidden'))).toBe(true);
    });

    it('hides the "most used" rows during a search', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-picker">
                <div class="cms-submenu-item" data-cms-most-used><a>Text</a></div>
                <div class="cms-submenu-item"><a>Text Plugin</a></div>
                <div class="cms-submenu-item"><a>Picture Plugin</a></div>
            </div>
        `;
        const list = document.querySelector<HTMLElement>('.cms-plugin-picker')!;
        filterPluginsList(list, 'text');
        const mostUsed = list.querySelector<HTMLElement>('[data-cms-most-used]');
        expect(mostUsed?.classList.contains('cms-hidden')).toBe(true);
        const allItems = Array.from(
            list.querySelectorAll<HTMLElement>('.cms-submenu-item:not([data-cms-most-used])'),
        );
        const visible = allItems.filter((el) => !el.classList.contains('cms-hidden'));
        expect(visible.map((el) => el.textContent?.trim())).toEqual(['Text Plugin']);
    });

    it('hides a section title whose section has no visible items', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-picker">
                <div class="cms-submenu-item cms-submenu-item-title"><span>Empty</span></div>
                <div class="cms-submenu-item"><a>Foo</a></div>
                <div class="cms-submenu-item cms-submenu-item-title"><span>Match</span></div>
                <div class="cms-submenu-item"><a>Match here</a></div>
            </div>
        `;
        const list = document.querySelector<HTMLElement>('.cms-plugin-picker')!;
        filterPluginsList(list, 'match');
        const titles = Array.from(
            list.querySelectorAll<HTMLElement>('.cms-submenu-item-title'),
        );
        expect(titles[0]?.classList.contains('cms-hidden')).toBe(true);
        expect(titles[1]?.classList.contains('cms-hidden')).toBe(false);
    });
});

describe('picker — removeAddPluginPlaceholder', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('removes every floating placeholder', () => {
        document.body.innerHTML = `
            <div class="cms-add-plugin-placeholder">a</div>
            <div class="cms-add-plugin-placeholder">b</div>
            <div class="cms-other"></div>
        `;
        removeAddPluginPlaceholder();
        expect(document.querySelectorAll('.cms-add-plugin-placeholder').length).toBe(0);
        expect(document.querySelectorAll('.cms-other').length).toBe(1);
    });
});

describe('picker — setupAddPluginModal: single-choice fast path', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        _resetRegistryForTest();
    });

    it('skips the modal and calls addPlugin directly when only one type is valid', () => {
        const { trigger } = fixture({
            children: `
                <div class="cms-submenu-item cms-submenu-item-title"><span>Only one</span></div>
                <div class="cms-submenu-item">
                    <a href="#OnlyText" data-rel="add" data-add-form="false">Only Text</a>
                </div>
            `,
        });
        const plugin = makePlugin();
        setupAddPluginModal(plugin, trigger);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(plugin.addPlugin).toHaveBeenCalledWith(
            'OnlyText',
            'Only Text',
            undefined,
            false,
        );
    });

    it('returns false and does nothing when the trigger is disabled', () => {
        const { trigger } = fixture();
        trigger.classList.add('cms-btn-disabled');
        const plugin = makePlugin();
        const wired = setupAddPluginModal(plugin, trigger);
        expect(wired).toBe(false);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(plugin.addPlugin).not.toHaveBeenCalled();
    });
});

describe('picker — setupAddPluginModal: multi-choice', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        _resetRegistryForTest();
        delete (window as { CMS?: unknown }).CMS;
    });

    it('opens the modal with a cloned + decorated picker', () => {
        // Fake CMS.Modal: capture the open() options for inspection.
        const opens: Array<{ html: HTMLElement | string }> = [];
        class FakeModal {
            open(opts: { html: HTMLElement | string }) {
                opens.push(opts);
            }
        }
        (window as unknown as { CMS: { Modal: typeof FakeModal } }).CMS = {
            Modal: FakeModal,
        };

        const { trigger, picker } = fixture();
        const plugin = makePlugin();
        setupAddPluginModal(plugin, trigger);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(opens.length).toBe(1);
        const html = opens[0]?.html as HTMLElement;
        expect(html).toBeInstanceOf(HTMLElement);
        // Clone, not the original.
        expect(html).not.toBe(picker);
        // Cloned items should include the quicksearch + child classes
        // appended to it.
        expect(html.querySelectorAll('.cms-submenu-item').length).toBeGreaterThan(0);
    });

    it('inserts an add-plugin placeholder into the dragarea on modal-loaded', async () => {
        const { Helpers } = await import('../../frontend/modules/cms-base');
        class FakeModal {
            open() {
                /* noop — we'll fire modal-loaded ourselves */
            }
        }
        (window as unknown as {
            CMS: { Modal: typeof FakeModal; config: { lang: { addPluginPlaceholder: string } } };
        }).CMS = {
            Modal: FakeModal,
            config: { lang: { addPluginPlaceholder: 'Drop here' } },
        };
        const { trigger } = fixture();
        const plugin = makePlugin();
        setupAddPluginModal(plugin, trigger);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        // Find the modal instance the picker just constructed (only one was created).
        // Track via the dispatch mechanism — pretend the modal we instantiated
        // is the payload's instance.
        // The picker keeps a closed-over reference; we can't get it directly.
        // Instead, dispatch with the actual modal instance — the picker
        // tracks by identity. Find the most-recently constructed FakeModal
        // by stashing it from the constructor.
        // Easier path: dispatch with `instance: any` and rely on
        // identity-check failing → no placeholder. To verify the loaded
        // path we need a wired instance. Use a constructor side-effect:
        let captured: FakeModal | null = null;
        class CapturingModal extends FakeModal {
            constructor() {
                super();
                captured = this;
            }
        }
        (window as unknown as { CMS: { Modal: typeof CapturingModal } }).CMS.Modal =
            CapturingModal;
        // Re-arm: open another picker via a fresh trigger.
        const trigger2 = document.querySelector<HTMLElement>('#trigger');
        // The previous setupAddPluginModal cached `modal` — open again with
        // a new instance via fresh wiring.
        const trigger3 = document.createElement('button');
        trigger3.className = 'cms-submenu-add';
        trigger3.id = 't3';
        trigger.parentElement?.appendChild(trigger3);
        const plugin2 = makePlugin();
        setupAddPluginModal(plugin2, trigger3);
        trigger3.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(captured).not.toBeNull();
        // No placeholder yet.
        expect(document.querySelectorAll('.cms-add-plugin-placeholder').length).toBe(0);
        // Fire modal-loaded with the matching instance.
        Helpers.dispatchEvent('modal-loaded', { instance: captured });
        const placeholders = document.querySelectorAll('.cms-add-plugin-placeholder');
        expect(placeholders.length).toBe(1);
        expect(placeholders[0]?.textContent).toBe('Drop here');
        void trigger2;
    });

    it('falls through to no-op (no error, no addPlugin call) when CMS.Modal is missing', () => {
        const { trigger } = fixture();
        const plugin = makePlugin();
        setupAddPluginModal(plugin, trigger);
        expect(() =>
            trigger.dispatchEvent(new Event('pointerup', { bubbles: true })),
        ).not.toThrow();
        expect(plugin.addPlugin).not.toHaveBeenCalled();
    });
});

describe('picker — setupQuickSearch', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });
    afterEach(() => {
        vi.useRealTimers();
        document.body.innerHTML = '';
    });

    it('debounces input → filterPluginsList', () => {
        document.body.innerHTML = `
            <div class="cms-plugin-picker">
                <div class="cms-quicksearch"><input type="search" /></div>
                <div class="cms-submenu-item"><a>Text Plugin</a></div>
                <div class="cms-submenu-item"><a>Picture Plugin</a></div>
            </div>
        `;
        const picker = document.querySelector<HTMLElement>('.cms-plugin-picker')!;
        const input = picker.querySelector<HTMLInputElement>('input')!;
        const trigger = document.createElement('button');
        const plugin = makePlugin();
        setupQuickSearch(plugin, trigger, picker);
        input.value = 'pict';
        input.dispatchEvent(new Event('keyup'));
        vi.advanceTimersByTime(200);
        const items = Array.from(
            picker.querySelectorAll<HTMLElement>('.cms-submenu-item'),
        );
        const visible = items
            .filter((el) => !el.classList.contains('cms-hidden'))
            .map((el) => el.textContent?.trim());
        expect(visible).toEqual(['Picture Plugin']);
    });
});

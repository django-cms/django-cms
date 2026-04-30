import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    delegateAction,
    hideSettingsMenu,
    setupSettingsMenu,
    showSettingsMenu,
} from '../../frontend/modules/plugins/ui/menu';
import {
    _resetRegistryForTest,
    getUsageMap,
} from '../../frontend/modules/plugins/registry';
import type { PluginInstance } from '../../frontend/modules/plugins/types';

/**
 * Build a minimal dragbar fixture with trigger + dropdown + actions.
 */
function fixture(opts: { withQuicksearch?: boolean } = {}) {
    document.body.innerHTML = `
        <div class="cms-dragarea cms-dragarea-1">
            <div class="cms-dragbar cms-dragbar-1">
                <span class="cms-dragbar-title">Title</span>
                <button class="cms-submenu-btn" id="trigger">…</button>
                <div class="cms-submenu-dropdown-settings cms-submenu-dropdown" style="display:none">
                    <ul>
                        <li class="cms-submenu-item">
                            <a id="edit-action" href="#" data-rel="edit">Edit</a>
                        </li>
                        <li class="cms-submenu-item">
                            <a id="copy-action" href="#" data-rel="copy">Copy</a>
                        </li>
                        <li class="cms-submenu-item cms-submenu-item-disabled">
                            <a id="paste-action" href="#" data-rel="paste">Paste</a>
                        </li>
                        <li class="cms-submenu-item">
                            <a id="cut-action" href="#" data-rel="cut">Cut</a>
                        </li>
                        <li class="cms-submenu-item">
                            <a id="delete-action" href="#" data-rel="delete">Delete</a>
                        </li>
                        <li class="cms-submenu-item">
                            <a id="add-action" href="#TextPlugin" data-rel="add">Add Text</a>
                        </li>
                    </ul>
                </div>
                ${
                    opts.withQuicksearch
                        ? '<div class="cms-quicksearch"><input type="search" /></div>'
                        : ''
                }
            </div>
        </div>
    `;
    return {
        trigger: document.getElementById('trigger')!,
        dropdown: document.querySelector<HTMLElement>('.cms-submenu-dropdown-settings')!,
    };
}

function makePlugin(): PluginInstance & {
    addPlugin: ReturnType<typeof vi.fn>;
    editPlugin: ReturnType<typeof vi.fn>;
    copyPlugin: ReturnType<typeof vi.fn>;
    cutPlugin: ReturnType<typeof vi.fn>;
    pastePlugin: ReturnType<typeof vi.fn>;
    deletePlugin: ReturnType<typeof vi.fn>;
} {
    return {
        options: {
            type: 'plugin',
            plugin_id: 1,
            plugin_name: 'Sample',
            urls: {
                edit_plugin: '/edit/',
                delete_plugin: '/delete/',
            },
        },
        addPlugin: vi.fn(),
        editPlugin: vi.fn(),
        copyPlugin: vi.fn(),
        cutPlugin: vi.fn(),
        pastePlugin: vi.fn(),
        deletePlugin: vi.fn(),
    };
}

describe('settings menu — toggle', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('first pointerup opens the dropdown and marks the trigger active', () => {
        const { trigger, dropdown } = fixture();
        setupSettingsMenu(makePlugin(), trigger);
        expect(trigger.classList.contains('cms-btn-active')).toBe(false);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(trigger.classList.contains('cms-btn-active')).toBe(true);
        expect(
            dropdown.classList.contains('cms-submenu-dropdown-settings--open'),
        ).toBe(true);
    });

    it('second pointerup closes the dropdown', () => {
        const { trigger, dropdown } = fixture();
        setupSettingsMenu(makePlugin(), trigger);
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(trigger.classList.contains('cms-btn-active')).toBe(false);
        expect(
            dropdown.classList.contains('cms-submenu-dropdown-settings--open'),
        ).toBe(false);
    });

    it('opening a second menu hides the first', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea">
                <button class="cms-submenu-btn" id="t1"></button>
                <div class="cms-submenu-dropdown-settings cms-submenu-dropdown" style="display:none"></div>
                <button class="cms-submenu-btn" id="t2"></button>
                <div class="cms-submenu-dropdown-settings cms-submenu-dropdown" style="display:none"></div>
            </div>
        `;
        const t1 = document.getElementById('t1') as HTMLElement;
        const t2 = document.getElementById('t2') as HTMLElement;
        setupSettingsMenu(makePlugin(), t1);
        setupSettingsMenu(makePlugin(), t2);
        t1.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(t1.classList.contains('cms-btn-active')).toBe(true);
        t2.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(t1.classList.contains('cms-btn-active')).toBe(false);
        expect(t2.classList.contains('cms-btn-active')).toBe(true);
    });
});

describe('settings menu — positioning', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('uses cms-submenu-dropdown-top when there is room below', () => {
        const { trigger, dropdown } = fixture();
        // Force a small dropdown so room-below is plenty.
        Object.defineProperty(dropdown, 'offsetHeight', {
            configurable: true,
            value: 50,
        });
        // Place trigger near top.
        Object.defineProperty(trigger, 'getBoundingClientRect', {
            configurable: true,
            value: () => ({ top: 10, bottom: 30, left: 0, right: 30, width: 30, height: 20 }),
        });
        showSettingsMenu(trigger, dropdown);
        expect(dropdown.classList.contains('cms-submenu-dropdown-top')).toBe(true);
        expect(dropdown.classList.contains('cms-submenu-dropdown-bottom')).toBe(false);
    });

    it('flips to cms-submenu-dropdown-bottom when no room below but room above', () => {
        const { trigger, dropdown } = fixture();
        Object.defineProperty(dropdown, 'offsetHeight', {
            configurable: true,
            value: 500,
        });
        // Trigger near bottom of viewport (jsdom innerHeight is 768).
        Object.defineProperty(trigger, 'getBoundingClientRect', {
            configurable: true,
            value: () => ({ top: 700, bottom: 720, left: 0, right: 30, width: 30, height: 20 }),
        });
        showSettingsMenu(trigger, dropdown);
        expect(dropdown.classList.contains('cms-submenu-dropdown-bottom')).toBe(true);
        expect(dropdown.classList.contains('cms-submenu-dropdown-top')).toBe(false);
    });
});

describe('settings menu — hideSettingsMenu', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('removes active state and closes dropdowns + quicksearch', () => {
        const { trigger, dropdown } = fixture({ withQuicksearch: true });
        const quicksearch = document.querySelector<HTMLElement>('.cms-quicksearch')!;
        const input = quicksearch.querySelector<HTMLInputElement>('input')!;
        input.value = 'old query';

        showSettingsMenu(trigger, dropdown);
        expect(trigger.classList.contains('cms-btn-active')).toBe(true);

        hideSettingsMenu(trigger);
        expect(trigger.classList.contains('cms-btn-active')).toBe(false);
        expect(
            dropdown.classList.contains('cms-submenu-dropdown-settings--open'),
        ).toBe(false);
        // Quicksearch visibility is governed by the legacy
        // `.cms-quicksearch { display: none }` rule once the parent panel
        // loses its `--open` modifier — no inline state to assert in jsdom.
        expect(input.value).toBe('');
    });

    it('without an arg, walks the doc for the active trigger', () => {
        const { trigger, dropdown } = fixture();
        showSettingsMenu(trigger, dropdown);
        hideSettingsMenu();
        expect(trigger.classList.contains('cms-btn-active')).toBe(false);
    });

    it('is a no-op when nothing is open', () => {
        expect(() => hideSettingsMenu()).not.toThrow();
    });
});

describe('settings menu — action delegation', () => {
    beforeEach(() => {
        _resetRegistryForTest();
    });
    afterEach(() => {
        _resetRegistryForTest();
        document.body.innerHTML = '';
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    function clickAction(plugin: ReturnType<typeof makePlugin>, id: string): void {
        const action = document.getElementById(id)!;
        const trigger = document.getElementById('trigger') as HTMLElement;
        // Build a synthetic event with target pointed at the action.
        const e = new MouseEvent('click', { bubbles: true, cancelable: true });
        Object.defineProperty(e, 'target', { value: action });
        delegateAction(plugin, trigger, e);
    }

    it('"edit" → calls plugin.editPlugin', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'edit-action');
        expect(p.editPlugin).toHaveBeenCalledWith('/edit/', 'Sample', []);
    });

    it('"copy" on enabled item → calls plugin.copyPlugin', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'copy-action');
        expect(p.copyPlugin).toHaveBeenCalledOnce();
    });

    it('"paste" on disabled item is a no-op (loader hidden, pastePlugin not called)', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'paste-action');
        expect(p.pastePlugin).not.toHaveBeenCalled();
    });

    it('"cut" → calls plugin.cutPlugin', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'cut-action');
        expect(p.cutPlugin).toHaveBeenCalledOnce();
    });

    it('"delete" → calls plugin.deletePlugin with delete URL', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'delete-action');
        expect(p.deletePlugin).toHaveBeenCalledWith('/delete/', 'Sample', []);
    });

    it('"add" → calls plugin.addPlugin and bumps usage counter', () => {
        fixture();
        const p = makePlugin();
        clickAction(p, 'add-action');
        expect(p.addPlugin).toHaveBeenCalled();
        expect(getUsageMap().TextPlugin).toBe(1);
    });

    it('closes the dropdown after dispatching', () => {
        const { trigger, dropdown } = fixture();
        setupSettingsMenu(makePlugin(), trigger);
        // Open
        trigger.dispatchEvent(new Event('pointerup', { bubbles: true }));
        expect(trigger.classList.contains('cms-btn-active')).toBe(true);
        // Click action
        const p = makePlugin();
        const action = document.getElementById('edit-action')!;
        const e = new MouseEvent('click', { bubbles: true, cancelable: true });
        Object.defineProperty(e, 'target', { value: action });
        delegateAction(p, trigger, e);
        expect(trigger.classList.contains('cms-btn-active')).toBe(false);
        expect(
            dropdown.classList.contains('cms-submenu-dropdown-settings--open'),
        ).toBe(false);
    });
});

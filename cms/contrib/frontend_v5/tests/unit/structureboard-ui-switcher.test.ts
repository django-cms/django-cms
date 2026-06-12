import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    setupModeSwitcher,
    type SwitcherHandle,
} from '../../frontend/modules/structureboard/ui/switcher';
import { _resetForTest } from '../../frontend/modules/structureboard/ui/mode';
import type { ModeContext } from '../../frontend/modules/structureboard/ui/mode';

const liveHandles: SwitcherHandle[] = [];
function track(handle: SwitcherHandle): SwitcherHandle {
    liveHandles.push(handle);
    return handle;
}

interface CmsTestable {
    config?: { mode?: string; settings?: Record<string, unknown> };
    settings?: { mode?: string };
    API?: { Helpers?: { setSettings?: ReturnType<typeof vi.fn> } };
}

function setupCms(): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: { mode: 'draft', settings: {} },
        settings: { mode: 'edit' },
        API: { Helpers: { setSettings: vi.fn() } },
    };
}

function buildContext(overrides: Partial<ModeContext> = {}): ModeContext {
    document.body.innerHTML = `
        <div id="container"></div>
        <div id="toolbar" style="width: 1000px"></div>
        <div id="switcher">
            <a class="cms-btn" href="/structure/">Structure</a>
            <a class="cms-btn" href="/edit/">Content</a>
        </div>
    `;
    return {
        container: document.getElementById('container') as HTMLElement,
        toolbar: document.getElementById('toolbar') as HTMLElement,
        html: document.documentElement,
        toolbarModeLinks: Array.from(
            document.querySelectorAll<HTMLElement>('.cms-btn'),
        ),
        win: window,
        isLoadedStructure: () => false,
        isLoadedContent: () => false,
        loadStructure: () => Promise.resolve(),
        loadContent: () => Promise.resolve(),
        ...overrides,
    };
}

function getModeLinks(): HTMLElement[] {
    return Array.from(document.querySelectorAll<HTMLElement>('.cms-btn'));
}

beforeEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    setupCms();
    _resetForTest();
});

afterEach(() => {
    while (liveHandles.length > 0) liveHandles.pop()!.destroy();
    document.body.innerHTML = '';
    document.documentElement.className = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetForTest();
    vi.restoreAllMocks();
});

describe('switcher — click handler', () => {
    it('flips mode on plain click (edit → structure)', async () => {
        const ctx = buildContext();
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));
        getModeLinks()[0]!.click();
        // show is async; await microtask
        await Promise.resolve();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('structure');
    });

    it('flips mode on plain click (structure → edit)', async () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));
        getModeLinks()[0]!.click();
        await Promise.resolve();
        expect(cms.settings!.mode).toBe('edit');
    });

    it('does nothing when all mode links are disabled', async () => {
        const ctx = buildContext();
        for (const link of getModeLinks()) {
            link.classList.add('cms-btn-disabled');
        }
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));
        getModeLinks()[0]!.click();
        await Promise.resolve();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('edit'); // unchanged
    });

    it('opens link in new tab when modifier is held', async () => {
        const ctx = buildContext();
        const open = vi.fn();
        // Override window.open
        Object.defineProperty(ctx.win, 'open', { value: open, configurable: true });
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));

        // Simulate ctrl-down
        const keydown = new KeyboardEvent('keydown', { ctrlKey: true });
        ctx.win.dispatchEvent(keydown);
        getModeLinks()[0]!.click();
        await Promise.resolve();

        expect(open).toHaveBeenCalledWith('/structure/', '_blank');
        // Mode unchanged
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('edit');
    });

    it('clears modifier flag on blur', async () => {
        const ctx = buildContext();
        const open = vi.fn();
        Object.defineProperty(ctx.win, 'open', { value: open, configurable: true });
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));

        const keydown = new KeyboardEvent('keydown', { ctrlKey: true });
        ctx.win.dispatchEvent(keydown);
        ctx.win.dispatchEvent(new Event('blur'));
        getModeLinks()[0]!.click();
        await Promise.resolve();

        expect(open).not.toHaveBeenCalled();
    });

    it('e.preventDefault is called', () => {
        const ctx = buildContext();
        track(setupModeSwitcher(ctx, { modeLinks: getModeLinks() }));
        const event = new MouseEvent('click', { bubbles: true, cancelable: true });
        getModeLinks()[0]!.dispatchEvent(event);
        expect(event.defaultPrevented).toBe(true);
    });
});

describe('switcher — keyboard shortcuts', () => {
    it('Space toggles when switcher exists and is enabled', async () => {
        const ctx = buildContext();
        track(setupModeSwitcher(ctx, {
            modeLinks: getModeLinks(),
            switcher: document.getElementById('switcher')!,
        }));
        const event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
            cancelable: true,
        });
        ctx.win.dispatchEvent(event);
        await Promise.resolve();
        expect(event.defaultPrevented).toBe(true);
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('structure');
    });

    it('Shift+Space calls onShowAndHighlight when in edit mode', async () => {
        const ctx = buildContext();
        const handler = vi.fn();
        track(setupModeSwitcher(ctx, {
            modeLinks: getModeLinks(),
            switcher: document.getElementById('switcher')!,
            onShowAndHighlight: handler,
        }));
        const event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
            shiftKey: true,
        });
        ctx.win.dispatchEvent(event);
        expect(handler).toHaveBeenCalled();
    });

    it('Space inside a text input is ignored', async () => {
        const ctx = buildContext();
        track(setupModeSwitcher(ctx, {
            modeLinks: getModeLinks(),
            switcher: document.getElementById('switcher')!,
        }));
        const input = document.createElement('input');
        document.body.appendChild(input);
        input.focus();
        const event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
        });
        Object.defineProperty(event, 'target', { value: input });
        ctx.win.dispatchEvent(event);
        await Promise.resolve();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('edit'); // unchanged
    });

    it('keyboard shortcuts not bound when switcher is disabled', async () => {
        const ctx = buildContext();
        const switcher = document.getElementById('switcher')!;
        switcher
            .querySelectorAll('.cms-btn')
            .forEach((b) => b.classList.add('cms-btn-disabled'));
        track(setupModeSwitcher(ctx, {
            modeLinks: getModeLinks(),
            switcher,
        }));
        const event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
            cancelable: true,
        });
        ctx.win.dispatchEvent(event);
        // No preventDefault (no listener bound)
        expect(event.defaultPrevented).toBe(false);
    });
});

describe('switcher — destroy()', () => {
    it('detaches all listeners', async () => {
        const ctx = buildContext();
        const handle = setupModeSwitcher(ctx, {
            modeLinks: getModeLinks(),
            switcher: document.getElementById('switcher')!,
        });
        handle.destroy();
        getModeLinks()[0]!.click();
        await Promise.resolve();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        expect(cms.settings!.mode).toBe('edit'); // unchanged
    });
});

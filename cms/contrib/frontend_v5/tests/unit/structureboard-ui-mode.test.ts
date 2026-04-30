import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _resetForTest,
    hide,
    hideBoard,
    isCondensed,
    makeCondensed,
    makeFullWidth,
    show,
    showBoard,
    toggleStructureBoard,
    type ModeContext,
} from '../../frontend/modules/structureboard/ui/mode';

interface CmsTestable {
    config?: {
        mode?: string;
        settings?: { mode?: string; structure?: string; edit?: string };
    };
    settings?: { mode?: string };
    API?: { Helpers?: { setSettings?: ReturnType<typeof vi.fn> } };
}

function setupCms(extras: Partial<CmsTestable> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            mode: 'draft',
            settings: {
                structure: '/cms/structure/',
                edit: '/cms/edit/',
            },
        },
        settings: { mode: 'edit' },
        API: { Helpers: { setSettings: vi.fn() } },
        ...extras,
    };
}

function buildContext(overrides: Partial<ModeContext> = {}): ModeContext {
    document.body.innerHTML = `
        <html><div id="container" class="cms-structure"></div>
        <div id="toolbar" style="width: 1024px"></div>
        <a class="cms-btn cms-btn-active" href="/structure/">Structure</a>
        <a class="cms-btn" href="/edit/">Content</a></html>
    `;
    document.documentElement.classList.remove(
        'cms-structure-mode-structure',
        'cms-structure-mode-content',
        'cms-overflow',
    );
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

beforeEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    setupCms();
    _resetForTest();
});

afterEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetForTest();
    vi.restoreAllMocks();
});

// ────────────────────────────────────────────────────────────────────
// show / hide
// ────────────────────────────────────────────────────────────────────

describe('mode — show', () => {
    it('returns false in live mode', async () => {
        setupCms({ config: { mode: 'live', settings: {} } });
        const ctx = buildContext();
        expect(await show(ctx)).toBe(false);
    });

    it('sets CMS.settings.mode to "structure" and persists', async () => {
        const ctx = buildContext();
        await show(ctx);
        expect(
            (window as unknown as { CMS: CmsTestable }).CMS.settings!.mode,
        ).toBe('structure');
        const helpers = (window as unknown as { CMS: CmsTestable }).CMS.API
            ?.Helpers;
        expect(helpers?.setSettings).toHaveBeenCalled();
    });

    it('awaits loadStructure before showing the board', async () => {
        const order: string[] = [];
        const ctx = buildContext({
            loadStructure: async () => {
                order.push('load');
            },
            container: (() => {
                const el = document.createElement('div');
                el.style.display = 'none';
                document.body.appendChild(el);
                return el;
            })(),
        });
        // Tap into showBoard via a side-effect: container display flips.
        await show(ctx);
        order.push('after');
        expect(order).toEqual(['load', 'after']);
        expect(ctx.container.classList.contains('cms-structure--open')).toBe(true);
    });

    it('flips html classes from content to structure mode', async () => {
        document.documentElement.classList.add('cms-structure-mode-content');
        const ctx = buildContext();
        await show(ctx);
        expect(
            document.documentElement.classList.contains(
                'cms-structure-mode-structure',
            ),
        ).toBe(true);
        expect(
            document.documentElement.classList.contains(
                'cms-structure-mode-content',
            ),
        ).toBe(false);
    });

    it('marks the first mode link as active', async () => {
        const ctx = buildContext();
        // Pre-clear active state
        for (const link of ctx.toolbarModeLinks) {
            link.classList.remove('cms-btn-active');
        }
        await show(ctx);
        expect(ctx.toolbarModeLinks[0]!.classList.contains('cms-btn-active')).toBe(
            true,
        );
        expect(ctx.toolbarModeLinks[1]!.classList.contains('cms-btn-active')).toBe(
            false,
        );
    });
});

describe('mode — hide', () => {
    it('returns false in live mode', async () => {
        setupCms({ config: { mode: 'live', settings: {} } });
        const ctx = buildContext();
        expect(await hide(ctx)).toBe(false);
    });

    it('sets CMS.settings.mode to "edit"', async () => {
        const ctx = buildContext();
        await hide(ctx);
        expect(
            (window as unknown as { CMS: CmsTestable }).CMS.settings!.mode,
        ).toBe('edit');
    });

    it('flips html classes from structure to content', async () => {
        document.documentElement.classList.add('cms-structure-mode-structure');
        const ctx = buildContext();
        await hide(ctx);
        expect(
            document.documentElement.classList.contains(
                'cms-structure-mode-content',
            ),
        ).toBe(true);
    });

    it('clears the toolbar.right inline style', async () => {
        const ctx = buildContext();
        ctx.toolbar.style.right = '15px';
        await hide(ctx);
        expect(ctx.toolbar.style.right).toBe('');
    });

    it('hides the structure container after loadContent resolves', async () => {
        const ctx = buildContext();
        ctx.container.classList.add('cms-structure--open');
        await hide(ctx);
        expect(ctx.container.classList.contains('cms-structure--open')).toBe(false);
    });

    it('marks the second mode link as active', async () => {
        const ctx = buildContext();
        await hide(ctx);
        expect(ctx.toolbarModeLinks[1]!.classList.contains('cms-btn-active')).toBe(
            true,
        );
    });
});

// ────────────────────────────────────────────────────────────────────
// showBoard / hideBoard
// ────────────────────────────────────────────────────────────────────

describe('mode — showBoard', () => {
    it('init=true skips makeCondensed when content is not loaded yet', () => {
        const ctx = buildContext({ isLoadedContent: () => false });
        showBoard(ctx, true);
        // Container has cms-structure-mode-structure class on html
        expect(
            document.documentElement.classList.contains(
                'cms-structure-mode-structure',
            ),
        ).toBe(true);
        // FullWidth path → not condensed
        expect(isCondensed()).toBe(false);
    });

    it('init=false → makeCondensed', () => {
        const ctx = buildContext();
        showBoard(ctx, false);
        expect(isCondensed()).toBe(true);
        expect(ctx.container.classList.contains('cms-structure-condensed')).toBe(
            true,
        );
    });

    it('dispatches a window resize event', () => {
        const ctx = buildContext();
        const spy = vi.fn();
        ctx.win.addEventListener('resize', spy, { once: true });
        showBoard(ctx, false);
        expect(spy).toHaveBeenCalled();
    });
});

describe('mode — hideBoard', () => {
    it('hides the container', () => {
        const ctx = buildContext();
        ctx.container.classList.add('cms-structure--open');
        hideBoard(ctx);
        expect(ctx.container.classList.contains('cms-structure--open')).toBe(false);
    });

    it('triggers window resize', () => {
        const ctx = buildContext();
        const spy = vi.fn();
        ctx.win.addEventListener('resize', spy, { once: true });
        hideBoard(ctx);
        expect(spy).toHaveBeenCalled();
    });
});

// ────────────────────────────────────────────────────────────────────
// makeCondensed / makeFullWidth
// ────────────────────────────────────────────────────────────────────

describe('mode — makeCondensed', () => {
    it('adds cms-structure-condensed', () => {
        const ctx = buildContext();
        makeCondensed(ctx);
        expect(ctx.container.classList.contains('cms-structure-condensed')).toBe(
            true,
        );
        expect(isCondensed()).toBe(true);
    });

    it('rewrites history to the edit URL when in structure mode', () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        const spy = vi.spyOn(history, 'replaceState');
        makeCondensed(ctx);
        expect(spy).toHaveBeenCalledWith({}, '', '/cms/edit/');
    });

    it('does NOT rewrite history when in edit mode', () => {
        const ctx = buildContext();
        const spy = vi.spyOn(history, 'replaceState');
        makeCondensed(ctx);
        expect(spy).not.toHaveBeenCalled();
    });
});

describe('mode — makeFullWidth', () => {
    it('removes cms-structure-condensed and unsets condensed flag', () => {
        const ctx = buildContext();
        makeCondensed(ctx);
        makeFullWidth(ctx);
        expect(ctx.container.classList.contains('cms-structure-condensed')).toBe(
            false,
        );
        expect(isCondensed()).toBe(false);
    });

    it('rewrites history to the structure URL when in structure mode', () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        const spy = vi.spyOn(history, 'replaceState');
        makeFullWidth(ctx);
        expect(spy).toHaveBeenCalledWith({}, '', '/cms/structure/');
    });

    it('adds cms-overflow class when html is in structure mode', () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        document.documentElement.classList.add('cms-structure-mode-structure');
        makeFullWidth(ctx);
        expect(document.documentElement.classList.contains('cms-overflow')).toBe(
            true,
        );
    });
});

// ────────────────────────────────────────────────────────────────────
// toggleStructureBoard
// ────────────────────────────────────────────────────────────────────

describe('mode — toggleStructureBoard', () => {
    it('hides when in structure mode', () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        toggleStructureBoard(ctx);
        // hide is async; check that mode flips
        // (we wait via a microtask)
        return Promise.resolve().then(() => {
            expect(cms.settings!.mode).toBe('edit');
        });
    });

    it('shows when in edit mode', () => {
        const ctx = buildContext();
        toggleStructureBoard(ctx);
        return Promise.resolve().then(() => {
            const cms = (window as unknown as { CMS: CmsTestable }).CMS;
            expect(cms.settings!.mode).toBe('structure');
        });
    });

    it('with useHoveredPlugin: true, calls onShowAndHighlight when in edit mode', () => {
        const ctx = buildContext();
        const handler = vi.fn(() => Promise.resolve());
        toggleStructureBoard(ctx, {
            useHoveredPlugin: true,
            successTimeout: 200,
            onShowAndHighlight: handler,
        });
        expect(handler).toHaveBeenCalledWith(200);
    });

    it('with useHoveredPlugin: true, no-op in structure mode', () => {
        const ctx = buildContext();
        const cms = (window as unknown as { CMS: CmsTestable }).CMS;
        cms.settings!.mode = 'structure';
        const handler = vi.fn();
        toggleStructureBoard(ctx, {
            useHoveredPlugin: true,
            onShowAndHighlight: handler,
        });
        expect(handler).not.toHaveBeenCalled();
    });
});

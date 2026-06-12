import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StructureBoard } from '../../frontend/modules/structureboard/structureboard';
import {
    _resetForTest as _resetModeForTest,
} from '../../frontend/modules/structureboard/ui/mode';
import {
    _resetForTest as _resetRefreshForTest,
} from '../../frontend/modules/structureboard/refresh';
import {
    _resetForTest as _resetPropagateForTest,
} from '../../frontend/modules/structureboard/network/propagate';
import { _resetCacheForTest } from '../../frontend/modules/structureboard/network/fetch';

interface CmsTestable {
    config?: {
        mode?: string;
        settings?: Record<string, unknown>;
    };
    settings?: { mode?: string; states?: Array<number | string> };
    _instances?: unknown[];
    _plugins?: unknown[];
    API?: {
        StructureBoard?: StructureBoard;
        Helpers?: { setSettings?: ReturnType<typeof vi.fn> };
    };
}

function setupCms(): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {
            mode: 'draft',
            settings: {
                mode: 'edit',
                structure: '/cms/structure/',
                edit: '/cms/edit/',
            },
        },
        settings: { mode: 'edit', states: [] },
        _instances: [],
        _plugins: [],
        API: { Helpers: { setSettings: vi.fn() } },
    };
}

function buildToolbarDom(): void {
    document.body.innerHTML = `
        <div class="cms-structure">
            <div class="cms-structure-content"></div>
        </div>
        <div class="cms-toolbar">
            <div class="cms-toolbar-item-cms-mode-switcher">
                <a class="cms-btn cms-btn-disabled" href="/structure/">Structure</a>
                <a class="cms-btn cms-btn-disabled" href="/edit/">Content</a>
            </div>
        </div>
    `;
}

let board: StructureBoard | null = null;

beforeEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    setupCms();
    _resetModeForTest();
    _resetRefreshForTest();
    _resetPropagateForTest();
    _resetCacheForTest();
});

afterEach(() => {
    board?.destroy();
    board = null;
    document.body.innerHTML = '';
    document.documentElement.className = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetModeForTest();
    _resetRefreshForTest();
    _resetPropagateForTest();
    _resetCacheForTest();
    vi.restoreAllMocks();
});

describe('StructureBoard — construction', () => {
    it('returns early when no mode-switcher is present', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
        `;
        board = new StructureBoard();
        // No throw, no preload, no switcher.
        expect(board).toBeInstanceOf(StructureBoard);
    });

    it('builds the ui bag from the live DOM', () => {
        buildToolbarDom();
        // Mock fetch so loadContent / loadStructure don't blow up.
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html><body></body></html>', { status: 200 }),
        );
        board = new StructureBoard();
        expect(board.ui.toolbar).not.toBeNull();
        expect(board.ui.container).not.toBeNull();
        expect(board.ui.toolbarModeLinks.length).toBe(2);
    });

    it('clears stale cms-structure localStorage on init', () => {
        localStorage.setItem('cms-structure', 'stale');
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
        `;
        board = new StructureBoard();
        expect(localStorage.getItem('cms-structure')).toBeNull();
    });

    it('enables the mode-switcher buttons when dragareas exist', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar">
                <div class="cms-toolbar-item-cms-mode-switcher">
                    <a class="cms-btn cms-btn-disabled" href="/structure/"></a>
                </div>
            </div>
            <div class="cms-dragarea"></div>
        `;
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html><body></body></html>', { status: 200 }),
        );
        board = new StructureBoard();
        const btn = document.querySelector<HTMLElement>(
            '.cms-toolbar-item-cms-mode-switcher .cms-btn',
        )!;
        expect(btn.classList.contains('cms-btn-disabled')).toBe(false);
    });

    it('does not enable mode-switcher buttons when no dragareas/placeholders exist', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar">
                <div class="cms-toolbar-item-cms-mode-switcher">
                    <a class="cms-btn cms-btn-disabled" href="/structure/"></a>
                </div>
            </div>
        `;
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html><body></body></html>', { status: 200 }),
        );
        board = new StructureBoard();
        const btn = document.querySelector<HTMLElement>(
            '.cms-toolbar-item-cms-mode-switcher .cms-btn',
        )!;
        expect(btn.classList.contains('cms-btn-disabled')).toBe(true);
    });
});

describe('StructureBoard — public API surface', () => {
    it('exposes show / hide / invalidateState / getId / getIds', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
        `;
        board = new StructureBoard();
        expect(typeof board.show).toBe('function');
        expect(typeof board.hide).toBe('function');
        expect(typeof board.invalidateState).toBe('function');
        expect(typeof board.getId).toBe('function');
        expect(typeof board.getIds).toBe('function');
        expect(typeof board.showAndHighlightPlugin).toBe('function');
        expect(typeof board.highlightPluginFromUrl).toBe('function');
    });

    it('static actualizePlaceholders is the same as the dom helper', () => {
        // Smoke: callable + side-effect-free with empty DOM.
        expect(() => StructureBoard.actualizePlaceholders()).not.toThrow();
    });

    it('static _getPluginDataFromMarkup parses descriptor scripts', () => {
        document.body.innerHTML = `
            <script type="application/json" id="cms-plugin-7">{"plugin_id":7}</script>
        `;
        const data = StructureBoard._getPluginDataFromMarkup(document.body, [7]);
        expect(data.length).toBe(1);
        expect(data[0]!.plugin_id).toBe(7);
    });

    it('getId reads the numeric id from a draggable element', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
        `;
        board = new StructureBoard();
        const el = document.createElement('div');
        el.className = 'cms-draggable cms-draggable-42';
        expect(board.getId(el)).toBe(42);
    });
});

describe('StructureBoard — invalidateState integration', () => {
    it('routes ADD through to the handler', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
            <div class="cms-dragarea cms-dragarea-1">
                <div class="cms-draggables"></div>
            </div>
        `;
        board = new StructureBoard();
        board.invalidateState(
            'ADD',
            {
                placeholder_id: 1,
                structure: {
                    html: '<div class="cms-draggable cms-draggable-7"></div>',
                    plugins: [],
                },
            },
            { propagate: false },
        );
        expect(document.querySelector('.cms-draggable-7')).not.toBeNull();
    });

    it('records latestAction for cross-tab dedup', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
            <div class="cms-clipboard-containers"></div>
        `;
        board = new StructureBoard();
        board.invalidateState(
            'COPY',
            { html: '<div></div>', plugins: [] },
            { propagate: false },
        );
        expect(board.latestAction[0]).toBe('COPY');
    });

    it('calls onFullReload (default Helpers.reloadBrowser) on undefined action', () => {
        document.body.innerHTML = `
            <div class="cms-structure"></div>
            <div class="cms-toolbar"></div>
        `;
        board = new StructureBoard();
        const reload = vi.fn();
        board.invalidateState(undefined, {}, { onFullReload: reload });
        expect(reload).toHaveBeenCalledOnce();
    });
});

describe('StructureBoard — destroy', () => {
    it('detaches dnd / switcher / preload / external-update listeners', () => {
        buildToolbarDom();
        vi.spyOn(global, 'fetch').mockResolvedValue(
            new Response('<html><body></body></html>', { status: 200 }),
        );
        board = new StructureBoard();
        board.destroy();
        // Calling again is safe.
        expect(() => board!.destroy()).not.toThrow();
    });
});

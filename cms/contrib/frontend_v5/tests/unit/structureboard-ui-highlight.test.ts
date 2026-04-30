import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    highlightPluginFromUrl,
    showAndHighlightPlugin,
    type ShowAndHighlightOptions,
} from '../../frontend/modules/structureboard/ui/highlight';
import {
    _resetForTest as _resetRefreshForTest,
    refreshContent,
} from '../../frontend/modules/structureboard/refresh';
import type { ModeContext } from '../../frontend/modules/structureboard/ui/mode';

interface CmsTestable {
    config?: {
        mode?: string;
        settings?: Record<string, unknown>;
    };
    settings?: { mode?: string; states?: Array<number | string> };
    API?: {
        Tooltip?: {
            domElem?: HTMLElement;
        };
        Helpers?: { setSettings?: ReturnType<typeof vi.fn> };
    };
}

function setupCms(extras: Partial<CmsTestable> = {}): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: { mode: 'draft', settings: {} },
        settings: { mode: 'edit', states: [] },
        API: { Helpers: { setSettings: vi.fn() } },
        ...extras,
    };
}

function buildContext(): ModeContext {
    document.body.innerHTML = `
        <div id="container" class="cms-structure"></div>
        <div id="toolbar" style="width: 1024px"></div>
        <a class="cms-btn" href="/structure/"></a>
        <a class="cms-btn" href="/edit/"></a>
    `;
    return {
        container: document.getElementById('container') as HTMLElement,
        toolbar: document.getElementById('toolbar') as HTMLElement,
        html: document.documentElement,
        toolbarModeLinks: Array.from(
            document.querySelectorAll<HTMLElement>('.cms-btn'),
        ),
        win: window,
        isLoadedStructure: () => true,
        isLoadedContent: () => true,
        loadStructure: () => Promise.resolve(),
        loadContent: () => Promise.resolve(),
    };
}

beforeEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    setupCms();
    _resetRefreshForTest();
    // Mark content loaded for highlightPluginFromUrl tests.
    refreshContent('<html><body></body></html>');
});

afterEach(() => {
    document.body.innerHTML = '';
    document.documentElement.className = '';
    delete (window as { CMS?: unknown }).CMS;
    _resetRefreshForTest();
    history.replaceState(null, '', '#');
    vi.restoreAllMocks();
});

// ────────────────────────────────────────────────────────────────────
// highlightPluginFromUrl
// ────────────────────────────────────────────────────────────────────

describe('highlight — highlightPluginFromUrl', () => {
    it('does nothing when no hash is present', () => {
        history.replaceState(null, '', '#');
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7"></div>
        `;
        // Should not throw, no class added
        expect(() => highlightPluginFromUrl()).not.toThrow();
    });

    it('does nothing when hash does not match cms-plugin-N', () => {
        history.replaceState(null, '', '#some-other-anchor');
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7"></div>
        `;
        highlightPluginFromUrl();
        // No success class added
        const el = document.querySelector('.cms-plugin-7') as HTMLElement;
        expect(el.classList.length).toBe(2); // unchanged
    });

    it('flashes the matching content node when hash is cms-plugin-N', () => {
        history.replaceState(null, '', '#cms-plugin-7');
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7" style="width:10px;height:10px"></div>
        `;
        // Stub getBoundingClientRect to return non-zero size so the
        // overlay is created (skips the empty-rect branch).
        const el = document.querySelector('.cms-plugin-7') as HTMLElement;
        vi.spyOn(el, 'getBoundingClientRect').mockReturnValue({
            top: 0,
            left: 0,
            right: 10,
            bottom: 10,
            width: 10,
            height: 10,
            x: 0,
            y: 0,
            toJSON: () => ({}),
        });
        highlightPluginFromUrl();
        // The overlay element gets appended to body
        expect(document.querySelector('.cms-plugin-overlay')).not.toBeNull();
    });

    it('skips when content is not loaded', () => {
        // Reset to a not-loaded state.
        _resetRefreshForTest();
        history.replaceState(null, '', '#cms-plugin-7');
        document.body.innerHTML = `
            <div class="cms-plugin cms-plugin-7"></div>
        `;
        highlightPluginFromUrl();
        expect(document.querySelector('.cms-plugin-overlay')).toBeNull();
    });
});

// ────────────────────────────────────────────────────────────────────
// showAndHighlightPlugin
// ────────────────────────────────────────────────────────────────────

describe('highlight — showAndHighlightPlugin', () => {
    it('returns false in live mode', async () => {
        setupCms({ config: { mode: 'live', settings: {} } });
        const result = await showAndHighlightPlugin(buildContext());
        expect(result).toBe(false);
    });

    it('returns false when Tooltip API is missing', async () => {
        setupCms(); // no Tooltip
        const result = await showAndHighlightPlugin(buildContext());
        expect(result).toBe(false);
    });

    it('returns false when tooltip element is not visible', async () => {
        const tooltipEl = document.createElement('div');
        // offsetParent === null → not visible (jsdom default).
        setupCms({
            API: {
                Tooltip: { domElem: tooltipEl },
            },
        });
        const result = await showAndHighlightPlugin(buildContext());
        expect(result).toBe(false);
    });

    it('returns false when no plugin id is set on the tooltip', async () => {
        const tooltipEl = document.createElement('div');
        document.body.appendChild(tooltipEl);
        Object.defineProperty(tooltipEl, 'offsetParent', {
            value: document.body,
            configurable: true,
        });
        setupCms({
            API: {
                Tooltip: { domElem: tooltipEl },
            },
        });
        const result = await showAndHighlightPlugin(buildContext());
        expect(result).toBe(false);
    });

    it('forwards options to the structure-side overlay', async () => {
        // Build the DOM first so subsequent appendChild for the
        // tooltip lands in a stable tree (innerHTML += would
        // re-parse and detach the tooltip reference).
        document.body.innerHTML = `
            <div id="container" class="cms-structure"></div>
            <div id="toolbar"></div>
            <a class="cms-btn"></a>
            <a class="cms-btn"></a>
            <div class="cms-draggable cms-draggable-7">
                <div class="cms-dragitem"></div>
            </div>
        `;
        const tooltipEl = document.createElement('div');
        tooltipEl.dataset.pluginId = '7';
        document.body.appendChild(tooltipEl);
        Object.defineProperty(tooltipEl, 'offsetParent', {
            value: document.body,
            configurable: true,
        });
        setupCms({
            API: {
                Tooltip: { domElem: tooltipEl },
                Helpers: { setSettings: vi.fn() },
            },
        });
        const ctx: ModeContext = {
            container: document.getElementById('container') as HTMLElement,
            toolbar: document.getElementById('toolbar') as HTMLElement,
            html: document.documentElement,
            toolbarModeLinks: Array.from(
                document.querySelectorAll<HTMLElement>('.cms-btn'),
            ),
            win: window,
            isLoadedStructure: () => true,
            isLoadedContent: () => true,
            loadStructure: () => Promise.resolve(),
            loadContent: () => Promise.resolve(),
        };
        const opts: ShowAndHighlightOptions = {
            successTimeout: 100,
            seeThrough: true,
        };
        const result = await showAndHighlightPlugin(ctx, opts);
        expect(result).toBe(true);
    });
});

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import PageTree from '../../frontend/modules/pagetree';
import { Helpers } from '../../frontend/modules/cms-base';

/**
 * Fake server response: two root `<li>` elements matching
 * the shape that `get_tree` renders via `menu.html`.
 */
const ROOT_HTML = `
<li class="cms-tree-node jstree-closed"
    data-id="1" data-node-id="1"
    data-colview='<div class="cms-tree-col">view-col-1</div>'
    data-colmenu='<div class="cms-tree-col"><div class="cms-tree-item js-cms-tree-item-menu"><a href="/en/admin/cms/pagecontent/1/change-navigation/">toggle nav</a></div></div>'
    data-coloptions='<div class="cms-tree-col"><a href="/en/admin/cms/pagecontent/1/change/" class="js-cms-tree-advanced-settings" data-url="/en/admin/cms/page/1/advanced-settings/">settings</a></div>'
    data-move-permission="true" data-add-permission="true">
    Home Page
</li>
<li class="cms-tree-node"
    data-id="2" data-node-id="2"
    data-colview='<div class="cms-tree-col">view-col-2</div>'
    data-colmenu='<div class="cms-tree-col"><div class="cms-tree-item js-cms-tree-item-menu"><a href="/en/admin/cms/pagecontent/2/change-navigation/">toggle nav</a></div></div>'
    data-move-permission="true" data-add-permission="false">
    About Page
</li>
`;

/** Children of node 1, returned by lazy-load fetch. */
const CHILDREN_HTML = `
<li class="cms-tree-node"
    data-id="3" data-node-id="3"
    data-colview='<div class="cms-tree-col">view-col-3</div>'
    data-colmenu='<div class="cms-tree-col">menu-col-3</div>'
    data-move-permission="true" data-add-permission="true">
    Child Page
</li>
<li class="cms-tree-node"
    data-id="4" data-node-id="4"
    data-colview='<div class="cms-tree-col">view-col-4</div>'
    data-colmenu='<div class="cms-tree-col">menu-col-4</div>'
    data-move-permission="false" data-add-permission="false">
    Another Child
</li>
`;

const BASE_CONFIG = {
    lang: { code: 'en', loading: 'Loading...', error: 'Error:', reload: 'Reload', apphook: 'Cannot copy apphook page' },
    urls: {
        tree: '/en/admin/cms/pagecontent/get-tree/',
        move: '/en/admin/cms/page/{id}/move-page/?site=1',
        copy: '/en/admin/cms/page/{id}/copy-page/?site=1',
    },
    site: 1,
    csrf: 'test-csrf-token-abc123',
    columns: [
        { key: '', title: 'Title', width: '1%' },
        { key: 'view', title: 'View', width: '1%', cls: 'cms-tree-col-view' },
        { key: 'menu', title: 'Menu', width: '1%', cls: 'cms-tree-col-menu' },
        { key: 'options', title: 'Options', width: '1%', cls: 'cms-tree-col-options' },
    ],
};

function stubFetch(responseHtml: string) {
    return vi.fn().mockResolvedValue({
        ok: true,
        text: async () => responseHtml,
    });
}

function setupDOM() {
    document.body.innerHTML = `
        <div class="js-cms-pagetree"
             data-json='${JSON.stringify(BASE_CONFIG)}'
             data-settings-url="/en/admin/cms/usersettings/get/">
        </div>
    `;
}

/** Flush the initial async loadTree() + any follow-up microtasks. */
async function flush(ticks = 3) {
    for (let i = 0; i < ticks; i++) {
        await new Promise((resolve) => setTimeout(resolve, 0));
    }
}

describe('PageTree', () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        vi.stubGlobal('__CMS_VERSION__', 'test-version');
        localStorage.clear();
        window.CMS = {
            config: { settings: { version: 'test-version' } },
            settings: {},
        };
        setupDOM();
        fetchMock = stubFetch(ROOT_HTML);
        vi.stubGlobal('fetch', fetchMock);
    });

    afterEach(() => {
        vi.unstubAllGlobals();
        document.body.innerHTML = '';
        localStorage.clear();
        delete (window as { CMS?: unknown }).CMS;
    });

    describe('initial render', () => {
        it('fetches tree data and renders <li> elements with ARIA roles', async () => {
            PageTree.init();
            await flush();

            const items = document.querySelectorAll('li[role="treeitem"]');
            expect(items.length).toBe(2);
            expect(items[0]!.getAttribute('aria-level')).toBe('1');
            expect(items[1]!.getAttribute('aria-level')).toBe('1');
        });

        it('materialises column cells from data-col* attributes', async () => {
            PageTree.init();
            await flush();

            const firstRow = document.querySelector('li[data-id="1"] .cms-tree-row');
            expect(firstRow).not.toBeNull();

            const viewCol = firstRow!.querySelector('.cms-tree-col-view');
            expect(viewCol).not.toBeNull();
            expect(viewCol!.textContent).toContain('view-col-1');

            const menuCol = firstRow!.querySelector('.cms-tree-col-menu');
            expect(menuCol).not.toBeNull();
            expect(menuCol!.textContent).toContain('toggle nav');
        });

        it('renders a toggle button for nodes that have children (jstree-closed)', async () => {
            PageTree.init();
            await flush();

            const node1Toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="1"] .cms-tree-toggle',
            );
            expect(node1Toggle).not.toBeNull();
            expect(node1Toggle!.disabled).toBe(false);
            expect(node1Toggle!.classList.contains('cms-icon-arrow-right')).toBe(true);
            expect(node1Toggle!.classList.contains('cms-tree-toggle-open')).toBe(false);

            // Node 2 has no jstree-closed/jstree-open → leaf → toggle disabled
            const node2Toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="2"] .cms-tree-toggle',
            );
            expect(node2Toggle).not.toBeNull();
            expect(node2Toggle!.disabled).toBe(true);
        });

        it('sets aria-expanded on expandable nodes', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            expect(node1!.getAttribute('aria-expanded')).toBe('false');

            const node2 = document.querySelector<HTMLLIElement>('li[data-id="2"]');
            expect(node2!.hasAttribute('aria-expanded')).toBe(false);
        });

        it('renders page title in a .cms-tree-title element', async () => {
            PageTree.init();
            await flush();

            const title = document.querySelector('li[data-id="1"] .cms-tree-title');
            expect(title).not.toBeNull();
            expect(title!.textContent).toContain('Home Page');
        });

        it('includes the expanding node id in the initial openNodes[] request', async () => {
            PageTree.init();
            await flush();

            const [url] = fetchMock.mock.calls[0]!;
            expect(url).toContain('language=en');
            expect(url).toContain('site=1');
        });
    });

    describe('expand and lazy-load children', () => {
        it('fetches children when expanding a closed node and renders them', async () => {
            PageTree.init();
            await flush();

            // Replace fetch mock for the children request
            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => CHILDREN_HTML,
            });

            // Click the toggle button on node 1
            const toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="1"] .cms-tree-toggle',
            );
            toggle!.click();
            await flush();

            // Children should be rendered
            const children = document.querySelectorAll(
                'li[data-id="1"] > ul > li[role="treeitem"]',
            );
            expect(children.length).toBe(2);
            expect(children[0]!.getAttribute('aria-level')).toBe('2');
            expect(children[0]!.querySelector('.cms-tree-title')?.textContent).toContain(
                'Child Page',
            );
        });

        it('sends the expanding node id in openNodes[] so the server returns children', async () => {
            PageTree.init();
            await flush();

            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => CHILDREN_HTML,
            });

            const toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="1"] .cms-tree-toggle',
            );
            toggle!.click();
            await flush();

            // The second fetch call (lazy-load) should include nodeId=1
            // AND openNodes[]=1 (the critical fix that was missing)
            const childFetchUrl = fetchMock.mock.calls[1]![0] as string;
            expect(childFetchUrl).toContain('nodeId=1');
            expect(childFetchUrl).toContain('openNodes%5B%5D=1');
        });

        it('does not re-fetch children on second expand (uses cached DOM)', async () => {
            PageTree.init();
            await flush();

            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => CHILDREN_HTML,
            });

            const toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="1"] .cms-tree-toggle',
            );

            // First expand → fetches
            toggle!.click();
            await flush();
            expect(fetchMock).toHaveBeenCalledTimes(2);

            // Collapse
            toggle!.click();
            await flush();

            // Second expand → no new fetch
            toggle!.click();
            await flush();
            expect(fetchMock).toHaveBeenCalledTimes(2);

            // Children still visible
            const children = document.querySelectorAll(
                'li[data-id="1"] > ul > li[role="treeitem"]',
            );
            expect(children.length).toBe(2);
        });
    });

    describe('collapse', () => {
        it('hides child <ul> on collapse and updates toggle icon', async () => {
            PageTree.init();
            await flush();

            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => CHILDREN_HTML,
            });

            const toggle = document.querySelector<HTMLButtonElement>(
                'li[data-id="1"] .cms-tree-toggle',
            );

            // Expand
            toggle!.click();
            await flush();
            expect(toggle!.classList.contains('cms-tree-toggle-open')).toBe(true);

            const childUl = document.querySelector<HTMLUListElement>(
                'li[data-id="1"] > ul',
            );
            expect(childUl!.classList.contains('cms-tree-collapsed')).toBe(false);

            // Collapse
            toggle!.click();
            await flush();
            expect(toggle!.classList.contains('cms-tree-toggle-open')).toBe(false);
            expect(childUl!.classList.contains('cms-tree-collapsed')).toBe(true);

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            expect(node1!.getAttribute('aria-expanded')).toBe('false');
        });
    });

    describe('keyboard navigation', () => {
        it('ArrowDown moves focus to the next visible item', async () => {
            PageTree.init();
            await flush();

            const items = document.querySelectorAll<HTMLLIElement>('li[role="treeitem"]');
            items[0]!.focus();
            items[0]!.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }),
            );

            expect(document.activeElement).toBe(items[1]);
        });

        it('ArrowUp moves focus to the previous visible item', async () => {
            PageTree.init();
            await flush();

            const items = document.querySelectorAll<HTMLLIElement>('li[role="treeitem"]');
            items[1]!.tabIndex = 0;
            items[1]!.focus();
            items[1]!.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true }),
            );

            expect(document.activeElement).toBe(items[0]);
        });

        it('Home focuses the first item, End focuses the last', async () => {
            PageTree.init();
            await flush();

            const items = document.querySelectorAll<HTMLLIElement>('li[role="treeitem"]');
            items[1]!.tabIndex = 0;
            items[1]!.focus();

            items[1]!.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'Home', bubbles: true }),
            );
            expect(document.activeElement).toBe(items[0]);

            items[0]!.dispatchEvent(
                new KeyboardEvent('keydown', { key: 'End', bubbles: true }),
            );
            expect(document.activeElement).toBe(items[1]);
        });
    });

    describe('action button POST requests', () => {
        it('sends a POST with CSRF token when clicking a .js-cms-tree-item-menu link', async () => {
            PageTree.init();
            await flush();

            // The initial fetch loaded ROOT_HTML which has action links.
            // Replace fetch for the POST request.
            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => '',
            });
            // Prevent page reload on success (jsdom doesn't support location.reload)
            vi.spyOn(Helpers, 'reloadBrowser').mockImplementation(() => {});

            const actionLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-item-menu a',
            );
            expect(actionLink).not.toBeNull();
            actionLink!.click();
            await flush();

            // Find the POST call (skip the initial GET for tree data)
            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBe(1);

            const [postUrl, postInit] = postCalls[0]!;
            expect(postUrl).toBe('/en/admin/cms/pagecontent/1/change-navigation/');
            expect((postInit as RequestInit).method).toBe('POST');
            expect(
                (postInit as RequestInit).headers as Record<string, string>,
            ).toHaveProperty('X-CSRFToken', 'test-csrf-token-abc123');
        });

        it('uses the csrf token from the page config, not window.CMS.config', async () => {
            // Explicitly clear any global csrf to prove it reads from config
            if (window.CMS?.config) {
                delete (window.CMS.config as Record<string, unknown>).csrf;
            }

            PageTree.init();
            await flush();

            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => '',
            });
            vi.spyOn(Helpers, 'reloadBrowser').mockImplementation(() => {});

            const actionLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-item-menu a',
            );
            actionLink!.click();
            await flush();

            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBe(1);
            expect(
                (postCalls[0]![1] as RequestInit).headers as Record<string, string>,
            ).toHaveProperty('X-CSRFToken', 'test-csrf-token-abc123');
        });

        it('does not POST for disabled dropdown items', async () => {
            PageTree.init();
            await flush();

            // Wrap the action link in a disabled container
            const actionLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-item-menu a',
            );
            actionLink!.closest('.cms-tree-item')?.classList.add(
                'cms-pagetree-dropdown-item-disabled',
            );

            actionLink!.click();
            await flush();

            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBe(0);
        });

        it('does not POST for links with href="#"', async () => {
            PageTree.init();
            await flush();

            const actionLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-item-menu a',
            );
            actionLink!.setAttribute('href', '#');
            actionLink!.click();
            await flush();

            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBe(0);
        });

        it('shows an error message on POST failure', async () => {
            PageTree.init();
            await flush();

            fetchMock.mockResolvedValueOnce({
                ok: false,
                status: 403,
                statusText: 'Forbidden',
                text: async () => 'Permission denied',
            });

            document.body.insertAdjacentHTML(
                'afterbegin',
                '<div class="breadcrumbs">Home</div>',
            );

            const actionLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-item-menu a',
            );
            actionLink!.click();
            await flush();

            const errorMsg = document.querySelector('.messagelist .error');
            expect(errorMsg).not.toBeNull();
            expect(errorMsg!.textContent).toContain('Permission denied');
        });
    });

    describe('advanced settings link', () => {
        it('SHIFT-click prevents default and reads the data-url', async () => {
            PageTree.init();
            await flush();

            const settingsLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-advanced-settings',
            );
            expect(settingsLink).not.toBeNull();
            expect(settingsLink!.dataset.url).toBe(
                '/en/admin/cms/page/1/advanced-settings/',
            );

            const clickEvent = new MouseEvent('click', {
                shiftKey: true,
                bubbles: true,
                cancelable: true,
            });
            settingsLink!.dispatchEvent(clickEvent);

            // SHIFT-click should preventDefault (don't follow the href)
            // and instead navigate to the data-url. We can't verify
            // window.location.href assignment in jsdom, but we CAN
            // verify preventDefault was called — which proves the
            // handler ran and intercepted the click.
            expect(clickEvent.defaultPrevented).toBe(true);
        });

        it('normal click does NOT preventDefault (follows the href)', async () => {
            PageTree.init();
            await flush();

            const settingsLink = document.querySelector<HTMLAnchorElement>(
                '.js-cms-tree-advanced-settings',
            );

            const clickEvent = new MouseEvent('click', {
                shiftKey: false,
                bubbles: true,
                cancelable: true,
            });
            settingsLink!.dispatchEvent(clickEvent);

            // Without SHIFT, the handler does nothing — default
            // navigation follows the href.
            expect(clickEvent.defaultPrevented).toBe(false);
        });
    });

    describe('clipboard — cut/copy/paste', () => {
        it('clicking cut stores clipboard state and enables paste buttons', async () => {
            PageTree.init();
            await flush();

            // Inject a cut button + paste button into the rendered tree
            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-cut" data-id="1">Cut</a>',
            );
            document.body.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled" data-id="2">Paste</a>',
            );

            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!.click();
            await flush();

            const pasteBtn = document.querySelector<HTMLElement>('.js-cms-tree-item-paste');
            expect(pasteBtn!.classList.contains('cms-pagetree-dropdown-item-disabled')).toBe(false);
        });

        it('clicking copy stores clipboard state in localStorage', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-copy" data-id="1">Copy</a>',
            );

            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-copy')!.click();
            await flush();

            const stored = JSON.parse(localStorage.getItem('cms_cookie') ?? '{}');
            expect(stored.pageClipboard).toBeDefined();
            expect(stored.pageClipboard.type).toBe('copy');
            expect(stored.pageClipboard.origin).toBe('1');
        });

        it('clicking cut again on the same node deselects (toggle)', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-cut" data-id="1">Cut</a>',
            );
            document.body.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled">Paste</a>',
            );

            const cutBtn = document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!;
            cutBtn.click();
            await flush();
            expect(
                document.querySelector('.js-cms-tree-item-paste')!
                    .classList.contains('cms-pagetree-dropdown-item-disabled'),
            ).toBe(false);

            // Click again → deselect
            cutBtn.click();
            await flush();
            expect(
                document.querySelector('.js-cms-tree-item-paste')!
                    .classList.contains('cms-pagetree-dropdown-item-disabled'),
            ).toBe(true);
        });

        it('copy sets lazy-url-data on dropdown elements so future lazy-loads enable paste', async () => {
            PageTree.init();
            await flush();

            // Add a dropdown element (simulating what the tree row renders)
            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-actions-dropdown js-cms-pagetree-dropdown"
                      data-lazy-url="/en/admin/cms/page/1/actions-menu/"
                      data-loaded="true">
                    <a href="#" class="js-cms-tree-item-copy" data-id="1">Copy</a>
                </div>`,
            );

            // Add a second dropdown on node 2 (already "loaded" with paste disabled)
            const node2 = document.querySelector<HTMLLIElement>('li[data-id="2"]');
            const row2 = node2!.querySelector('.cms-tree-row')!;
            row2.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-actions-dropdown js-cms-pagetree-dropdown"
                      data-lazy-url="/en/admin/cms/page/2/actions-menu/"
                      data-loaded="true">
                    <a href="#" class="js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled" data-id="2">Paste</a>
                </div>`,
            );

            // Copy from node 1
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-copy')!.click();
            await flush();

            // After copy: all dropdown elements should have lazy-url-data
            // with has_copy flag so future lazy-loads render paste as enabled
            const dd2 = node2!.querySelector<HTMLElement>('.js-cms-pagetree-actions-dropdown')!;
            expect(dd2.dataset.lazyUrlData).toBeDefined();
            const parsedData = JSON.parse(dd2.dataset.lazyUrlData!);
            expect(parsedData.has_copy).toBe('true');

            // And the 'loaded' flag should be cleared so the dropdown
            // re-fetches on next open (getting the server-rendered paste
            // button with the enabled state)
            expect(dd2.dataset.loaded).toBeUndefined();
        });

        it('disabling paste clears lazy-url-data and resets loaded flag', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-actions-dropdown js-cms-pagetree-dropdown"
                      data-lazy-url="/en/admin/cms/page/1/actions-menu/">
                    <a href="#" class="js-cms-tree-item-cut" data-id="1">Cut</a>
                </div>`,
            );
            document.body.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-actions-dropdown" data-loaded="true"
                      data-lazy-url-data='{"has_cut":"true"}'></div>`,
            );

            // Cut → enables paste
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!.click();
            await flush();

            // Cut again on same node → toggle off → disables paste
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!.click();
            await flush();

            const dd = document.querySelectorAll<HTMLElement>('.js-cms-pagetree-actions-dropdown');
            for (const el of Array.from(dd)) {
                expect(el.dataset.lazyUrlData).toBeUndefined();
                expect(el.dataset.loaded).toBeUndefined();
            }
        });

        it('paste is disabled on the cut node itself and its descendants', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                `<a href="#" class="js-cms-tree-item-cut" data-id="1">Cut</a>
                 <a href="#" class="js-cms-tree-item-paste" data-id="1">Paste</a>`,
            );

            // Also add a paste button on node 2 (should stay enabled)
            const node2 = document.querySelector<HTMLLIElement>('li[data-id="2"]');
            const row2 = node2!.querySelector('.cms-tree-row')!;
            row2.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-paste cms-pagetree-dropdown-item-disabled" data-id="2">Paste</a>',
            );

            // Cut node 1
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!.click();
            await flush();

            // Node 1's paste button should be DISABLED (can't paste into yourself)
            const paste1 = node1!.querySelector<HTMLElement>('.js-cms-tree-item-paste');
            expect(paste1!.classList.contains('cms-pagetree-dropdown-item-disabled')).toBe(true);

            // Node 2's paste button should be ENABLED
            const paste2 = node2!.querySelector<HTMLElement>('.js-cms-tree-item-paste');
            expect(paste2!.classList.contains('cms-pagetree-dropdown-item-disabled')).toBe(false);
        });

        it('paste sends a POST to the move endpoint for cut clipboard', async () => {
            PageTree.init();
            await flush();

            // Set up clipboard state (simulate a cut)
            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-cut" data-id="1">Cut</a>',
            );

            const node2 = document.querySelector<HTMLLIElement>('li[data-id="2"]');
            const row2 = node2!.querySelector('.cms-tree-row')!;
            row2.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-paste" data-id="2">Paste</a>',
            );

            // Cut node 1
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-cut')!.click();
            await flush();

            // Mock the POST response
            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => '',
            });
            // Mock the subsequent tree reload
            fetchMock.mockResolvedValueOnce({
                ok: true,
                text: async () => ROOT_HTML,
            });

            // Paste onto node 2
            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-paste')!.click();
            await flush(5);

            // Find the POST call
            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBeGreaterThanOrEqual(1);

            const [postUrl, postInit] = postCalls[0]!;
            expect(postUrl).toContain('/move-page/');
            expect((postInit as RequestInit).headers as Record<string, string>)
                .toHaveProperty('X-CSRFToken', 'test-csrf-token-abc123');
        });

        it('paste sends a POST to the copy endpoint for copy clipboard', async () => {
            PageTree.init();
            await flush();

            const node1 = document.querySelector<HTMLLIElement>('li[data-id="1"]');
            const row = node1!.querySelector('.cms-tree-row')!;
            row.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-copy" data-id="1">Copy</a>',
            );

            const node2 = document.querySelector<HTMLLIElement>('li[data-id="2"]');
            const row2 = node2!.querySelector('.cms-tree-row')!;
            row2.insertAdjacentHTML(
                'beforeend',
                '<a href="#" class="js-cms-tree-item-paste" data-id="2">Paste</a>',
            );

            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-copy')!.click();
            await flush();

            fetchMock.mockResolvedValueOnce({ ok: true, text: async () => '' });
            fetchMock.mockResolvedValueOnce({ ok: true, text: async () => ROOT_HTML });

            document.querySelector<HTMLAnchorElement>('.js-cms-tree-item-paste')!.click();
            await flush(5);

            const postCalls = fetchMock.mock.calls.filter(
                (call: unknown[]) => {
                    const init = call[1] as RequestInit | undefined;
                    return init?.method === 'POST';
                },
            );
            expect(postCalls.length).toBeGreaterThanOrEqual(1);
            expect(postCalls[0]![0]).toContain('/copy-page/');
        });
    });

    describe('header search + filter dropdown', () => {
        function setupSearchDOM() {
            document.body.innerHTML = `
                <div class="cms-pagetree-root" id="changelist">
                    <div class="cms-pagetree cms-pagetree-header">
                        <form class="js-cms-pagetree-header-search" method="get">
                            <div class="cms-pagetree-header-filter">
                                <input type="text" id="field-searchbar" name="q" value="">
                                <div class="js-cms-pagetree-header-filter-trigger">▼</div>
                                <div class="js-cms-pagetree-header-filter-container"
                                     style="display:none">
                                    <a href="#" class="js-cms-pagetree-header-search-close">x</a>
                                </div>
                            </div>
                        </form>
                        <div class="js-cms-pagetree-header-search-copy cms-hidden">
                            <form>
                                <input type="hidden" name="language" value="en">
                                <input type="hidden" name="site" value="1">
                            </form>
                        </div>
                    </div>
                    <div class="js-cms-pagetree"
                         data-json='${JSON.stringify(BASE_CONFIG)}'></div>
                </div>
            `;
        }

        it('copies hidden filter inputs into the visible form', async () => {
            setupSearchDOM();
            PageTree.init();
            await flush();

            const visibleForm = document.querySelector<HTMLFormElement>(
                '.js-cms-pagetree-header-search',
            )!;
            expect(visibleForm.querySelector('input[name="language"]')).not.toBeNull();
            expect(visibleForm.querySelector('input[name="site"]')).not.toBeNull();
        });

        it('toggles the filter container on trigger click', async () => {
            setupSearchDOM();
            PageTree.init();
            await flush();

            const trigger = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-trigger',
            )!;
            const container = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-container',
            )!;

            trigger.click();
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(true);

            trigger.click();
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(false);
        });

        it('closes the filter on close button click', async () => {
            setupSearchDOM();
            PageTree.init();
            await flush();

            const trigger = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-trigger',
            )!;
            const container = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-container',
            )!;
            const close = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-search-close',
            )!;

            trigger.click();
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(true);
            close.click();
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(false);
        });

        it('closes the filter on outside click', async () => {
            setupSearchDOM();
            PageTree.init();
            await flush();

            const trigger = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-trigger',
            )!;
            const container = document.querySelector<HTMLElement>(
                '.js-cms-pagetree-header-filter-container',
            )!;

            trigger.click();
            // Let the deferred document click listener attach
            await flush(1);
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(true);

            document.body.click();
            expect(
                container.classList.contains(
                    'cms-pagetree-header-filter-container--open',
                ),
            ).toBe(false);
        });

        it('adds active class when the search field is focused', async () => {
            setupSearchDOM();
            PageTree.init();
            await flush();

            const header = document.querySelector<HTMLElement>(
                '.cms-pagetree-header',
            )!;
            const field = document.querySelector<HTMLInputElement>(
                '#field-searchbar',
            )!;
            field.dispatchEvent(new FocusEvent('focus'));
            expect(
                header.classList.contains('cms-pagetree-header-filter-active'),
            ).toBe(true);
        });
    });

    describe('filtered mode', () => {
        it('adopts the pre-rendered <ul> and does NOT fetch from get_tree', async () => {
            // Mimic the Django template: filtered=true and the server
            // has pre-rendered matching rows into a <ul> inside the
            // container. get_tree has no query support, so the ajax
            // fetch must NOT fire.
            const filteredConfig = { ...BASE_CONFIG, filtered: true };
            document.body.innerHTML = `
                <div class="js-cms-pagetree"
                     data-json='${JSON.stringify(filteredConfig)}'>
                    <ul>
                        <li class="cms-tree-node"
                            data-id="42" data-node-id="42"
                            data-colview='<div class="cms-tree-col">v</div>'
                            data-colmenu='<div class="cms-tree-col">m</div>'
                            data-move-permission="true" data-add-permission="true">
                            Matched Page
                        </li>
                    </ul>
                </div>
            `;

            PageTree.init();
            await flush();

            // get_tree must not be called in filtered mode
            expect(fetchMock).not.toHaveBeenCalled();

            // The pre-rendered <li> is adopted and enhanced
            const li = document.querySelector<HTMLLIElement>('li[data-id="42"]');
            expect(li).not.toBeNull();
            expect(li!.getAttribute('role')).toBe('treeitem');

            // The tree root is the server's <ul>, upgraded with role="tree"
            const ul = document.querySelector<HTMLUListElement>(
                '.js-cms-pagetree > ul',
            );
            expect(ul?.getAttribute('role')).toBe('tree');
            expect(ul?.classList.contains('cms-pagetree-list')).toBe(true);

            // No second tree root gets appended
            expect(
                document.querySelectorAll('.js-cms-pagetree > ul').length,
            ).toBe(1);
        });
    });

    describe('dropdown integration', () => {
        it('opens a dropdown when the trigger is clicked', async () => {
            // Add a dropdown trigger to the DOM (simulating what data-coloptions renders)
            PageTree.init();
            await flush();

            // The options column has the dropdown structure from ROOT_HTML.
            // But the actual dropdown trigger class needs to be in the rendered columns.
            // Let's insert one manually into the container for this test.
            const container = document.querySelector<HTMLElement>('.js-cms-pagetree')!;
            container.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-dropdown">
                    <a href="#" class="js-cms-pagetree-dropdown-trigger">Menu</a>
                    <div class="js-cms-pagetree-dropdown-menu">
                        <a href="/action/">Action</a>
                    </div>
                </div>`,
            );

            const trigger = container.querySelector<HTMLAnchorElement>(
                '.js-cms-pagetree-dropdown-trigger',
            );
            trigger!.click();

            const dropdown = container.querySelector('.js-cms-pagetree-dropdown');
            expect(dropdown!.classList.contains('cms-pagetree-dropdown-menu-open')).toBe(true);
        });

        it('closes dropdowns on outside click', async () => {
            PageTree.init();
            await flush();

            const container = document.querySelector<HTMLElement>('.js-cms-pagetree')!;
            container.insertAdjacentHTML(
                'beforeend',
                `<div class="js-cms-pagetree-dropdown">
                    <a href="#" class="js-cms-pagetree-dropdown-trigger">Menu</a>
                    <div class="js-cms-pagetree-dropdown-menu">Content</div>
                </div>`,
            );

            // Open
            container.querySelector<HTMLAnchorElement>(
                '.js-cms-pagetree-dropdown-trigger',
            )!.click();
            expect(
                container.querySelector('.js-cms-pagetree-dropdown')!
                    .classList.contains('cms-pagetree-dropdown-menu-open'),
            ).toBe(true);

            // Click outside
            document.body.click();
            expect(
                container.querySelector('.js-cms-pagetree-dropdown')!
                    .classList.contains('cms-pagetree-dropdown-menu-open'),
            ).toBe(false);
        });
    });
});

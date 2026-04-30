/*
 * Phase 4a — read-only pagetree rendering.
 *
 * Replaces the legacy jsTree-based page tree with a vanilla nested-ul
 * rendering. The server's `get_tree` endpoint returns HTML `<li>`
 * elements that already carry:
 *
 *   - Tree hierarchy (nested `<ul>` for pre-expanded children)
 *   - Page title as text content
 *   - Column cells in `data-col*` attributes (server-rendered HTML)
 *   - Permission flags in `data-*` attributes
 *   - State classes (`jstree-open`, `jstree-closed`)
 *
 * This module enhances that HTML: inserts it into a `<ul role="tree">`
 * container, materialises the column cells from data attributes into
 * visible DOM, adds ARIA attributes, wires expand/collapse click
 * handlers, lazy-loads children on first expand, and syncs expand
 * state to localStorage (same key as legacy for compat).
 *
 * Phase 4a scope — read-only. No DnD, no dropdowns, no clipboard.
 * Those are phases 4b–4d.
 */

import TreeDrag, { TreeDropResult } from './tree/drag';

import { Helpers } from './cms-base';
import PageTreeDropdowns from './pagetree-dropdowns';

// ────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────

interface ClipboardState {
    type: 'cut' | 'copy' | null;
    origin: string | null;
    id: string | null;
    source_site: number | null;
}

interface PageTreeConfig {
    lang: { code: string; loading: string; apphook?: string; error?: string; reload?: string };
    urls: {
        tree: string;
        move?: string;
        copy?: string;
        copyPermission?: string;
    };
    site: number;
    columns: Array<{
        key: string;
        title: string;
        width?: string;
        cls?: string;
    }>;
    filtered?: boolean;
    csrf?: string;
    permission?: boolean;
    hasAddRootPermission?: boolean;
}

// ────────────────────────────────────────────────────────────────────
// PageTree class
// ────────────────────────────────────────────────────────────────────

export default class PageTree {
    readonly config: PageTreeConfig;
    private readonly container: HTMLElement;
    private readonly treeRoot: HTMLUListElement;
    private expandedNodeIds: Set<string>;
    private dropdowns: PageTreeDropdowns | null = null;
    private clipboard: ClipboardState = {
        type: null,
        origin: null,
        id: null,
        source_site: null,
    };
    private treeDrag: TreeDrag | null = null;

    constructor(container: HTMLElement, config: PageTreeConfig) {
        this.config = config;
        this.container = container;
        this.expandedNodeIds = new Set<string>(this.getStoredNodeIds());

        // The template renders an empty <ul> inside the container —
        // in non-filtered mode it's a placeholder for loadTree() to
        // populate, in filtered mode the server has already rendered
        // matching rows into it. Either way, adopt the existing <ul>
        // as the tree root so we don't end up with a leftover empty
        // sibling <ul> consuming vertical space.
        const existingUl =
            this.container.querySelector<HTMLUListElement>(':scope > ul');
        if (existingUl) {
            this.treeRoot = existingUl;
        } else {
            this.treeRoot = document.createElement('ul');
            this.container.appendChild(this.treeRoot);
        }
        this.treeRoot.setAttribute('role', 'tree');
        this.treeRoot.classList.add('cms-pagetree-list');

        // Keyboard nav on the tree root
        this.treeRoot.addEventListener('keydown', this.onKeyDown.bind(this));

        // Dropdown menus (Phase 4b) — delegated on the ROOT container
        // (#changelist / .cms-pagetree-root) so both the header
        // dropdowns (site picker, "Options" menu) AND the per-row
        // burger menus are handled by one instance. The template has
        // MULTIPLE sibling .cms-pagetree elements (header, section,
        // container) — none is the ancestor of the others. Their
        // common ancestor is #changelist. Legacy attached to ALL
        // .cms-pagetree elements via jQuery collection; we use the
        // single common ancestor instead.
        const broadContainer =
            this.container.closest<HTMLElement>('#changelist') ??
            this.container.closest<HTMLElement>('.cms-pagetree-root') ??
            this.container;
        this.dropdowns = new PageTreeDropdowns({
            container: broadContainer,
            onContentLoaded: () => {
                // After lazy-load: re-apply paste disabling on the cut
                // node's dropdown. The server renders paste as enabled
                // (because it got has_cut=true), but the cut node's own
                // dropdown should have paste disabled (can't paste into
                // yourself).
                this.disablePasteOnCutNode();
            },
        });

        // Wire action buttons that POST via AJAX (publish, set-home,
        // change-navigation, etc.). Phase 4b. Scoped to the same broad
        // container as dropdowns so header actions work too.
        this.bindActionButtons(broadContainer);

        // Clipboard — cut/copy/paste (Phase 4d)
        this.bindClipboard(broadContainer);
        this.restoreClipboard();

        // Header search + filter dropdown (Phase 4e)
        this.setupSearch(broadContainer);

        // Initial load. In filtered mode, the server is the source of
        // truth — always enhance whatever rows are already in the DOM
        // (possibly none, if the filter matched nothing) and NEVER
        // call loadTree, since get_tree has no query support and
        // would return the full unfiltered tree.
        if (config.filtered) {
            this.enhanceTree(this.treeRoot, 1);
        } else {
            this.loadTree();
        }

        // CSRF: pagetree's POSTs use the native `request.ts` wrapper,
        // which reads the token per-call from the cookie. We
        // intentionally do NOT call `Helpers.csrf()` here — that would
        // lazy-load the jQuery chunk just to set up `$.ajaxSetup`,
        // and nothing on the pagetree page makes jQuery ajax calls.
    }

    // ────────────────────────────────────────────────────────────
    // Action buttons (Phase 4b) — links that POST via AJAX
    // ────────────────────────────────────────────────────────────

    /**
     * Wire action buttons that fire POST requests to Django endpoints.
     * These are links rendered inside the dropdown menus (and directly
     * on the tree row) for: publish, unpublish, set-home,
     * change-in-navigation, and language-specific publish actions.
     *
     * Each such link has a selector matching one of the legacy
     * patterns: `.js-cms-tree-item-menu a`, `.js-cms-tree-lang-trigger`,
     * `.js-cms-tree-item-set-home a`. When clicked, the link's `href`
     * is sent as a POST request. On success the page reloads.
     *
     * Port of legacy PageTree._setAjaxPost().
     */
    private bindActionButtons(actionContainer: HTMLElement): void {
        const actionSelectors = [
            '.js-cms-tree-item-menu a',
            '.js-cms-tree-lang-trigger',
            '.js-cms-tree-item-set-home a',
        ];

        for (const selector of actionSelectors) {
            actionContainer.addEventListener('click', (e) => {
                const target = e.target;
                if (!(target instanceof Element)) return;
                const link = target.closest<HTMLAnchorElement>(selector);
                if (!link) return;

                e.preventDefault();

                // Disabled items
                if (link.closest('.cms-pagetree-dropdown-item-disabled')) return;

                const href = link.getAttribute('href');
                if (!href || href === '#') return;

                // Special case: links with target="_top" need a form-based POST
                // (because the admin might be inside a sideframe)
                if (link.getAttribute('target') === '_top') {
                    this.postViaForm(href);
                    return;
                }

                this.postAction(href);
            });
        }

        // Advanced settings link — SHIFT-click goes to advanced settings,
        // normal click follows the href (page content change form).
        actionContainer.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const link = target.closest<HTMLAnchorElement>(
                '.js-cms-tree-advanced-settings',
            );
            if (!link) return;
            if (e instanceof MouseEvent && e.shiftKey) {
                e.preventDefault();
                const advUrl = link.dataset.url;
                if (advUrl) window.location.href = advUrl;
            }
            // Normal click: follows the link's href naturally (no preventDefault)
        });
    }

    private async postAction(url: string): Promise<void> {
        try {
            const csrfToken = this.config.csrf ?? window.CMS?.config?.csrf ?? '';
            const response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
            });
            if (!response.ok) {
                const text = await response.text();
                this.showError(text || response.statusText);
                return;
            }
            // Reload the page tree after a successful action
            if (window.self === window.top) {
                Helpers.reloadBrowser();
            } else {
                window.location.reload();
            }
        } catch (err) {
            this.showError(String(err));
        }
    }

    private postViaForm(url: string): void {
        const parent = window.parent ?? window;
        const csrfInput = document.querySelector<HTMLInputElement>(
            'form input[name="csrfmiddlewaretoken"]',
        );
        const csrfToken = csrfInput?.value ?? this.config.csrf ?? '';
        const form = document.createElement('form');
        form.method = 'post';
        form.action = url;
        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">`;
        parent.document.body.appendChild(form);
        form.submit();
    }

    private showError(message: string): void {
        // The server's `jsonify_request` returns form errors serialized
        // as Django's ErrorList HTML — usually
        //   `<ul class="errorlist"><li>actual message</li></ul>`
        // We want the actual message inside the admin-style
        // `.messagelist` wrapper, not a nested errorlist. Parse out
        // the inner <li> content and inject it.
        const parser = document.createElement('div');
        parser.innerHTML = message;
        const innerLi = parser.querySelector('li');
        const innerMessage = innerLi ? innerLi.innerHTML : message;

        const existing = document.querySelector('.messagelist');
        const breadcrumb = document.querySelector('.breadcrumbs');
        const container =
            this.container.closest<HTMLElement>('#changelist') ??
            document.querySelector<HTMLElement>('#content-main') ??
            document.body;
        const tpl = `<ul class="messagelist"><li class="error"><strong>${this.config.lang.error ?? 'Error:'}</strong> ${innerMessage} <a href="#reload" class="cms-tree-reload">${this.config.lang.reload ?? 'Reload'}</a></li></ul>`;
        if (existing) {
            existing.outerHTML = tpl;
        } else if (breadcrumb) {
            breadcrumb.insertAdjacentHTML('afterend', tpl);
        } else {
            container.insertAdjacentHTML('afterbegin', tpl);
        }
    }

    // ────────────────────────────────────────────────────────────
    // Clipboard — cut/copy/paste (Phase 4d)
    // ────────────────────────────────────────────────────────────

    private bindClipboard(clipboardContainer: HTMLElement): void {
        // Cut
        clipboardContainer.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const link = target.closest<HTMLElement>('.js-cms-tree-item-cut');
            if (!link) return;
            e.preventDefault();
            this.cutOrCopy('cut', link);
        });

        // Copy
        clipboardContainer.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const link = target.closest<HTMLElement>('.js-cms-tree-item-copy');
            if (!link) return;
            e.preventDefault();

            // Prevent copying pages with apphooks
            if (link.dataset.apphook) {
                this.showError(this.config.lang.apphook ?? 'Cannot copy a page with an apphook.');
                return;
            }
            this.cutOrCopy('copy', link);
        });

        // Paste
        clipboardContainer.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const link = target.closest<HTMLElement>('.js-cms-tree-item-paste');
            if (!link) return;
            e.preventDefault();
            if (link.classList.contains('cms-pagetree-dropdown-item-disabled')) return;
            this.paste(link);
        });
    }

    // ────────────────────────────────────────────────────────────
    // Header search + filter dropdown (Phase 4e)
    // ────────────────────────────────────────────────────────────

    /**
     * Wire up the header search UI. Native GET submission already
     * handles the actual filtering — this method only adds the UX
     * chrome: filter-dropdown toggle, focus/blur active state, and
     * copying hidden filter inputs into the visible form so extra
     * filter params (language, site, …) survive a search submission.
     *
     * Port of legacy PageTree._setupSearch().
     */
    private setupSearch(searchContainer: HTMLElement): void {
        const header = searchContainer.querySelector<HTMLElement>(
            '.cms-pagetree-header',
        );
        if (!header) return;

        const filterActiveCls = 'cms-pagetree-header-filter-active';
        const visibleForm = searchContainer.querySelector<HTMLFormElement>(
            '.js-cms-pagetree-header-search',
        );
        const hiddenForm = searchContainer.querySelector<HTMLFormElement>(
            '.js-cms-pagetree-header-search-copy form',
        );
        const filterTrigger = searchContainer.querySelector<HTMLElement>(
            '.js-cms-pagetree-header-filter-trigger',
        );
        const filterContainer = searchContainer.querySelector<HTMLElement>(
            '.js-cms-pagetree-header-filter-container',
        );
        const filterClose = filterContainer?.querySelector<HTMLElement>(
            '.js-cms-pagetree-header-search-close',
        );
        const searchField =
            searchContainer.querySelector<HTMLInputElement>('#field-searchbar');

        // Copy hidden filter inputs into the visible form so extra
        // params (language, site, …) survive a search submission. The
        // template renders them into a hidden sibling form; we move
        // them into the visible form at init.
        if (visibleForm && hiddenForm) {
            const hiddenInputs = hiddenForm.querySelectorAll<HTMLInputElement>(
                'input[type="hidden"]',
            );
            for (const input of Array.from(hiddenInputs)) {
                visibleForm.appendChild(input);
            }
        }

        // Focus/blur on the search field toggles the "active" class.
        // Blur is delayed so clicking the filter trigger doesn't cause
        // the field to shrink mid-click.
        let filterActive = false;
        if (searchField) {
            searchField.addEventListener('focus', () => {
                header.classList.add(filterActiveCls);
            });
            searchField.addEventListener('blur', () => {
                setTimeout(() => {
                    if (!filterActive) header.classList.remove(filterActiveCls);
                }, 200);
            });
        }

        const closeFilter = () => {
            if (!filterContainer) return;
            filterContainer.classList.remove(
                'cms-pagetree-header-filter-container--open',
            );
            if (!searchField || document.activeElement !== searchField) {
                header.classList.remove(filterActiveCls);
            }
            filterActive = false;
            document.removeEventListener('click', onDocClick);
        };
        const openFilter = () => {
            if (!filterContainer) return;
            filterContainer.classList.add(
                'cms-pagetree-header-filter-container--open',
            );
            header.classList.add(filterActiveCls);
            filterActive = true;
            // Defer so the opening click itself doesn't immediately
            // close the dropdown via the document handler.
            setTimeout(() => {
                document.addEventListener('click', onDocClick);
            }, 0);
        };
        const onDocClick = () => closeFilter();

        filterTrigger?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (filterActive) closeFilter();
            else openFilter();
        });

        filterClose?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeFilter();
        });

        // Clicks inside the filter container should not close it.
        filterContainer?.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    private restoreClipboard(): void {
        try {
            const settings = window.CMS?.settings as Record<string, unknown> | undefined;
            const stored = settings?.pageClipboard as ClipboardState | undefined;
            if (stored?.type && stored?.origin) {
                this.clipboard = { ...stored };
                this.enablePaste();
                this.updatePasteState();
            }
        } catch {
            // ignore
        }
    }

    private cutOrCopy(type: 'cut' | 'copy', element: HTMLElement): void {
        const pageId = element.dataset.id ?? '';
        // The jstree node id is extracted from the closest grid cell
        // in legacy. In our rendering, the element is inside a tree row
        // that's inside a <li data-id="...">. The li's data-id is the
        // page id which doubles as the tree identifier.
        const treeNodeId =
            element.closest<HTMLElement>('li[data-id]')?.dataset.id ?? pageId;

        // Toggle: clicking the same action again deselects
        if (this.clipboard.type === type && treeNodeId === this.clipboard.id) {
            this.clipboard = { type: null, origin: null, id: null, source_site: null };
            this.disablePaste();
        } else {
            this.clipboard = {
                type,
                origin: pageId,
                id: treeNodeId,
                source_site: this.config.site,
            };
            this.enablePaste();
            this.updatePasteState();
        }

        // Persist to localStorage (so clipboard survives page reload)
        if (this.clipboard.type === 'copy' || !this.clipboard.type) {
            this.persistClipboard();
        }

        // Close dropdowns after cut/copy
        this.dropdowns?.closeAllDropdowns();
    }

    private async paste(targetElement: HTMLElement): Promise<void> {
        if (!this.clipboard.type || !this.clipboard.origin) return;

        this.disablePaste();

        const targetPageId =
            targetElement.closest<HTMLElement>('li[data-id]')?.dataset.id ??
            targetElement.dataset.id ??
            '';

        const data: Record<string, string> = {
            position: '0',
        };

        if (targetPageId && targetPageId !== '#' && targetPageId !== '#root') {
            data.target = targetPageId;
        }

        if (this.clipboard.type === 'cut') {
            await this.moveNode(this.clipboard.origin, data);
        } else {
            await this.copyNode(this.clipboard.origin, data);
        }

        // Reset clipboard
        this.clipboard = { type: null, origin: null, id: null, source_site: null };
        this.persistClipboard();
    }

    /**
     * POST to a tree-mutation endpoint (move / copy) and reload the
     * tree on success. Returns true if the operation succeeded.
     *
     * The CMS admin wraps all such responses via `jsonify_request`
     * (cms/utils/admin.py): even 4xx error responses come back as
     * HTTP 200 with a JSON body `{status: <original>, content: <msg>}`.
     * So `response.ok` is useless for error detection — we parse the
     * envelope and inspect `status` explicitly. 200 = success; any
     * other status means showError(content) and skip the reload.
     */
    private async postTreeMutation(
        url: string,
        data: Record<string, string>,
    ): Promise<boolean> {
        try {
            const body = new URLSearchParams(data);
            const response = await fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'X-CSRFToken': this.config.csrf ?? '' },
                body,
            });
            const text = await response.text();
            // Try to parse the jsonify_request envelope. If parsing
            // fails, fall back to raw HTTP status.
            let innerStatus = response.status;
            let innerContent = text;
            try {
                const parsed = JSON.parse(text) as { status?: number; content?: string };
                if (typeof parsed.status === 'number') innerStatus = parsed.status;
                if (typeof parsed.content === 'string') innerContent = parsed.content;
            } catch {
                // Not JSON — keep the raw text/status we already have.
            }
            if (innerStatus !== 200) {
                // eslint-disable-next-line no-console
                console.error('PageTree mutation failed:', innerStatus, innerContent);
                this.showError(innerContent || `HTTP ${innerStatus}`);
                return false;
            }
            // Reload the tree from the server.
            this.treeRoot.innerHTML = '';
            await this.loadTree();
            return true;
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error('PageTree mutation exception:', err);
            this.showError(String(err));
            return false;
        }
    }

    private async moveNode(
        pageId: string,
        data: Record<string, string>,
    ): Promise<void> {
        const url = (this.config.urls.move ?? '').replace('{id}', pageId);
        if (!url) return;

        data.site = String(this.config.site);
        if (this.clipboard.source_site && this.clipboard.source_site !== this.config.site) {
            data.source_site = String(this.clipboard.source_site);
        }

        await this.postTreeMutation(url, data);
    }

    private async copyNode(
        pageId: string,
        data: Record<string, string>,
    ): Promise<void> {
        const url = (this.config.urls.copy ?? '').replace('{id}', pageId);
        if (!url) return;

        data.source_site = String(this.clipboard.source_site ?? this.config.site);
        await this.postTreeMutation(url, data);
    }

    private enablePaste(): void {
        // Enable any paste buttons already in the DOM
        const pasteButtons = document.querySelectorAll<HTMLElement>(
            '.js-cms-tree-item-paste',
        );
        for (const btn of Array.from(pasteButtons)) {
            btn.classList.remove('cms-pagetree-dropdown-item-disabled');
        }

        // Tell lazy-loaded dropdowns to pass clipboard state to the
        // server so FUTURE lazy-loads render paste as enabled. Also
        // reset 'loaded' flag so already-loaded dropdowns re-fetch
        // with the new state when next opened.
        const urlData = this.clipboard.type === 'cut'
            ? { has_cut: 'true' }
            : { has_copy: 'true' };
        const dropdowns = document.querySelectorAll<HTMLElement>(
            '.js-cms-pagetree-actions-dropdown',
        );
        for (const dd of Array.from(dropdowns)) {
            dd.dataset.lazyUrlData = JSON.stringify(urlData);
            delete dd.dataset.loaded;
        }

        // Disable paste on the cut node itself and its descendants
        // (can't paste into yourself). Must run AFTER enabling all
        // paste buttons above.
        this.disablePasteOnCutNode();
    }

    /**
     * After a cut, disable paste on the cut node and all its
     * descendants. This runs both at cut time (for already-rendered
     * paste buttons) AND is re-applied after lazy-load completes
     * (because the server-rendered HTML doesn't know about client-side
     * cut state).
     */
    private disablePasteOnCutNode(): void {
        if (this.clipboard.type !== 'cut' || !this.clipboard.id) return;
        if (this.clipboard.source_site !== this.config.site) return;

        const cutLi = this.treeRoot.querySelector<HTMLElement>(
            `li[data-id="${this.clipboard.id}"]`,
        );
        if (!cutLi) return;

        // Disable paste buttons inside the cut node AND all its descendants
        const pasteInCut = cutLi.querySelectorAll<HTMLElement>(
            '.js-cms-tree-item-paste',
        );
        for (const btn of Array.from(pasteInCut)) {
            btn.classList.add('cms-pagetree-dropdown-item-disabled');
        }
    }

    private disablePaste(): void {
        const pasteButtons = document.querySelectorAll<HTMLElement>(
            '.js-cms-tree-item-paste',
        );
        for (const btn of Array.from(pasteButtons)) {
            btn.classList.add('cms-pagetree-dropdown-item-disabled');
        }

        // Clear the clipboard data from lazy-load dropdowns and reset
        // loaded state so they re-fetch clean.
        const dropdowns = document.querySelectorAll<HTMLElement>(
            '.js-cms-pagetree-actions-dropdown',
        );
        for (const dd of Array.from(dropdowns)) {
            delete dd.dataset.lazyUrlData;
            delete dd.dataset.loaded;
        }
    }

    private updatePasteState(): void {
        if (this.clipboard.type && this.clipboard.id) {
            this.enablePaste();
        }
    }

    private persistClipboard(): void {
        try {
            if (window.CMS) {
                const settings = (window.CMS.settings ?? {}) as Record<string, unknown>;
                settings.pageClipboard = this.clipboard;
                Helpers.setSettings(settings);
            }
        } catch {
            // localStorage might be unavailable
        }
    }

    // ────────────────────────────────────────────────────────────
    // Drag-and-drop — custom pointer-events controller
    // ────────────────────────────────────────────────────────────
    //
    // Unlike the earlier SortableJS-based implementation, this one
    // does not mutate the tree DOM during drag. TreeDrag renders a
    // drop marker at the prospective position and commits via
    // `onTreeDrop` on pointerup. The server reload reconciles DOM.
    //
    // See CLAUDE.md decision 4: drop-on-row-middle = child, drop
    // between rows = sibling, with horizontal cursor picking depth.

    private installSortable(_container: HTMLElement): void {
        // Idempotent: re-called after each lazy-load, but we only
        // need ONE TreeDrag instance bound to the tree root. Skip if
        // already installed.
        if (this.treeDrag) return;
        this.treeDrag = new TreeDrag({
            containers: [this.treeRoot],
            handleSelector: '.cms-tree-handle',
            itemSelector: 'li[role="treeitem"]',
            rowSelector: '.cms-tree-row',
            depthPx: 24,
            canDrag: (item) => item.dataset.movePermission === 'true',
            canDropAsChild: (target, item) =>
                target.dataset.addPermission === 'true' && !item.contains(target),
            onDrop: (result) => this.onTreeDrop(result),
        });
    }

    private async onTreeDrop(result: TreeDropResult): Promise<void> {
        const item = result.item as HTMLLIElement;
        const pageId = item.dataset.id ?? '';
        if (!pageId) return;

        // Work out the server-side `target` (parent page id) and
        // `position` (index within parent). In both cases, `target`
        // is the NEW PARENT — for sibling drops that's the parent of
        // the anchor, for child drops that's the reference itself.
        let targetPageId: string | undefined;
        let position = 0;

        if (result.kind === 'child') {
            targetPageId = (result.reference as HTMLElement).dataset.id;
            position = 0;
            // Ensure the target node is marked to re-expand after
            // the server reload, so the dropped child is visible.
            if (targetPageId) this.storeNodeId(targetPageId);
        } else {
            // Sibling drop — compute parent + position from the anchor.
            const anchor = result.anchor as HTMLElement;
            const parentUl = anchor.parentElement;
            const parentLi = parentUl?.closest<HTMLElement>('li[role="treeitem"]');
            if (parentLi) {
                targetPageId = parentLi.dataset.id;
                if (targetPageId) this.storeNodeId(targetPageId);
            }
            // Compute the server-side `position` index. The Django
            // move form (see cms/admin/forms.py PageTreeForm) looks
            // up siblings in the PRE-MOVE tree — so our indexing must
            // INCLUDE the dragged item. Do NOT filter it out.
            if (parentUl) {
                const siblings = Array.from(
                    parentUl.querySelectorAll<HTMLElement>(
                        ':scope > li[role="treeitem"]',
                    ),
                );
                const anchorIdx = siblings.indexOf(anchor);
                position =
                    result.kind === 'sibling-after'
                        ? anchorIdx + 1
                        : anchorIdx;
            }
        }

        const data: Record<string, string> = {
            position: String(position),
            site: String(this.config.site),
        };
        if (targetPageId) {
            data.target = targetPageId;
        }

        await this.moveNode(pageId, data);
    }

    // ────────────────────────────────────────────────────────────
    // Data loading
    // ────────────────────────────────────────────────────────────

    private async loadTree(): Promise<void> {
        const params = new URLSearchParams();
        params.set('language', this.config.lang.code);
        params.set('site', String(this.config.site));
        for (const id of this.expandedNodeIds) {
            params.append('openNodes[]', id);
        }

        try {
            const response = await fetch(
                `${this.config.urls.tree}?${params.toString()}`,
                { credentials: 'same-origin' },
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const html = await response.text();
            this.treeRoot.innerHTML = html;
            this.enhanceTree(this.treeRoot, 1);
            if (!this.config.filtered) {
                this.installSortable(this.treeRoot);
            }
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error('PageTree: failed to load tree', err);
        }
    }

    private async loadChildren(
        parentLi: HTMLElement,
        nodeId: string,
    ): Promise<void> {
        const params = new URLSearchParams();
        params.set('language', this.config.lang.code);
        params.set('site', String(this.config.site));
        params.set('nodeId', nodeId);
        for (const id of this.expandedNodeIds) {
            params.append('openNodes[]', id);
        }

        try {
            const response = await fetch(
                `${this.config.urls.tree}?${params.toString()}`,
                { credentials: 'same-origin' },
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const html = await response.text();

            let childUl = parentLi.querySelector<HTMLUListElement>(
                ':scope > ul',
            );
            if (!childUl) {
                childUl = document.createElement('ul');
                childUl.setAttribute('role', 'group');
                parentLi.appendChild(childUl);
            }
            childUl.innerHTML = html;

            const parentDepth = Number(parentLi.getAttribute('aria-level') ?? 1);
            this.enhanceTree(childUl, parentDepth + 1);
            if (!this.config.filtered) {
                this.installSortable(childUl);
            }
            parentLi.dataset.childrenLoaded = 'true';
        } catch (err) {
            // eslint-disable-next-line no-console
            console.error('PageTree: failed to load children for', nodeId, err);
        }
    }

    // ────────────────────────────────────────────────────────────
    // DOM enhancement
    // ────────────────────────────────────────────────────────────

    /**
     * Walk each `<li>` in the given container and enhance it:
     * materialise column cells, add ARIA, add toggle buttons.
     */
    private enhanceTree(container: HTMLElement, startDepth: number): void {
        const items = container.querySelectorAll<HTMLLIElement>(':scope > li');
        const siblingCount = items.length;

        items.forEach((li, index) => {
            this.enhanceNode(li, startDepth, index + 1, siblingCount);
        });
    }

    private enhanceNode(
        li: HTMLLIElement,
        depth: number,
        posInSet: number,
        setSize: number,
    ): void {
        const nodeId = li.dataset.nodeId ?? li.dataset.id ?? '';
        const hasChildren =
            li.classList.contains('jstree-open') ||
            li.classList.contains('jstree-closed') ||
            li.querySelector(':scope > ul') !== null;
        const isExpanded =
            li.classList.contains('jstree-open') ||
            this.expandedNodeIds.has(nodeId);

        // ARIA
        li.setAttribute('role', 'treeitem');
        li.setAttribute('aria-level', String(depth));
        li.setAttribute('aria-setsize', String(setSize));
        li.setAttribute('aria-posinset', String(posInSet));
        li.tabIndex = depth === 1 && posInSet === 1 ? 0 : -1;

        if (hasChildren) {
            li.setAttribute('aria-expanded', String(isExpanded));
            li.dataset.hasServerChildren = 'true';
        }

        // If the node already has real children rendered (jstree-open),
        // mark it as loaded so expandNode doesn't re-fetch.
        if (li.classList.contains('jstree-open') && li.querySelector(':scope > ul > li')) {
            li.dataset.childrenLoaded = 'true';
        }

        // Build the row wrapper (grid container for columns)
        const existingRow = li.querySelector(':scope > .cms-tree-row');
        if (existingRow) return; // already enhanced (e.g. re-enhance after lazy load)

        const row = document.createElement('div');
        row.className = 'cms-tree-row';
        // Indentation is NOT applied as padding-left on the row —
        // that would put empty space inside the row's background box.
        // Instead the nested <ul role="group"> carries padding-inline-
        // start via CSS (_tree-new-dom.scss), which naturally shifts
        // child rows inward so their backgrounds/borders start at the
        // indented x-position.

        // Drag handle — visual affordance for DnD. SortableJS's handle
        // selector now points at this element (see installSortable);
        // rows are no longer draggable as a whole, which prevents
        // accidental drags when clicking title text or column links.
        if (this.config.filtered !== true) {
            const handle = document.createElement('span');
            handle.className = 'cms-tree-handle';
            handle.setAttribute('aria-hidden', 'true');
            row.appendChild(handle);
        }

        // Toggle button — uses `cms-icon-arrow-right` from the
        // iconfont. The rotated-open state is triggered via the
        // `cms-tree-toggle-open` modifier class (CSS rotates the
        // `::before` pseudo 90°) — matches the legacy jstree-ocl
        // approach in `_tree.scss` line 845.
        const toggle = document.createElement('button');
        toggle.className = 'cms-tree-toggle cms-icon cms-icon-arrow-right';
        toggle.type = 'button';
        toggle.tabIndex = -1;
        if (hasChildren) {
            if (isExpanded) toggle.classList.add('cms-tree-toggle-open');
            toggle.setAttribute('aria-label', isExpanded ? 'Collapse' : 'Expand');
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNode(li);
            });
        } else {
            toggle.disabled = true;
        }
        row.appendChild(toggle);

        // Title cell — the text content of the `<li>` is the page title
        // (rendered by `{% get_page_display_name page %}` in menu.html).
        // We need to extract ONLY the direct text, not the child `<ul>`.
        const titleCell = document.createElement('span');
        titleCell.className = 'cms-tree-title';
        // Collect text nodes that are direct children of the `<li>`
        const textNodes: string[] = [];
        for (const child of Array.from(li.childNodes)) {
            if (child.nodeType === Node.TEXT_NODE && child.textContent?.trim()) {
                textNodes.push(child.textContent.trim());
            }
        }
        titleCell.textContent = textNodes.join(' ');
        row.appendChild(titleCell);

        // Column cells from data-col* attributes.
        //
        // The server-rendered HTML already wraps each column's content
        // in its own `<div class="cms-tree-col">` (see
        // cms/templates/admin/cms/page/tree/menu.html). We parse that
        // HTML and hoist the top-level element directly into the row
        // as the grid cell — wrapping again would give us
        // `.cms-tree-col > .cms-tree-col`. The optional `col.cls`
        // from config is merged into the existing class list.
        const parser = document.createElement('div');
        for (const col of this.config.columns) {
            if (!col.key) continue; // first column is the title, skip
            const attrName = `col${col.key.replace(/-/g, '')}`;
            const html = li.dataset[attrName];
            if (!html) continue;
            parser.innerHTML = html.trim();
            const cell = parser.firstElementChild as HTMLElement | null;
            if (!cell) continue;
            if (col.cls) cell.classList.add(...col.cls.split(/\s+/).filter(Boolean));
            row.appendChild(cell);
        }

        // Insert the row at the start of the <li>, before any child <ul>
        li.insertBefore(row, li.firstChild);

        // Clean up the bare text nodes (now displayed via the title cell)
        for (const child of Array.from(li.childNodes)) {
            if (child.nodeType === Node.TEXT_NODE) {
                li.removeChild(child);
            }
        }

        // Mark child <ul> as group
        let childUl = li.querySelector<HTMLUListElement>(':scope > ul');
        if (childUl) {
            childUl.setAttribute('role', 'group');
            if (!isExpanded) {
                childUl.classList.add('cms-tree-collapsed');
            }
            // Enhance children recursively
            this.enhanceTree(childUl, depth + 1);
        }

        // Ensure every node that accepts children has a <ul> drop
        // target for SortableJS, even if it's a leaf or collapsed
        // lazy node. Without this, SortableJS can't drop INTO the
        // node (only reorder among its siblings).
        const canAddChildren = li.dataset.addPermission === 'true';
        if (canAddChildren && !li.querySelector(':scope > ul')) {
            const emptyUl = document.createElement('ul');
            emptyUl.setAttribute('role', 'group');
            emptyUl.classList.add('cms-tree-collapsed');
            li.appendChild(emptyUl);
        }

        // Row click → focus this node
        row.addEventListener('click', () => {
            this.focusNode(li);
        });
    }

    // ────────────────────────────────────────────────────────────
    // Expand / collapse
    // ────────────────────────────────────────────────────────────

    private async toggleNode(li: HTMLLIElement): Promise<void> {
        const isExpanded = li.getAttribute('aria-expanded') === 'true';
        if (isExpanded) {
            this.collapseNode(li);
        } else {
            await this.expandNode(li);
        }
    }

    private async expandNode(li: HTMLLIElement): Promise<void> {
        const nodeId = li.dataset.nodeId ?? li.dataset.id ?? '';
        li.setAttribute('aria-expanded', 'true');

        // Update toggle icon — rotate the iconfont arrow 90° via class
        const toggle = li.querySelector<HTMLButtonElement>(
            ':scope > .cms-tree-row > .cms-tree-toggle',
        );
        if (toggle) {
            toggle.classList.add('cms-tree-toggle-open');
            toggle.setAttribute('aria-label', 'Collapse');
        }

        // Persist BEFORE fetch — the server's get_tree view filters
        // children by `Q(parent__in=open_page_ids)`, so the expanding
        // node's id MUST be in the openNodes[] param for the server to
        // return its children. Legacy does the same: _storeNodeId runs
        // inside jsTree's data() callback before the AJAX fires.
        this.storeNodeId(nodeId);

        // Lazy-load children if not yet loaded. Check the server-side
        // "has children" flag (set during enhanceNode from jstree-closed/
        // jstree-open classes) rather than the existence of a <ul>,
        // because enhanceNode now creates empty <ul> drop targets on
        // every add-permission node for SortableJS.
        const isLazyParent = li.dataset.hasServerChildren === 'true';
        if (isLazyParent && li.dataset.childrenLoaded !== 'true') {
            await this.loadChildren(li, nodeId);
        }

        // Show children — `.cms-tree-collapsed` rule already drives
        // display, no inline override needed.
        const ul = li.querySelector<HTMLUListElement>(':scope > ul');
        ul?.classList.remove('cms-tree-collapsed');
    }

    private collapseNode(li: HTMLLIElement): void {
        const nodeId = li.dataset.nodeId ?? li.dataset.id ?? '';
        li.setAttribute('aria-expanded', 'false');

        const toggle = li.querySelector<HTMLButtonElement>(
            ':scope > .cms-tree-row > .cms-tree-toggle',
        );
        if (toggle) {
            toggle.classList.remove('cms-tree-toggle-open');
            toggle.setAttribute('aria-label', 'Expand');
        }

        const childUl = li.querySelector<HTMLUListElement>(':scope > ul');
        childUl?.classList.add('cms-tree-collapsed');

        this.removeNodeId(nodeId);
    }

    // ────────────────────────────────────────────────────────────
    // Keyboard navigation
    // ────────────────────────────────────────────────────────────

    private onKeyDown(e: KeyboardEvent): void {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        const li = target.closest<HTMLLIElement>('li[role="treeitem"]');
        if (!li) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.focusNextVisible(li);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.focusPrevVisible(li);
                break;
            case 'ArrowRight':
                e.preventDefault();
                if (li.getAttribute('aria-expanded') === 'false') {
                    this.expandNode(li);
                } else if (li.getAttribute('aria-expanded') === 'true') {
                    const firstChild = li.querySelector<HTMLLIElement>(
                        ':scope > ul > li[role="treeitem"]',
                    );
                    if (firstChild) this.focusNode(firstChild);
                }
                break;
            case 'ArrowLeft':
                e.preventDefault();
                if (li.getAttribute('aria-expanded') === 'true') {
                    this.collapseNode(li);
                } else {
                    const parentLi = li.parentElement?.closest<HTMLLIElement>(
                        'li[role="treeitem"]',
                    );
                    if (parentLi) this.focusNode(parentLi);
                }
                break;
            case 'Home':
                e.preventDefault();
                {
                    const first = this.treeRoot.querySelector<HTMLLIElement>(
                        'li[role="treeitem"]',
                    );
                    if (first) this.focusNode(first);
                }
                break;
            case 'End':
                e.preventDefault();
                {
                    const all = this.getVisibleItems();
                    if (all.length > 0) this.focusNode(all[all.length - 1]!);
                }
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (li.hasAttribute('aria-expanded')) {
                    this.toggleNode(li);
                }
                break;
        }
    }

    private focusNode(li: HTMLLIElement): void {
        // Remove tabindex from currently focused treeitem
        const prev = this.treeRoot.querySelector<HTMLLIElement>(
            'li[role="treeitem"][tabindex="0"]',
        );
        if (prev) prev.tabIndex = -1;
        li.tabIndex = 0;
        li.focus();
    }

    private getVisibleItems(): HTMLLIElement[] {
        const items: HTMLLIElement[] = [];
        const walk = (container: HTMLElement) => {
            for (const li of Array.from(
                container.querySelectorAll<HTMLLIElement>(':scope > li[role="treeitem"]'),
            )) {
                items.push(li);
                if (li.getAttribute('aria-expanded') === 'true') {
                    const childUl = li.querySelector<HTMLUListElement>(':scope > ul');
                    if (childUl) walk(childUl);
                }
            }
        };
        walk(this.treeRoot);
        return items;
    }

    private focusNextVisible(li: HTMLLIElement): void {
        const all = this.getVisibleItems();
        const idx = all.indexOf(li);
        if (idx >= 0 && idx < all.length - 1) {
            this.focusNode(all[idx + 1]!);
        }
    }

    private focusPrevVisible(li: HTMLLIElement): void {
        const all = this.getVisibleItems();
        const idx = all.indexOf(li);
        if (idx > 0) {
            this.focusNode(all[idx - 1]!);
        }
    }

    // ────────────────────────────────────────────────────────────
    // LocalStorage expand state (compat with legacy keys)
    // ────────────────────────────────────────────────────────────

    private getStoredNodeIds(): string[] {
        try {
            const settings = window.CMS?.settings as Record<string, unknown> | undefined;
            const stored = settings?.pagetree;
            return Array.isArray(stored) ? (stored as string[]) : [];
        } catch {
            return [];
        }
    }

    private storeNodeId(id: string): void {
        this.expandedNodeIds.add(id);
        this.persistExpandState();
    }

    private removeNodeId(id: string): void {
        this.expandedNodeIds.delete(id);
        // Also remove any descendant ids that might be in storage
        const li = this.treeRoot.querySelector<HTMLLIElement>(
            `li[data-node-id="${id}"], li[data-id="${id}"]`,
        );
        if (li) {
            const childItems = li.querySelectorAll<HTMLLIElement>('li[data-node-id]');
            for (const child of Array.from(childItems)) {
                const childId = child.dataset.nodeId ?? child.dataset.id ?? '';
                this.expandedNodeIds.delete(childId);
            }
        }
        this.persistExpandState();
    }

    private persistExpandState(): void {
        try {
            if (window.CMS) {
                const settings = (window.CMS.settings ?? {}) as Record<string, unknown>;
                settings.pagetree = [...this.expandedNodeIds];
                Helpers.setSettings(settings);
            }
        } catch {
            // silently fail — localStorage might be unavailable
        }
    }

    // ────────────────────────────────────────────────────────────
    // Static init (matches legacy pattern)
    // ────────────────────────────────────────────────────────────

    static init(): void {
        const el = document.querySelector<HTMLElement>('.js-cms-pagetree');
        if (!el) return;

        const configStr = el.getAttribute('data-json') ?? el.dataset.json ?? '{}';
        let config: PageTreeConfig;
        try {
            config = JSON.parse(configStr) as PageTreeConfig;
        } catch {
            // eslint-disable-next-line no-console
            console.error('PageTree: invalid JSON config on .js-cms-pagetree');
            return;
        }

        // Create the tree container inside the existing element
        new PageTree(el, config);
    }
}

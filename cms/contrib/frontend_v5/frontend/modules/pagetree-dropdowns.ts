/*
 * Pagetree action dropdowns (burger menus).
 *
 * Port of the legacy `cms/static/cms/js/modules/cms.pagetree.dropdown.js`.
 * Each page row in the tree has a "..." trigger button that opens a
 * dropdown with actions: copy, cut, paste, delete, advanced settings,
 * permissions. The dropdown content is lazy-loaded from the server on
 * first open to avoid fetching menus for hundreds of rows on page load.
 *
 * Phase 4b scope: open/close dropdowns, lazy-load content, close on
 * outside click. The actual cut/copy/paste actions are Phase 4d.
 *
 * Ported from jQuery to vanilla DOM. Uses event delegation on the
 * tree container so it works for dynamically-loaded (lazy) rows.
 */

interface DropdownOptions {
    container: HTMLElement;
    dropdownSelector?: string;
    triggerSelector?: string;
    menuSelector?: string;
    openCls?: string;
    /** Called after a dropdown's lazy-loaded content is inserted. */
    onContentLoaded?: (dropdown: HTMLElement) => void;
}

const DEFAULTS = {
    dropdownSelector: '.js-cms-pagetree-dropdown',
    triggerSelector: '.js-cms-pagetree-dropdown-trigger',
    menuSelector: '.js-cms-pagetree-dropdown-menu',
    openCls: 'cms-pagetree-dropdown-menu-open',
};

export default class PageTreeDropdowns {
    private readonly container: HTMLElement;
    private readonly sel: Required<typeof DEFAULTS>;
    private readonly onContentLoaded: ((dropdown: HTMLElement) => void) | null;
    private readonly teardowns: Array<() => void> = [];

    constructor(options: DropdownOptions) {
        this.container = options.container;
        this.sel = { ...DEFAULTS, ...options };
        this.onContentLoaded = options.onContentLoaded ?? null;
        this.bindEvents();
    }

    private bindEvents(): void {
        // Toggle dropdown on trigger click (delegated). Uses
        // stopPropagation to prevent the document-level outside-click
        // handler from immediately closing the dropdown we just opened.
        const onTriggerClick = (e: Event) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            const trigger = target.closest(this.sel.triggerSelector);
            if (!trigger) return;
            e.preventDefault();
            e.stopPropagation();
            this.toggleDropdown(trigger as HTMLElement);
        };
        this.container.addEventListener('click', onTriggerClick);
        this.teardowns.push(() =>
            this.container.removeEventListener('click', onTriggerClick),
        );

        // Close dropdown when clicking a menu link (delegated)
        const onMenuLinkClick = (e: Event) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            if (target.closest(`${this.sel.menuSelector} a`)) {
                this.closeAllDropdowns();
            }
        };
        this.container.addEventListener('click', onMenuLinkClick);
        this.teardowns.push(() =>
            this.container.removeEventListener('click', onMenuLinkClick),
        );

        // Stop propagation on menu clicks so the document-level
        // outside-click handler doesn't close the dropdown mid-interaction.
        // Using stopPropagation (NOT stopImmediatePropagation) so that
        // other handlers on the same container — specifically the action
        // button handlers from pagetree.ts — still fire for clicks on
        // action links inside the dropdown menu.
        const onMenuClick = (e: Event) => {
            const target = e.target;
            if (!(target instanceof Element)) return;
            if (target.closest(this.sel.menuSelector)) {
                e.stopPropagation();
            }
        };
        this.container.addEventListener('click', onMenuClick);
        this.teardowns.push(() =>
            this.container.removeEventListener('click', onMenuClick),
        );

        // Close all dropdowns on outside click
        const onDocClick = () => this.closeAllDropdowns();
        document.addEventListener('click', onDocClick);
        this.teardowns.push(() =>
            document.removeEventListener('click', onDocClick),
        );
    }

    private toggleDropdown(trigger: HTMLElement): void {
        const dropdown = trigger.closest(this.sel.dropdownSelector) as HTMLElement | null;
        if (!dropdown) return;

        const allDropdowns = this.container.querySelectorAll<HTMLElement>(
            this.sel.dropdownSelector,
        );

        if (dropdown.classList.contains(this.sel.openCls)) {
            // Already open → close it
            for (const dd of Array.from(allDropdowns)) {
                dd.classList.remove(this.sel.openCls);
            }
            return;
        }

        // Close others, open this one
        for (const dd of Array.from(allDropdowns)) {
            dd.classList.remove(this.sel.openCls);
        }
        dropdown.classList.add(this.sel.openCls);

        this.loadContent(dropdown);
    }

    private async loadContent(dropdown: HTMLElement): Promise<void> {
        const lazyUrl = dropdown.dataset.lazyUrl;
        if (!lazyUrl || dropdown.dataset.loaded === 'true') return;

        const LOADER_SHOW_TIMEOUT = 200;
        const loader = dropdown.querySelector<HTMLElement>(
            '.js-cms-pagetree-dropdown-loader',
        );
        const loaderTimeout = setTimeout(() => {
            loader?.classList.add('cms-loader');
        }, LOADER_SHOW_TIMEOUT);

        try {
            // Build URL with any extra data (e.g. has_cut/has_copy flags
            // from the clipboard state, set by Phase 4d)
            let url = lazyUrl;
            const lazyUrlData = dropdown.dataset.lazyUrlData;
            if (lazyUrlData) {
                try {
                    const data = JSON.parse(lazyUrlData) as Record<string, string>;
                    const params = new URLSearchParams(data);
                    url += (url.includes('?') ? '&' : '?') + params.toString();
                } catch {
                    // ignore parse errors
                }
            }

            const response = await fetch(url, { credentials: 'same-origin' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const html = await response.text();

            const menu = dropdown.querySelector<HTMLElement>(this.sel.menuSelector);
            if (menu) menu.innerHTML = html;
            dropdown.dataset.loaded = 'true';
            this.onContentLoaded?.(dropdown);
        } catch {
            // Silently fail — leave the loader/dummy structure as-is
        } finally {
            clearTimeout(loaderTimeout);
            loader?.classList.remove('cms-loader');
        }
    }

    closeAllDropdowns(): void {
        const allDropdowns = this.container.querySelectorAll<HTMLElement>(
            this.sel.dropdownSelector,
        );
        for (const dd of Array.from(allDropdowns)) {
            dd.classList.remove(this.sel.openCls);
        }
    }

    destroy(): void {
        for (const teardown of this.teardowns) {
            teardown();
        }
    }
}

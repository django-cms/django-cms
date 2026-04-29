/*
 * Navigation — toolbar overflow controller. Mirrors `cms.navigation.js`.
 *
 * On narrow viewports, the toolbar can run out of horizontal space.
 * This class measures every nav-item width up-front, then on resize
 * pushes items into a "more" dropdown (right-to-left from the left
 * part, left-to-right from the right part) until everything fits.
 * On widening it pulls them back out in reverse.
 *
 * Public surface:
 *   class Navigation {
 *       constructor()
 *       items: { left, right, leftTotalWidth, rightTotalWidth, moreButtonWidth }
 *       rightMostItemIndex: number
 *       leftMostItemIndex: number
 *   }
 *
 * Width measurement is lazy because the toolbar's CSS may not have
 * loaded at construction time (legacy mode). The class probes the
 * computed `float` of the first nav <li>; if it's still `none`,
 * stylesheet hasn't applied and we skip the measure pass — the next
 * resize/load event triggers it.
 */

import { throttle } from 'lodash-es';

const THROTTLE_TIMEOUT = 50;

interface MeasuredItem {
    element: HTMLElement;
    width: number;
}

interface NavItems {
    left: MeasuredItem[];
    right: MeasuredItem[];
    leftTotalWidth: number;
    rightTotalWidth: number;
    moreButtonWidth: number;
}

interface NavigationUi {
    toolbarLeftPart: HTMLElement | null;
    toolbarRightPart: HTMLElement | null;
    trigger: HTMLElement | null;
    dropdown: HTMLElement | null;
    toolbarTrigger: HTMLElement | null;
    logo: HTMLElement | null;
}

export class Navigation {
    public ui: NavigationUi;
    public items: NavItems;
    public rightMostItemIndex = -1;
    public leftMostItemIndex = 0;

    private widthsReady = false;
    private cleanups: Array<() => void> = [];

    constructor() {
        this.ui = this.setupUi();
        this.items = this.emptyItems();
        this.bindEvents();
    }

    /** Release every listener bound by the constructor. */
    destroy(): void {
        for (const c of this.cleanups) c();
        this.cleanups = [];
    }

    // ────────────────────────────────────────────────────────────
    // Internal
    // ────────────────────────────────────────────────────────────

    private setupUi(): NavigationUi {
        const container = document.querySelector<HTMLElement>('.cms');
        const trigger = container?.querySelector<HTMLElement>(
            '.cms-toolbar-more',
        ) ?? null;
        return {
            toolbarLeftPart:
                container?.querySelector<HTMLElement>('.cms-toolbar-left') ??
                null,
            toolbarRightPart:
                container?.querySelector<HTMLElement>('.cms-toolbar-right') ??
                null,
            trigger,
            dropdown: trigger?.querySelector<HTMLElement>(':scope > ul') ?? null,
            toolbarTrigger:
                container?.querySelector<HTMLElement>('.cms-toolbar-trigger') ??
                null,
            logo:
                container?.querySelector<HTMLElement>('.cms-toolbar-item-logo') ??
                null,
        };
    }

    private emptyItems(): NavItems {
        return {
            left: [],
            right: [],
            leftTotalWidth: 0,
            rightTotalWidth: 0,
            moreButtonWidth: 0,
        };
    }

    private bindEvents(): void {
        const handler = throttle(
            () => this.handleResize(),
            THROTTLE_TIMEOUT,
        );
        window.addEventListener('resize', handler);
        window.addEventListener('load', handler);
        window.addEventListener('orientationchange', handler);
        this.cleanups.push(() => {
            window.removeEventListener('resize', handler);
            window.removeEventListener('load', handler);
            window.removeEventListener('orientationchange', handler);
            handler.cancel();
        });
    }

    /**
     * Measure widths once the toolbar CSS has loaded. Called from
     * `handleResize` after probing the first nav <li>'s computed
     * `float`.
     */
    private getWidths(): void {
        if (!this.ui.toolbarLeftPart || !this.ui.toolbarRightPart) return;

        // Reset everything to natural (toolbar) positions before measuring.
        this.showAll();

        this.items = this.emptyItems();
        const leftItems = Array.from(
            this.ui.toolbarLeftPart.querySelectorAll<HTMLElement>(
                '.cms-toolbar-item-navigation > li:not(.cms-toolbar-more)',
            ),
        );
        const rightItems = Array.from(
            this.ui.toolbarRightPart.querySelectorAll<HTMLElement>(
                ':scope > .cms-toolbar-item',
            ),
        );

        for (const el of leftItems) {
            this.items.left.push({ element: el, width: outerWidthMargins(el) });
        }
        for (const el of rightItems) {
            this.items.right.push({ element: el, width: outerWidthMargins(el) });
        }

        this.items.leftTotalWidth = this.items.left.reduce(
            (s, i) => s + i.width,
            0,
        );
        this.items.rightTotalWidth = this.items.right.reduce(
            (s, i) => s + i.width,
            0,
        );
        this.items.moreButtonWidth = this.ui.trigger
            ? outerWidthNoMargins(this.ui.trigger)
            : 0;

        this.rightMostItemIndex = this.items.left.length - 1;
        this.leftMostItemIndex = 0;
        this.widthsReady = true;
    }

    private calculateAvailableWidth(): number {
        const fullWidth = window.innerWidth;
        const right = this.ui.toolbarRightPart;
        const logo = this.ui.logo;
        const cs = right ? getComputedStyle(right) : null;
        const padInlineEnd = cs ? parseInt(cs.paddingInlineEnd, 10) || 0 : 0;
        const logoWidth = logo ? outerWidthMargins(logo) : 0;
        return fullWidth - padInlineEnd - logoWidth;
    }

    private showDropdown(): void {
        if (this.ui.trigger) this.ui.trigger.style.display = 'list-item';
    }

    private hideDropdown(): void {
        if (this.ui.trigger) this.ui.trigger.style.display = 'none';
    }

    private handleResize(): void {
        if (!this.widthsReady) {
            const probe = this.ui.toolbarLeftPart?.querySelector<HTMLElement>(
                '.cms-toolbar-item-navigation > li',
            );
            if (!probe || getComputedStyle(probe).cssFloat === 'none') return;
            this.getWidths();
        }

        const availableWidth = this.calculateAvailableWidth();

        if (
            availableWidth >
            this.items.leftTotalWidth + this.items.rightTotalWidth
        ) {
            this.showAll();
            return;
        }

        // First handle the left part.
        let remainingWidth =
            availableWidth -
            this.items.moreButtonWidth -
            this.items.rightTotalWidth;

        let newRightMostItemIndex = -1;
        while (
            this.items.left[newRightMostItemIndex + 1] &&
            remainingWidth -
                this.items.left[newRightMostItemIndex + 1]!.width >=
                0
        ) {
            remainingWidth -=
                this.items.left[newRightMostItemIndex + 1]!.width;
            newRightMostItemIndex++;
        }

        if (newRightMostItemIndex < this.rightMostItemIndex) {
            this.moveToDropdown(
                this.rightMostItemIndex - newRightMostItemIndex,
            );
        } else if (this.rightMostItemIndex < newRightMostItemIndex) {
            this.moveOutOfDropdown(
                newRightMostItemIndex - this.rightMostItemIndex,
            );
        }

        this.showDropdown();

        // If everything from the left part is already in the dropdown
        // and we still don't fit, stuff the right part in too.
        if (remainingWidth < 0 && this.rightMostItemIndex === -1) {
            const newLeftMostItemIndex = this.items.right.length;
            // Legacy comment: "but for now we want to move all of them
            // immediately" — preserve that behaviour.
            this.moveToDropdown(
                newLeftMostItemIndex - this.leftMostItemIndex,
                'right',
            );
            this.ui.dropdown?.classList.add('cms-more-dropdown-full');
        } else {
            this.showAllRight();
            this.ui.dropdown?.classList.remove('cms-more-dropdown-full');
        }
    }

    private showAll(): void {
        this.showAllLeft();
        this.showAllRight();
        this.hideDropdown();
    }

    private showAllLeft(): void {
        this.moveOutOfDropdown(
            this.items.left.length - 1 - this.rightMostItemIndex,
        );
    }

    private showAllRight(): void {
        this.moveOutOfDropdown(this.leftMostItemIndex, 'right');
    }

    private moveToDropdown(
        numberOfItems: number,
        part: 'left' | 'right' = 'left',
    ): void {
        if (numberOfItems <= 0 || !this.ui.dropdown) return;

        if (part === 'right') {
            const start = this.leftMostItemIndex;
            const end = this.leftMostItemIndex + numberOfItems - 1;
            for (let i = start; i <= end; i++) {
                const el = this.items.right[i]?.element;
                if (!el) continue;
                const wrapper = document.createElement('li');
                wrapper.className = 'cms-more-buttons';
                wrapper.appendChild(el);
                this.ui.dropdown.insertBefore(
                    wrapper,
                    this.ui.dropdown.firstChild,
                );
            }
            this.leftMostItemIndex += numberOfItems;
        } else {
            const end = this.rightMostItemIndex;
            const start = this.rightMostItemIndex - numberOfItems + 1;
            for (let i = end; i >= start; i--) {
                const el = this.items.left[i]?.element;
                if (!el) continue;
                this.ui.dropdown.insertBefore(el, this.ui.dropdown.firstChild);
                const sub = el.querySelector<HTMLUListElement>(':scope > ul');
                if (sub && sub.children.length > 0) {
                    el.classList.add('cms-toolbar-item-navigation-children');
                }
            }
            this.rightMostItemIndex -= numberOfItems;
        }
    }

    private moveOutOfDropdown(
        numberOfItems: number,
        part: 'left' | 'right' = 'left',
    ): void {
        if (numberOfItems <= 0) return;

        if (part === 'right') {
            const end = this.leftMostItemIndex - 1;
            const start = this.leftMostItemIndex - numberOfItems;
            for (let i = end; i >= start; i--) {
                const el = this.items.right[i]?.element;
                if (!el || !this.ui.toolbarRightPart) continue;
                // Unwrap the `<li class="cms-more-buttons">` we added.
                const parent = el.parentElement;
                if (parent && parent.tagName === 'LI') {
                    parent.parentElement?.removeChild(parent);
                }
                this.ui.toolbarRightPart.insertBefore(
                    el,
                    this.ui.toolbarRightPart.firstChild,
                );
            }
            this.leftMostItemIndex -= numberOfItems;
        } else {
            const start = this.rightMostItemIndex + 1;
            const end = this.rightMostItemIndex + numberOfItems;
            for (let i = start; i <= end; i++) {
                const el = this.items.left[i]?.element;
                if (!el || !this.ui.trigger) continue;
                this.ui.trigger.parentElement?.insertBefore(
                    el,
                    this.ui.trigger,
                );
                el.classList.remove('cms-toolbar-item-navigation-children');
                el.querySelectorAll<HTMLElement>(':scope > ul').forEach(
                    (ul) => ul.removeAttribute('style'),
                );
            }
            this.rightMostItemIndex += numberOfItems;
        }
    }
}

function outerWidthMargins(el: HTMLElement): number {
    const rect = el.getBoundingClientRect();
    const cs = window.getComputedStyle(el);
    const ml = parseFloat(cs.marginLeft) || 0;
    const mr = parseFloat(cs.marginRight) || 0;
    return rect.width + ml + mr;
}

function outerWidthNoMargins(el: HTMLElement): number {
    return el.getBoundingClientRect().width;
}

export default Navigation;

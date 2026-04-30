import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupMenus } from '../../frontend/modules/toolbar/menus';

const HOVER = 'cms-toolbar-item-navigation-hover';

function setupDom(): HTMLElement {
    // Mirror the legacy template: `.cms-toolbar-item-navigation` is the
    // `<ul>` itself (see cms/templates/cms/toolbar/toolbar.html), not a
    // `<div>` wrapping a `<ul>`. Top-level `Menu` items render with
    // `sub_level=False` (cms/toolbar/items.py:330) — i.e. WITHOUT the
    // `cms-toolbar-item-navigation-children` class. Only nested
    // `SubMenu` items carry it.
    document.body.innerHTML = `
        <div class="cms-toolbar">
            <ul class="cms-toolbar-item cms-toolbar-item-navigation">
                <li>
                    <a href="#">Page</a>
                    <ul>
                        <li><a href="/edit/">Edit</a></li>
                        <li class="cms-toolbar-item-navigation-children">
                            <a href="#">Templates</a>
                            <ul>
                                <li><a href="/t/">T1</a></li>
                            </ul>
                        </li>
                        <li class="cms-toolbar-item-navigation-disabled">
                            <a href="/disabled/">Disabled</a>
                        </li>
                    </ul>
                </li>
                <li>
                    <a href="/quick/">Quick</a>
                </li>
            </ul>
        </div>
    `;
    return document.querySelector<HTMLElement>('.cms-toolbar')!;
}

beforeEach(() => {
    setupDom();
});

afterEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
});

describe('setupMenus — basic interaction', () => {
    it('clicking a top-level li with children opens its submenu', () => {
        const toolbar = setupDom();
        const onTopLevelClick = vi.fn();
        const handle = setupMenus({ toolbar, onTopLevelClick });
        const li = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(true);
        const submenu = li.querySelector<HTMLElement>(':scope > ul')!;
        expect(submenu.style.display).toBe('');
        handle.destroy();
    });

    it('clicking outside closes an open menu', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const li = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(true);
        // Outside click on body — should NOT bubble back to li (we're
        // dispatching directly on document via a synthetic event).
        document.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(false);
        handle.destroy();
    });

    it('Esc keyup closes an open menu', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const li = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(true);
        const ev = new KeyboardEvent('keyup', { keyCode: 27 });
        Object.defineProperty(ev, 'keyCode', { value: 27 });
        window.dispatchEvent(ev);
        expect(li.classList.contains(HOVER)).toBe(false);
        handle.destroy();
    });

    it('clicking a top-level link delegates to onTopLevelClick', () => {
        const toolbar = setupDom();
        const onTopLevelClick = vi.fn();
        const handle = setupMenus({ toolbar, onTopLevelClick });
        const anchor = toolbar.querySelector<HTMLAnchorElement>(
            '.cms-toolbar-item-navigation > li:nth-child(2) > a',
        )!;
        anchor.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(onTopLevelClick).toHaveBeenCalledWith(anchor);
        handle.destroy();
    });

    it('disabled submenu items do not trigger onTopLevelClick', () => {
        const toolbar = setupDom();
        const onTopLevelClick = vi.fn();
        const handle = setupMenus({ toolbar, onTopLevelClick });
        const disabledAnchor = toolbar.querySelector<HTMLAnchorElement>(
            '.cms-toolbar-item-navigation-disabled a',
        )!;
        disabledAnchor.dispatchEvent(
            new MouseEvent('click', { bubbles: true }),
        );
        expect(onTopLevelClick).not.toHaveBeenCalled();
        handle.destroy();
    });

    it('destroy() releases listeners — outside clicks no longer reset', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const li = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        handle.destroy();
        // After destroy, hover class is cleared by the destroy reset.
        // Now a fresh outside click should not toggle it back on.
        document.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(false);
    });
});

describe('setupMenus — cursor into dropdown keeps it open', () => {
    it('pointerover on the dropdown UL itself does not remove top-level HOVER', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const topLi = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        topLi.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(topLi.classList.contains(HOVER)).toBe(true);

        const submenuUl = topLi.querySelector<HTMLElement>(':scope > ul')!;
        // Simulate cursor entering the dropdown UL itself (not a nested li).
        submenuUl.dispatchEvent(
            new Event('pointerover', { bubbles: true }),
        );
        expect(topLi.classList.contains(HOVER)).toBe(true);
        handle.destroy();
    });

    it('pointerover on a nested li keeps top-level HOVER and adds nested HOVER', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const topLi = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        topLi.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(topLi.classList.contains(HOVER)).toBe(true);

        const nestedLi = topLi.querySelector<HTMLElement>(
            ':scope > ul > li:first-child',
        )!;
        nestedLi.dispatchEvent(
            new Event('pointerover', { bubbles: true }),
        );
        expect(topLi.classList.contains(HOVER)).toBe(true);
        expect(nestedLi.classList.contains(HOVER)).toBe(true);
        handle.destroy();
    });

    it('hovering a leaf nested-li does NOT hide the dropdown UL itself', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const topLi = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        topLi.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        const submenuUl = topLi.querySelector<HTMLElement>(':scope > ul')!;
        // Sanity: the click handler removed any inline display.
        expect(submenuUl.style.display).toBe('');

        const nestedLi = topLi.querySelector<HTMLElement>(
            ':scope > ul > li:first-child',
        )!;
        // Hovering Edit (a leaf) — must not stamp `display: none` onto
        // the dropdown UL via the `nav.querySelectorAll('ul ul')` wipe.
        nestedLi.dispatchEvent(
            new Event('pointerover', { bubbles: true }),
        );
        expect(submenuUl.style.display).not.toBe('none');
        expect(topLi.classList.contains(HOVER)).toBe(true);
        handle.destroy();
    });

    it('pointerout from anchor inside top-level li does not close dropdown', () => {
        const toolbar = setupDom();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
        });
        const topLi = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        topLi.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        const anchor = topLi.querySelector<HTMLElement>(':scope > a')!;
        anchor.dispatchEvent(
            new Event('pointerout', { bubbles: true }),
        );
        expect(topLi.classList.contains(HOVER)).toBe(true);
        handle.destroy();
    });
});

describe('setupMenus — long-menus integration', () => {
    it('calls longMenus.recompute on submenu open', () => {
        const toolbar = setupDom();
        const recompute = vi.fn();
        const handle = setupMenus({
            toolbar,
            onTopLevelClick: () => {},
            longMenus: {
                recompute,
                stick: () => {},
                destroy: () => {},
            },
        });
        const li = toolbar.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation > li:first-child',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(recompute).toHaveBeenCalled();
        handle.destroy();
    });
});

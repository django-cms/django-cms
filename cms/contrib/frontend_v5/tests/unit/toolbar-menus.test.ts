import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupMenus } from '../../frontend/modules/toolbar/menus';

const HOVER = 'cms-toolbar-item-navigation-hover';

function setupDom(): HTMLElement {
    document.body.innerHTML = `
        <div class="cms-toolbar">
            <div class="cms-toolbar-item-navigation">
                <ul>
                    <li class="cms-toolbar-item-navigation-children">
                        <a href="#">Page</a>
                        <ul>
                            <li><a href="/edit/">Edit</a></li>
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
            '.cms-toolbar-item-navigation-children',
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
            '.cms-toolbar-item-navigation-children',
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
            '.cms-toolbar-item-navigation-children',
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
            '.cms-toolbar-item-navigation > ul > li:nth-child(2) > a',
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
            '.cms-toolbar-item-navigation-children',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        handle.destroy();
        // After destroy, hover class is cleared by the destroy reset.
        // Now a fresh outside click should not toggle it back on.
        document.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(li.classList.contains(HOVER)).toBe(false);
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
            '.cms-toolbar-item-navigation-children',
        )!;
        li.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(recompute).toHaveBeenCalled();
        handle.destroy();
    });
});

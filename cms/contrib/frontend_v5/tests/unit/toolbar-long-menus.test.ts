import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { setupLongMenus } from '../../frontend/modules/toolbar/long-menus';

function setupDom(): { body: HTMLElement; toolbar: HTMLElement } {
    document.body.innerHTML = `
        <div class="cms">
            <div class="cms-toolbar"></div>
            <div class="cms-toolbar-item-navigation">
                <ul>
                    <li class="cms-toolbar-item-navigation-hover">
                        <ul></ul>
                    </li>
                </ul>
            </div>
        </div>
    `;
    return {
        body: document.documentElement,
        toolbar: document.querySelector<HTMLElement>('.cms-toolbar')!,
    };
}

beforeEach(() => {
    setupDom();
});

afterEach(() => {
    document.body.innerHTML = '';
});

describe('setupLongMenus', () => {
    it('stays sticky when no menus are open', () => {
        const { body, toolbar } = setupDom();
        // Remove the hover class so no menu is "open".
        document
            .querySelector('.cms-toolbar-item-navigation-hover')!
            .classList.remove('cms-toolbar-item-navigation-hover');
        const ctrl = setupLongMenus({ body, toolbar });
        ctrl.recompute();
        expect(body.classList.contains('cms-toolbar-non-sticky')).toBe(false);
        expect(toolbar.style.top).toBe('0px');
    });

    it('unsticks when an open menu overflows the viewport', () => {
        const { body, toolbar } = setupDom();
        const ul = document.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation-hover > ul',
        )!;
        // Stub a giant rect that exceeds viewport height.
        Object.defineProperty(ul, 'getBoundingClientRect', {
            value: () => ({
                top: 0,
                left: 0,
                right: 0,
                bottom: 9999,
                width: 0,
                height: 9999,
                x: 0,
                y: 0,
                toJSON: () => ({}),
            }),
        });
        const fakeWindow = {
            innerHeight: 100,
            scrollY: 100,
        } as unknown as Window;
        const ctrl = setupLongMenus({
            body,
            toolbar,
            window: fakeWindow,
        });
        ctrl.recompute();
        expect(body.classList.contains('cms-toolbar-non-sticky')).toBe(true);
        // Top should be set to the scroll position with !important.
        expect(toolbar.style.top).toBe('100px');
        expect(toolbar.style.getPropertyPriority('top')).toBe('important');
    });

    it('re-sticks when overflowing menu is closed', () => {
        const { body, toolbar } = setupDom();
        const ul = document.querySelector<HTMLElement>(
            '.cms-toolbar-item-navigation-hover > ul',
        )!;
        Object.defineProperty(ul, 'getBoundingClientRect', {
            value: () => ({
                top: 0,
                bottom: 9999,
                width: 0,
                height: 9999,
                left: 0,
                right: 0,
                x: 0,
                y: 0,
                toJSON: () => ({}),
            }),
        });
        const ctrl = setupLongMenus({
            body,
            toolbar,
            window: { innerHeight: 100, scrollY: 100 } as unknown as Window,
        });
        ctrl.recompute();
        expect(body.classList.contains('cms-toolbar-non-sticky')).toBe(true);
        // Close the menu.
        document
            .querySelector('.cms-toolbar-item-navigation-hover')!
            .classList.remove('cms-toolbar-item-navigation-hover');
        ctrl.recompute();
        expect(body.classList.contains('cms-toolbar-non-sticky')).toBe(false);
    });

    it('stick() forces sticky regardless of state', () => {
        const { body, toolbar } = setupDom();
        body.classList.add('cms-toolbar-non-sticky');
        toolbar.style.setProperty('top', '50px', 'important');
        const ctrl = setupLongMenus({ body, toolbar });
        ctrl.stick();
        expect(body.classList.contains('cms-toolbar-non-sticky')).toBe(false);
        expect(toolbar.style.top).toBe('0px');
    });
});

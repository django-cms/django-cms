/* ========================================================================
 * Bootstrap: dropdown.js v3.3.7
 * http://getbootstrap.com/javascript/#dropdowns
 * ========================================================================
 * Copyright 2011-2016 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */

/* eslint-disable complexity, no-magic-numbers, curly */
// modified for cms purposes - event names, parent resolutions, class names

// Vanilla ES6 Dropdown für django-cms
// Migration von Bootstrap/jQuery auf native DOM-APIs

// DROPDOWN CLASS DEFINITION
// =========================


const BACKDROP_CLASS = 'cms-dropdown-backdrop';
const TOGGLE_SELECTOR = '.cms-dropdown-toggle';
const DROPDOWN_OPEN_CLASS = 'cms-dropdown-open';
const DROPDOWN_MENU_SELECTOR = '.cms-dropdown-menu';

class Dropdown {
    constructor(element) {
        element.addEventListener('click', this.toggle.bind(this));
    }

    static getParent(el) {
        return el.closest('.cms-dropdown');
    }

    static clearMenus(e) {
        if (e && e.which === 3) return;
        document.querySelectorAll('.' + BACKDROP_CLASS).forEach(bd => bd.remove());
        document.querySelectorAll(TOGGLE_SELECTOR).forEach(toggleEl => {
            const parent = Dropdown.getParent(toggleEl);

            if (!parent || !parent.classList.contains(DROPDOWN_OPEN_CLASS)) return;
            if (e && e.type === 'click' && (/input|textarea/i.test(e.target.tagName)) && parent.contains(e.target)) {
                return;
            }
            const hideEvent = new CustomEvent(
                'hide.cms.dropdown',
                { detail: { relatedTarget: toggleEl }, cancelable: true }
            );

            parent.dispatchEvent(hideEvent);
            if (hideEvent.defaultPrevented) return;
            toggleEl.setAttribute('aria-expanded', 'false');
            parent.classList.remove(DROPDOWN_OPEN_CLASS);
            parent.dispatchEvent(new CustomEvent('hidden.cms.dropdown', { detail: { relatedTarget: toggleEl } }));
        });
    }

    toggle(e) {
        const toggleEl = e.currentTarget;

        if (toggleEl.classList.contains('cms-btn-disabled') || toggleEl.disabled) return;
        const parent = Dropdown.getParent(toggleEl);
        const isActive = parent && parent.classList.contains(DROPDOWN_OPEN_CLASS);

        Dropdown.clearMenus();
        if (!isActive) {
            if ('ontouchstart' in document.documentElement && !parent.closest('.navbar-nav')) {
                const backdrop = document.createElement('div');

                backdrop.className = BACKDROP_CLASS;
                toggleEl.after(backdrop);
                backdrop.addEventListener('click', Dropdown.clearMenus);
            }
            const showEvent = new CustomEvent(
                'show.cms.dropdown',
                { detail: { relatedTarget: toggleEl }, cancelable: true }
            );

            parent.dispatchEvent(showEvent);
            if (showEvent.defaultPrevented) return;
            toggleEl.focus();
            toggleEl.setAttribute('aria-expanded', 'true');
            parent.classList.add(DROPDOWN_OPEN_CLASS);
            parent.dispatchEvent(new CustomEvent('shown.cms.dropdown', { detail: { relatedTarget: toggleEl } }));
        }
        e.preventDefault();
        return false;
    }

    keydown(e) {
        if (!/(38|40|27|32)/.test(e.which) || /input|textarea/i.test(e.target.tagName)) return;
        const toggleEl = e.currentTarget;

        e.preventDefault();
        e.stopPropagation();
        if (toggleEl.classList.contains('cms-btn-disabled') || toggleEl.disabled) return;
        const parent = Dropdown.getParent(toggleEl);
        const isActive = parent && parent.classList.contains(DROPDOWN_OPEN_CLASS);

        if ((!isActive && e.which !== 27) || (isActive && e.which === 27)) {
            if (e.which === 27) {
                parent.querySelector(TOGGLE_SELECTOR)?.focus();
            }
            return toggleEl.click();
        }
        const items = Array.from(parent.querySelectorAll(DROPDOWN_MENU_SELECTOR + ' li a'))
            .filter(a => a.offsetParent !== null && !a.closest('.cms-btn-disabled'));

        if (!items.length) return;
        let index = items.indexOf(e.target);

        if (e.which === 38 && index > 0) index--;
        if (e.which === 40 && index < items.length - 1) index++;
        if (index < 0) index = 0;
        items[index].focus();
    }
}

// Initialisierung: Event-Delegation
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', Dropdown.clearMenus);
    document.querySelectorAll('.cms-dropdown form').forEach(form => {
        form.addEventListener('click', e => e.stopPropagation());
    });
    document.querySelectorAll(TOGGLE_SELECTOR).forEach(toggleEl => {
        new Dropdown(toggleEl);
        toggleEl.addEventListener('pointerup', Dropdown.prototype.toggle);
        toggleEl.addEventListener('keydown', Dropdown.prototype.keydown);
    });
    document.querySelectorAll(DROPDOWN_MENU_SELECTOR).forEach(menu => {
        menu.addEventListener('keydown', Dropdown.prototype.keydown);
    });
});

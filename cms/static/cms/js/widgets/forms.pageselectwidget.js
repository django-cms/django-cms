/*
 * Copyright https://github.com/django-cms/django-cms
 */

// this essentially makes sure that dynamically required bundles are loaded
// from the same place
// eslint-disable-next-line
__webpack_public_path__ = require('../modules/get-dist-path')('bundle.forms.pageselectwidget');

// #############################################################################
// PAGE SELECT WIDGET
// cms/forms/widgets.py

/**
 * Manages the selection of two select fields. The first field
 * sets the "Site" and the second the "Pagetree".
 *
 * @class PageSelectWidget
 * @namespace CMS
 */
class PageSelectWidget {
    constructor(options) {
        this.options = Object.assign({}, options);
        this._setup(options);
    }

    /**
     * Setup internal functions and events.
     *
     * @private
     * @method _setup
     * @param {Object} options
     * @param {String} options.name
     */
    _setup(options) {
        const group0 = document.getElementById('id_' + options.name + '_0');
        const group1 = document.getElementById('id_' + options.name + '_1');
        const group2 = document.getElementById('id_' + options.name + '_2');
        const addBtn = document.getElementById('add_id_' + options.name);
        let tmp;

        if (addBtn) {
            addBtn.style.display = 'none';
        }

        if (group0 && group1 && group2) {
            group0.addEventListener('change', function () {
                const selected = group0.options[group0.selectedIndex];

                tmp = selected ? selected.textContent : '';

                // Remove all optgroups from group1
                Array.from(group1.querySelectorAll('optgroup')).forEach(og => og.remove());
                // Find matching optgroup in group2 and clone it into group1
                const match = Array.from(group2.querySelectorAll('optgroup')).find(og => og.label === tmp);

                if (match) {
                    group1.appendChild(match.cloneNode(true));
                }
                // Refresh second select
                setTimeout(() => {
                    group1.dispatchEvent(new Event('change'));
                }, 0);
            });
            // Initial trigger
            group0.dispatchEvent(new Event('change'));

            group1.addEventListener('change', function () {
                const selected = group1.options[group1.selectedIndex];

                tmp = selected ? selected.value : '';
                if (tmp) {
                    Array.from(group2.options).forEach(opt => {
                        opt.selected = false;
                    });
                    const match = Array.from(group2.options).find(opt => opt.value === tmp);

                    if (match) {
                        match.selected = true;
                    }
                } else if (group2.options.length) {
                    const emptyOpt = Array.from(group2.options).find(opt => opt.value === '');

                    if (emptyOpt) {
                        emptyOpt.selected = true;
                    }
                }
            });
        }
    }
}

window.CMS = window.CMS || {};
window.CMS.PageSelectWidget = PageSelectWidget;

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-cms-widget-pageselect]').forEach(function (el) {
        const widget = JSON.parse(el.querySelector('script').textContent);

        new PageSelectWidget(widget);
    });
});

/*
 * Copyright https://github.com/divio/django-cms
 */

/**
 * @module CMS
 */
/* istanbul ignore next */
var CMS = window.CMS || {};

(function ($) {
    'use strict';

    /**
     * Dropdowns in the pagetree.
     * Have to be delegated, since pagetree nodes can be
     * lazy loaded.
     *
     * @class PageTreeDropdowns
     * @namespace CMS
     */
    CMS.PageTreeDropdowns = new CMS.Class({
        options: {
            dropdownSelector: '.js-cms-pagetree-dropdown',
            triggerSelector: '.js-cms-pagetree-dropdown-trigger',
            menuSelector: '.js-cms-pagetree-dropdown-menu',
            openCls: 'cms-pagetree-dropdown-menu-open'
        },

        initialize: function initialize(options) {
            this.options = $.extend(true, {}, this.options, options);
            this.click = 'click.cms.pagetree.dropdown';

            this._setupUI();
            this._events();
        },

        /**
         * @method _setupUI
         * @private
         */
        _setupUI: function _setupUI() {
            this.ui = {
                container: this.options.container,
                document: $(document)
            };
        },

        /**
         * Event handlers.
         *
         * @method _events
         * @private
         */
        _events: function _events() {
            var that = this;

            // attach event to the trigger
            this.ui.container.on(this.click, this.options.triggerSelector, function (e) {
                e.preventDefault();
                e.stopImmediatePropagation();

                that._toggleDropdown(this);
            });

            // stop propagation on the element
            this.ui.container.on(this.click, that.options.menuSelector, function (e) {
                e.stopImmediatePropagation();
            });

            this.ui.container.on(this.click, that.options.menuSelector + ' a', function () {
                that.closeAllDropdowns();
            });

            this.ui.document.on(this.click, function () {
                that.closeAllDropdowns();
            });
        },

        /**
         * @method _toggleDropdown
         * @param {jQuery} trigger trigger clicked
         * @private
         * @returns {Boolean|void}
         */
        _toggleDropdown: function _toggleDropdown(trigger) {
            var triggers = $(this.options.triggerSelector);
            var dropdowns = $(this.options.dropdownSelector);
            var index = triggers.index(trigger);

            // cancel if opened tooltip is triggered again
            if (dropdowns.eq(index).hasClass(this.options.openCls)) {
                dropdowns.removeClass(this.options.openCls);
                return false;
            }

            // otherwise show the dropdown
            dropdowns
                .removeClass(this.options.openCls)
                .eq(index)
                .addClass(this.options.openCls);
        },

        /**
         * @method closeAllDropdowns
         * @public
         */
        closeAllDropdowns: function closeAllDropdowns() {
            $(this.options.dropdownSelector).removeClass(this.options.openCls);
        }
    });

})(CMS.$);

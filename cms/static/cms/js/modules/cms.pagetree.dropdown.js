var $ = require('jquery');
var Class = require('classjs');

/**
 * Dropdowns in the pagetree.
 * Have to be delegated, since pagetree nodes can be
 * lazy loaded.
 *
 * @class PageTreeDropdowns
 * @namespace CMS
 */
var PageTreeDropdowns = new Class({
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
        var dropdowns = $(this.options.dropdownSelector);
        var dropdown = $(trigger).closest(this.options.dropdownSelector);

        // cancel if opened tooltip is triggered again
        if (dropdown.hasClass(this.options.openCls)) {
            dropdowns.removeClass(this.options.openCls);
            return false;
        }

        // otherwise show the dropdown
        dropdowns.removeClass(this.options.openCls);
        dropdown.addClass(this.options.openCls);

        this._loadContent(dropdown);
    },

    /**
     * @method _loadContent
     * @private
     * @param {jQuery} dropdown
     * @returns {Boolean|$.Deferred} false if not lazy or already loaded or promise
     */
    _loadContent: function _loadContent(dropdown) {
        var data = dropdown.data();
        var LOADER_SHOW_TIMEOUT = 200;

        if (!data.lazyUrl || data.loaded) {
            return false;
        }

        var loaderTimeout = setTimeout(function () {
            dropdown.find('.js-cms-pagetree-dropdown-loader').addClass('cms-loader');
        }, LOADER_SHOW_TIMEOUT);

        $.ajax({
            url: data.lazyUrl,
            data: data.lazyUrlData
        }).done(function (response) {
            dropdown.find('.js-cms-pagetree-dropdown-menu').html(response);
            dropdown.data('loaded', true);
            clearTimeout(loaderTimeout);
        });
    },

    /**
     * @method closeAllDropdowns
     * @public
     */
    closeAllDropdowns: function closeAllDropdowns() {
        $(this.options.dropdownSelector).removeClass(this.options.openCls);
    }
});

module.exports = PageTreeDropdowns;

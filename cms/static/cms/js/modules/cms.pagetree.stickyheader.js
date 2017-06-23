/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';
import Class from 'classjs';
import { Helpers } from './cms.base';

/**
 * Sticky language headers in pagetree
 *
 * @class PageTreeStickyHeader
 * @namespace CMS
 */
var PageTreeStickyHeader = new Class({
    initialize: function initialize(options) {
        var that = this;

        that.options = $.extend(true, {}, that.options, options);
        that.resize = 'resize.cms.pagetree.header';
        that.scroll = 'scroll.cms.pagetree.header';
        that.areClonesInDOM = false;

        that._setupUI();
        that._saveSizes();
        that._events();
    },

    /**
     * @method _setupUI
     * @private
     */
    _setupUI: function _setupUI() {
        var container = this.options.container;
        var headers = container.find('.jstree-grid-header');

        this.ui = {
            container: container,
            window: $(window),
            headers: headers,
            columns: container.find('.jstree-grid-column').toArray().map(function(el) {
                return $(el);
            }),
            clones: headers.clone().toArray().map(function(el) {
                return $(el);
            })
        };
    },

    /**
     * Determines positions/sizes of elements
     *
     * @method _saveSizes
     * @private
     */
    _saveSizes: function _saveSizes() {
        this.headersTopOffset = this.ui.headers.offset().top;
        this.toolbarHeight = 0;
        if (this._isInSideframe()) {
            this.toolbarHeight = CMS.API.Helpers._getWindow().parent.CMS.$('.cms-toolbar').height();
        } else {
            this.toolbarHeight = $('#branding').height();
        }
    },

    /**
     * @method _isInSideframe
     * @returns {Boolean} are we in sideframe?
     * @private
     */
    _isInSideframe: function() {
        var win = Helpers._getWindow();

        if (win && win.parent && win.parent !== win) {
            return true;
        }

        return false;
    },

    /**
     * Event handlers.
     *
     * @method _events
     * @private
     */
    _events: function _events() {
        this.ui.window.on([this.resize, this.scroll].join(' '), this._handleResizeOrScroll.bind(this));
    },

    /**
     * @method _handleResizeOrScroll
     * @private
     */
    _handleResizeOrScroll: function _handleResizeOrScroll() {
        var that = this;
        var scrollTop = that.ui.window.scrollTop();
        var scrollLeft = that.ui.window.scrollLeft();

        if (that._shouldStick(scrollTop)) {
            that._stickHeader(scrollTop, scrollLeft);
        } else {
            that._unstickHeader();
        }
    },

    /**
     * @method _shouldStick
     * @param {Number} scrollTop position in pixels
     * @returns {Boolean} should headers stick
     * @private
     */
    _shouldStick: function(scrollTop) {
        return scrollTop + this.toolbarHeight >= this.headersTopOffset;
    },

    /**
     * @method _stickHeader
     * @param {Number} scrollTop top
     * @param {Number} scrollLeft left
     * @private
     */
    _stickHeader: function _stickHeader(scrollTop, scrollLeft) {
        var that = this;

        that._insertClones();

        that.ui.headers.each(function(index) {
            var el = $(this);

            var width = that.ui.clones[index].css('width');
            var offset = that.ui.clones[index].offset().left;

            el.css({
                width: width,
                left: offset - scrollLeft
            });
        });

        that.ui.headers.addClass('jstree-grid-header-fixed').css({
            top: that.toolbarHeight
        });
    },

    /**
     * @method _unstickHeader
     * @private
     */
    _unstickHeader: function _unstickHeader() {
        var that = this;

        that._detachClones();

        that.ui.headers.removeClass('jstree-grid-header-fixed').css({
            top: 0,
            width: 'auto',
            left: 'auto'
        });
    },

    /**
     * Inserts clones of headers so when header becomes sticky the
     * pagetree doesn't jump. Only does it once and sets the flag.
     *
     * @method _insertClones
     * @private
     */
    _insertClones: function _insertClones() {
        var that = this;

        if (!that.areClonesInDOM) {
            that.ui.columns.forEach(function(el, index) {
                el.prepend(that.ui.clones[index]);
            });
            that.areClonesInDOM = true;
        }
    },

    /**
     * Detaches the clones of headers so then headers "unsticks"
     * the pagetree doesn't jump. Relies on the flag.
     *
     * @method _detachClones
     * @private
     */
    _detachClones: function _detachClones() {
        var that = this;

        if (that.areClonesInDOM) {
            that.ui.clones.forEach(function(el) {
                el.detach();
            });
            that.areClonesInDOM = false;
        }
    }
});

export default PageTreeStickyHeader;

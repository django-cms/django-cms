/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
var CMS = window.CMS || {};

// #############################################################################
// Toolbar
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * Responsible for creating usable navigation for narrow screens.
         *
         * @class Navigation
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.Navigation = new CMS.Class({

            implement: [CMS.API.Helpers],

            initialize: function initialize() {
                this._setupUI();
                this.getWidths();

                /** The zero based index of the right-most visible nav menu item. */
                this.rightMostItemIndex = this.items.left.length - 1;

                this._events();
            },

            /**
             * Cache UI jquery objects
             * @method _setupUI
             * @private
             */
            _setupUI: function _setupUI() {
                var trigger = $('.cms-toolbar-more');
                this.ui = {
                    window: $(window),
                    toolbarLeftPart: $('.cms-toolbar-left'),
                    toolbarRightPart: $('.cms-toolbar-right'),
                    trigger: trigger,
                    dropdown: trigger.find('> ul'),
                    toolbarTrigger: $('.cms-toolbar-trigger'),
                    logo: $('.cms-toolbar-item-logo')
                };
            },

            /**
             * Setup resize handler to construct the dropdown
             * @method _events
             * @private
             */
            _events: function _events() {
                this.ui.window.on('resize.cms load.cms', CMS.API.Helpers.throttle(
                    this._handleResize.bind(this), 50
                ));
            },

            /**
             * Calculates all the movable menu items widths
             * @method _getWidths
             */
            getWidths: function getWidths() {
                var that = this;
                that.items = {
                    left: [],
                    leftTotalWidth: 0,
                    right: [],
                    rightTotalWidth: 0,
                    moreButtonWidth: 0
                };
                var leftItems = that.ui.toolbarLeftPart
                    .find('.cms-toolbar-item-navigation > li:not(.cms-toolbar-more)');
                var rightItems = that.ui.toolbarRightPart.find('> .cms-toolbar-item');

                var getSize = function getSize(el, store) {
                    var element = $(el);
                    var width = $(el).outerWidth(true);

                    store.push({
                        element: element,
                        width: width
                    });
                };
                var sumWidths = function sumWidths(sum, item) {
                    return sum + item.width;
                };

                leftItems.each(function () {
                    getSize(this, that.items.left);
                });

                rightItems.each(function () {
                    getSize(this, that.items.right);
                });

                that.items.leftTotalWidth = that.items.left.reduce(sumWidths, 0);
                that.items.rightTotalWidth = that.items.right.reduce(sumWidths, 0);
                that.items.moreButtonWidth = that.ui.trigger.outerWidth();
            },

            /**
             * Calculates available width based on the state of the page
             * @method calculateAvailableWidth
             */
            calculateAvailableWidth: function calculateAvailableWidth() {
                var fullWidth = this.ui.window.width();
                var reduce = this.ui.toolbarTrigger.width() + this.ui.logo.offset().left +
                    this.ui.logo.outerWidth(true);

                return fullWidth - reduce;
            },

            /**
             * Shows the dropdown
             *
             * @method showDropdown
             */
            showDropdown: function showDropdown() {
                this.ui.trigger.show();
            },

            /**
             * Hides the dropdown
             *
             * @method hideDropdown
             */
            hideDropdown: function hideDropdown() {
                this.ui.trigger.hide();
            },

            /**
             * Figures out if we need to show/hide/modify the dropdown
             *
             * @method _handleResize
             * @private
             */
            _handleResize: function _handleResize() {
                var remainingWidth;
                var availableWidth = this.calculateAvailableWidth();

                if (availableWidth > this.items.leftTotalWidth + this.items.rightTotalWidth) {
                    this.showAll();
                } else {
                    // first handle the left part
                    remainingWidth = availableWidth - this.items.moreButtonWidth -
                        this.ui.toolbarRightPart.width();

                    // Figure out how many nav menu items fit into the available space.
                    var newRightMostItemIndex = -1;
                    while (remainingWidth - this.items.left[newRightMostItemIndex + 1].width >= 0) {
                        remainingWidth -= this.items.left[newRightMostItemIndex + 1].width;
                        newRightMostItemIndex++;
                    }

                    if (newRightMostItemIndex < this.rightMostItemIndex) {
                        this.moveToDropdown(this.rightMostItemIndex - newRightMostItemIndex);
                    } else if (this.rightMostItemIndex < newRightMostItemIndex) {
                        this.moveOutOfDropdown(newRightMostItemIndex - this.rightMostItemIndex);
                    }
                    this.showDropdown();
                }
            },

            /**
             * Hides and empties dropdown
             *
             * @method showAll
             */
            showAll: function showAll() {
                this.moveOutOfDropdown((this.items.left.length - 1) - this.rightMostItemIndex);
                this.hideDropdown();
            },

            /**
             * Moves items into the dropdown
             *
             * @param numberOfItems Number how many items to move to dropdown
             */
            moveToDropdown: function moveToDropdown(numberOfItems) {
                if (numberOfItems <= 0) {
                    return;
                }

                // Move items (working right-to-left) from the nav bar to the more menu.
                var item;
                var rightMostIndexToMove = this.rightMostItemIndex;
                var leftMostIndexToMove = this.rightMostItemIndex - numberOfItems + 1;
                for (var i = rightMostIndexToMove; i >= leftMostIndexToMove; i--) {
                    item = this.items.left[i].element;

                    this.ui.dropdown.prepend(item);
                    if (item.find('> ul').children().length) {
                        item.addClass('cms-toolbar-item-navigation-children');
                    }
                }

                this.rightMostItemIndex -= numberOfItems;
            },

            /**
             * Moves items out of the dropdown
             *
             * @param numberOfItems Number how many items to move out of the dropdown
             */
            moveOutOfDropdown: function moveOutOfDropdown(numberOfItems) {
                if (numberOfItems <= 0) {
                    return;
                }

                // Move items (working top-to-bottom) from the more menu into the nav bar.
                var item;
                var leftMostIndexToMove = this.rightMostItemIndex + 1;
                var rightMostIndexToMove = this.rightMostItemIndex + numberOfItems;

                for (var i = leftMostIndexToMove; i <= rightMostIndexToMove; i++) {
                    item = this.items.left[i].element;

                    item.insertBefore(this.ui.trigger);
                    item.removeClass('cms-toolbar-item-navigation-children');
                    item.find('> ul').removeAttr('style');
                }

                this.rightMostItemIndex += numberOfItems;
            }

        });

    });
})(CMS.$);

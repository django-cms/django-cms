/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';
import { throttle } from 'lodash';

/**
 * Responsible for creating usable navigation for narrow screens.
 *
 * @class Navigation
 * @namespace CMS
 */
class Navigation {
    constructor() {
        this._setupUI();
        this._getWidths();

        /**
         * The zero based index of the right-most visible menu item of the left toolbar part.
         *
         * @property rightMostItemIndex {Number}
         */
        this.rightMostItemIndex = this.items.left.length - 1;

        /**
         * The zero based index of the left-most visible item of the right toolbar part.
         *
         * @property leftMostItemIndex {Number}
         */
        this.leftMostItemIndex = 0;

        this.resize = 'resize.cms.navigation';
        this.load = 'load.cms.navigation';
        this.orientationChange = 'orientationchange.cms.navigation';

        this._events();
    }

    /**
     * Cache UI jquery objects.
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
        var container = $('.cms');
        var trigger = container.find('.cms-toolbar-more');

        this.ui = {
            window: $(window),
            toolbarLeftPart: container.find('.cms-toolbar-left'),
            toolbarRightPart: container.find('.cms-toolbar-right'),
            trigger: trigger,
            dropdown: trigger.find('> ul'),
            toolbarTrigger: container.find('.cms-toolbar-trigger'),
            logo: container.find('.cms-toolbar-item-logo')
        };
    }

    /**
     * Setup resize handler to construct the dropdown.
     *
     * @method _events
     * @private
     */
    _events() {
        var THROTTLE_TIMEOUT = 50;

        this.ui.window
            .off([this.resize, this.load, this.orientationChange].join(' '))
            .on(
                [this.resize, this.load, this.orientationChange].join(' '),
                throttle(this._handleResize.bind(this), THROTTLE_TIMEOUT)
            );
    }

    /**
     * Calculates all the movable menu items widths.
     *
     * @method _getWidths
     * @private
     */
    _getWidths() {
        var that = this;

        that.items = {
            left: [],
            leftTotalWidth: 0,
            right: [],
            rightTotalWidth: 0,
            moreButtonWidth: 0
        };
        var leftItems = that.ui.toolbarLeftPart.find('.cms-toolbar-item-navigation > li:not(.cms-toolbar-more)');
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

        leftItems.each(function() {
            getSize(this, that.items.left);
        });

        rightItems.each(function() {
            getSize(this, that.items.right);
        });

        that.items.leftTotalWidth = that.items.left.reduce(sumWidths, 0);
        that.items.rightTotalWidth = that.items.right.reduce(sumWidths, 0);
        that.items.moreButtonWidth = that.ui.trigger.outerWidth();
    }

    /**
     * Calculates available width based on the state of the page.
     *
     * @method _calculateAvailableWidth
     * @private
     * @returns {Number} available width in px
     */
    _calculateAvailableWidth() {
        var fullWidth = this.ui.window.width();
        var reduce = parseInt(this.ui.toolbarRightPart.css('padding-inline-end'), 10) + this.ui.logo.outerWidth(true);

        return fullWidth - reduce;
    }

    /**
     * Shows the dropdown.
     *
     * @method _showDropdown
     * @private
     */
    _showDropdown() {
        this.ui.trigger.css('display', 'list-item');
    }

    /**
     * Hides the dropdown.
     *
     * @method _hideDropdown
     * @private
     */
    _hideDropdown() {
        this.ui.trigger.css('display', 'none');
    }

    /**
     * Figures out if we need to show/hide/modify the dropdown.
     *
     * @method _handleResize
     * @private
     */
    _handleResize() {
        var remainingWidth;
        var availableWidth = this._calculateAvailableWidth();

        if (availableWidth > this.items.leftTotalWidth + this.items.rightTotalWidth) {
            this._showAll();
        } else {
            // first handle the left part
            remainingWidth = availableWidth - this.items.moreButtonWidth - this.items.rightTotalWidth;

            // Figure out how many nav menu items fit into the available space.
            var newRightMostItemIndex = -1;

            while (remainingWidth - this.items.left[newRightMostItemIndex + 1].width >= 0) {
                remainingWidth -= this.items.left[newRightMostItemIndex + 1].width;
                newRightMostItemIndex++;
            }

            if (newRightMostItemIndex < this.rightMostItemIndex) {
                this._moveToDropdown(this.rightMostItemIndex - newRightMostItemIndex);
            } else if (this.rightMostItemIndex < newRightMostItemIndex) {
                this._moveOutOfDropdown(newRightMostItemIndex - this.rightMostItemIndex);
            }

            this._showDropdown();

            // if we do not have any width left and all the items from the left part
            // are already in the dropdown - start with the right part
            if (remainingWidth < 0 && this.rightMostItemIndex === -1) {
                remainingWidth += this.items.rightTotalWidth;

                var newLeftMostItemIndex = this.items.right.length;

                // istanbul ignore if: this moves items to the right one by one
                // eslint-disable-next-line no-constant-condition
                if (false) {
                    // if you want to move items from the right one by one
                    while (remainingWidth - this.items.right[newLeftMostItemIndex - 1].width > 0) {
                        remainingWidth -= this.items.right[newLeftMostItemIndex - 1].width;
                        newLeftMostItemIndex--;
                    }

                    if (newLeftMostItemIndex > this.leftMostItemIndex) {
                        this._moveToDropdown(newLeftMostItemIndex - this.leftMostItemIndex, 'right');
                    } else if (newLeftMostItemIndex < this.leftMostItemIndex) {
                        this._moveOutOfDropdown(this.leftMostItemIndex - newLeftMostItemIndex, 'right');
                    }
                } else {
                    // but for now we want to move all of them immediately
                    this._moveToDropdown(newLeftMostItemIndex - this.leftMostItemIndex, 'right');
                    this.ui.dropdown.addClass('cms-more-dropdown-full');
                }
            } else {
                this._showAllRight();
                this.ui.dropdown.removeClass('cms-more-dropdown-full');
            }
        }
    }

    /**
     * Hides and empties dropdown.
     *
     * @method _showAll
     * @private
     */
    _showAll() {
        this._showAllLeft();
        this._showAllRight();
        this._hideDropdown();
    }

    /**
     * Show all items in the left part of the toolbar.
     *
     * @method _showAllLeft
     * @private
     */
    _showAllLeft() {
        this._moveOutOfDropdown(this.items.left.length - 1 - this.rightMostItemIndex);
    }

    /**
     * Show all items in the right part of the toolbar.
     *
     * @method _showAllRight
     * @private
     */
    _showAllRight() {
        this._moveOutOfDropdown(this.leftMostItemIndex, 'right');
    }

    /**
     * Moves items into the dropdown, reducing menu right-to-left in case it's a left part of toolbar
     * and left-to-right if it's right one.
     *
     * @method _moveToDropdown
     * @private
     * @param {Number} numberOfItems how many items to move to dropdown
     * @param {String} part from which part to move to dropdown (defaults to left)
     */
    _moveToDropdown(numberOfItems, part) {
        if (numberOfItems <= 0) {
            return;
        }

        var item;
        var leftMostIndexToMove;
        var rightMostIndexToMove;
        var i;

        if (part === 'right') {
            // Move items (working left-to-right) from the toolbar left part to the more menu.
            leftMostIndexToMove = this.leftMostItemIndex;
            rightMostIndexToMove = this.leftMostItemIndex + numberOfItems - 1;
            for (i = leftMostIndexToMove; i <= rightMostIndexToMove; i++) {
                item = this.items.right[i].element;

                this.ui.dropdown.prepend(item.wrap('<li class="cms-more-buttons"></li>').parent());
            }

            this.leftMostItemIndex += numberOfItems;
        } else {
            // Move items (working right-to-left) from the toolbar left part to the more menu.
            rightMostIndexToMove = this.rightMostItemIndex;
            leftMostIndexToMove = this.rightMostItemIndex - numberOfItems + 1;
            for (i = rightMostIndexToMove; i >= leftMostIndexToMove; i--) {
                item = this.items.left[i].element;

                this.ui.dropdown.prepend(item);
                if (item.find('> ul').children().length) {
                    item.addClass('cms-toolbar-item-navigation-children');
                }
            }

            this.rightMostItemIndex -= numberOfItems;
        }
    }

    /**
     * Moves items out of the dropdown.
     *
     * @method _moveOutOfDropdown
     * @private
     * @param {Number} numberOfItems how many items to move out of the dropdown
     * @param {String} part to which part to move out of dropdown (defaults to left)
     */
    _moveOutOfDropdown(numberOfItems, part) {
        if (numberOfItems <= 0) {
            return;
        }

        var i;
        var item;
        var leftMostIndexToMove;
        var rightMostIndexToMove;

        if (part === 'right') {
            // Move items (working bottom-to-top) from the more menu into the toolbar right part.
            rightMostIndexToMove = this.leftMostItemIndex - 1;
            leftMostIndexToMove = this.leftMostItemIndex - numberOfItems;

            for (i = rightMostIndexToMove; i >= leftMostIndexToMove; i--) {
                item = this.items.right[i].element;
                item.unwrap('<li></li>');

                item.prependTo(this.ui.toolbarRightPart);
            }

            this.leftMostItemIndex -= numberOfItems;
        } else {
            // Move items (working top-to-bottom) from the more menu into the toolbar left part.
            leftMostIndexToMove = this.rightMostItemIndex + 1;
            rightMostIndexToMove = this.rightMostItemIndex + numberOfItems;

            for (i = leftMostIndexToMove; i <= rightMostIndexToMove; i++) {
                item = this.items.left[i].element;

                item.insertBefore(this.ui.trigger);
                item.removeClass('cms-toolbar-item-navigation-children');
                item.find('> ul').removeAttr('style');
            }

            this.rightMostItemIndex += numberOfItems;
        }
    }
}

export default Navigation;

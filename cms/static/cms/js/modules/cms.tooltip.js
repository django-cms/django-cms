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
// Tooltip
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * The tooltip is the element which shows over plugins
         * and suggests clicking/tapping them to edit.
         *
         * @class Tooltip
         * @namespace CMS
         */
        CMS.Tooltip = new CMS.Class({

            initialize: function () {
                this.body = $('body');
                this.isTouch = false;
                this.domElem = this.pick();

                this.checkTouch();
            },

            /**
             * Checks for touch event and switches to touch tooltip if detected
             *
             * @method checkTouch
             * @private
             */
            checkTouch: function () {
                var that = this;

                this.body.one('touchstart.cms', function () {
                    that.isTouch = true;
                    that.domElem = that.pick();

                    // attach tooltip event for touch devices
                    that.domElem.on('touchstart.cms', function () {
                        $('.cms-plugin-' + $(this).data('plugin_id')).trigger('dblclick');
                    });
                });
            },

            /**
             * Manages show/hide calls
             *
             * @method displayToggle
             * @private
             * @param isShown {Boolean}
             * @param e {Object}
             * @param name {String} - current plugin name
             * @param id {String} - current plugin id
             */
            displayToggle: function (isShown, e, name, id) {
                isShown ? this.show(e, name, id) : this.hide();
            },

            /**
             * Shows tooltip with specific plugin-related parameters
             *
             * @method show
             * @private
             * @param e {Object}
             * @param name {String} - current plugin name
             * @param id {String} - current plugin id
             */
            show: function (e, name, id) {
                var tooltip = this.domElem;
                var that = this;

                // change css and attributes
                tooltip.css('visibility', 'visible')
                    .data('plugin_id', id || null)
                    .show()
                    .find('span').html(name);

                if (this.isTouch) {
                    this.position(e, tooltip);
                } else {
                    // attaches move event
                    // this sets the correct position for the edit tooltip
                    this.body.on('mousemove.cms', function (e) {
                        that.position(e, tooltip);
                    });
                }
            },

            /**
             * Hides tooltip
             *
             * @method hide
             * @private
             */
            hide: function () {
                // change css
                this.domElem.css('visibility', 'hidden').hide();

                // unbind events
                if (!this.isTouch) {
                    this.body.off('mousemove.cms');
                }
            },

            /**
             * Picks tooltip to show (touch or desktop)
             *
             * @method pick
             * @private
             */
            pick: function () {
                return this.isTouch ? $('.cms-tooltip-touch') : $('.cms-tooltip');
            },

            /**
             * Positions tooltip next to the pointer event coordinates
             *
             * @method position
             * @private
             * @param e {Object}
             * @param tooltip {Object}
             */
            position: function (e, tooltip) {
                // so lets figure out where we are
                var offset = 20;
                var relX = e.pageX - $(tooltip).offsetParent().offset().left;
                var relY = e.pageY - $(tooltip).offsetParent().offset().top;
                var bound = $(tooltip).offsetParent().width();
                var pos = relX + tooltip.outerWidth(true) + offset;

                tooltip.css({
                    left: (pos >= bound) ? relX - tooltip.outerWidth(true) - offset : relX + offset,
                    top: relY - 12
                });
            }

        });
    });
})(CMS.$);

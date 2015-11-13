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
                /**
                 * Are we on touch device?
                 *
                 * @property {Boolean} isTouch
                 */
                this.isTouch = false;
                /**
                 * Tooltip DOM element
                 *
                 * @property {jQuery} domElem
                 */
                this.domElem = this._pick();

                this._checkTouch();
            },

            /**
             * Checks for touch event and switches to touch tooltip if detected.
             *
             * @method checkTouch
             * @private
             */
            _checkTouch: function () {
                var that = this;

                this.body.one('touchstart.cms', function () {
                    that.isTouch = true;
                    that.domElem = that._pick();

                    // attach tooltip event for touch devices
                    that.domElem.on('touchstart.cms', function () {
                        var id = $(this).data('plugin_id');
                        var plugin = $('.cms-plugin-' + id);
                        // check if it is a normal plugin or a generic
                        if (plugin.length) {
                            plugin.trigger('dblclick.cms');
                        } else {
                            // generics are added through the content mode via special
                            // template tags some generic element might be
                            // cms-plugin-cms-page-changelist-x
                            var generic = $('.cms-plugin[class*="cms-plugin-cms-"][class*="-' + id + '"]');
                            generic.eq(0).trigger('dblclick.cms');
                        }
                    });
                });
            },

            /**
             * Manages show/hide calls.
             *
             * @method displayToggle
             * @param {Boolean} isShown
             * @param {Object} e event object
             * @param {String} name current plugin name
             * @param {String} id current plugin id
             */
            displayToggle: function (isShown, e, name, id) {
                isShown ? this.show(e, name, id) : this.hide();
            },

            /**
             * Shows tooltip with specific plugin-related parameters
             *
             * @method show
             * @param {Object} e
             * @param {String} name current plugin name
             * @param {String} id current plugin id
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
                    this.position(e.originalEvent, tooltip);
                } else {
                    // attaches move event
                    // this sets the correct position for the edit tooltip
                    that.position(e.originalEvent, tooltip);
                    this.body.on('mousemove.cms', function (e) {
                        that.position(e, tooltip);
                    });
                }
            },

            /**
             * Hides tooltip
             *
             * @method hide
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
             * Picks tooltip to show (touch or desktop).
             *
             * @method _pick
             * @private
             */
            _pick: function () {
                $('.cms-tooltip-touch, .cms-tooltip').css('visibility', 'hidden').hide();
                return this.isTouch ? $('.cms-tooltip-touch') : $('.cms-tooltip');
            },

            /**
             * Positions tooltip next to the pointer event coordinates.
             *
             * @method position
             * @private
             * @param {Object} e event object
             * @param {jQuery} tooltip element
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

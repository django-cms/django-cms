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
                this.isTouch = false;
                this.domElem = this.pick();

                this.checkTouch();
            },

            checkTouch: function () {
                var that = this;

                $('body').one('touchstart.cms', function () {
                    that.isTouch = true;
                    that.domElem = that.pick();
                });
            },

            displayToggle: function (isShown, e, name, id) {
                isShown ? CMS.API.Tooltip.show(e, name, id) : CMS.API.Tooltip.hide();
            },

            // handles the tooltip for the plugins
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

                    // attach tooltip event for touch devices
                    tooltip.bind('touchstart.cms', function () {
                        $('.cms-plugin-' + $(this).data('plugin_id')).trigger('dblclick');
                    });
                } else {
                    // attaches move event
                    // this sets the correct position for the edit tooltip
                    $('body').bind('mousemove.cms', function (e) {
                        that.position(e, tooltip);
                    });
                }
            },

            hide: function () {
                var tooltip = this.domElem;

                // change css
                tooltip.css('visibility', 'hidden').hide();

                // unbind events
                $('body').unbind('mousemove.cms');
                if (this.isTouch) {
                    tooltip.unbind('touchstart.cms');
                }
            },

            pick: function () {
                return this.isTouch ? $('.cms-tooltip-touch') : $('.cms-tooltip');
            },

            position: function (e, tooltip) {
                // so lets figure out where we are
                var offset = 20;
                var relX = e.pageX - $(tooltip).offsetParent().offset().left;
                var relY = e.pageY - $(tooltip).offsetParent().offset().top;
                var bound = $(tooltip).offsetParent().width();
                var pos = relX + tooltip.outerWidth(true) + offset;

                tooltip.css({
                    'left': (pos >= bound) ? relX - tooltip.outerWidth(true) - offset : relX + offset,
                    'top': relY - 12
                });
            }

        });
    });
})(CMS.$);

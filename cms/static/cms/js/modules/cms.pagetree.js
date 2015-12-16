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
// MODAL
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {

        // shifts options element inside the node
        $.jstree.plugins.options = function (options, parent) {
            var buttons = '.cms-tree-data';

            // what happens when redrawing
            this.redraw_node = function (obj, deep, callback, force_draw) {
                // default draw method
                obj = parent.redraw_node.call(this, obj, deep, callback, force_draw);

                // we need to append the options bar after the <li> as additional
                // options cannot be rendered within an anchor
                if (obj) {
                    var el = $(obj);
                    var tmp = el.find(buttons);

                    el.append(tmp);
                }

                // return the object
                return obj;
            };
        };

        /**
         * TODO
         *
         * @class PageTree
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        // TODO col sync needs to be implemented when resizing
        // TODO we need to implement the hover filtering
        // TODO implement success feedback when moving a tree item (that.options.lang.success)
        // TODO implement error handling when tree couldnt be moved (that.options.lang.error)
        // TODO make sure static path is not hard coded
        // TODO implement dialog for copy permissions
        /* TODO avialable ajax requests:
        *  'cms/page/' + pageId + '/change-navigation/?language=' + language (used for filtering)
        *  > loaded for first initialization
        *  > need to pass "data.fitlered = 1"
        *  > might need to consider site: { 1: 1 }
        *  'cms/page/' + pageId + '/' + language + '/descendants/'
        *  > loading decendents of a closed item
        *  'cms/page/' + item_id + '/dialog/copy/'
        *  > triggers the permission conform dialog
        *  > copy an item into new ancestor with
        *  > { position: position, target: target_id, site: site }
        *  'cms/page/' + item_id + '/copy-page/
        *  > same as above but triggers the actual move
        *  'cms/page/' + item_id + '/move-page/
        *  > { position: position, target: target_id, site: site }
        */
        CMS.PageTree = new CMS.Class({

            implement: [CMS.API.Helpers],

            initialize: function initialize(options) {
                // options are loaded from the pagetree html node
                this.options = $('.js-cms-pagetree').data('json');
                this.options = $.extend(true, {}, this.options, options);

                // elements
                this._setupUI();

                // states and events
                this.click = 'click.cms.pagetree';

                // make sure that ajax request send the csrf token
                this.csrf(this.options.csrf);

                // setup functionality
                this._setup();
                this._events();
                this._setFilter();
                this._setTooltips();

                // make sure ajax post requests are working
                this._setAjaxPost('.js-cms-tree-item-menu a');
                this._setAjaxPost('.js-cms-tree-lang-trigger');
            },

            /**
             * Stores all jQuery references within `this.ui`.
             *
             * @method _setupUI
             * @private
             */
            _setupUI: function _setupUI() {
                var pagetree = $('.cms-pagetree-container');
                this.ui = {
                    container: pagetree,
                    document: $(document),
                    tree: pagetree.find('.js-cms-pagetree')
                };
            },

            /**
             * Setting up the jstree and the related columns.
             *
             * @method _setup
             * @private
             */
            _setup: function _setup() {
                var that = this;
                var columns = [];

                // setup column headings
                $.each(this.options.columns, function (index, obj) {
                    if (obj.key === '') {
                        // the first row is already populated, to avoid overwrites
                        // just leave the "key" param empty
                        columns.push({
                            header: obj.title
                        });
                    } else {
                        columns.push({
                            header: obj.title,
                            value: function (node) {
                                // it needs to have the "colde" format and not "col-de"
                                // as jstree will convert "col-de" to "colDe"
                                return node.data['col' + obj.key];
                            }
                        });
                    }
                });

                // bind options to the jstree instance
                this.ui.tree.jstree({
                    core: {
                        // disable open/close animations
                        animation: 0,
                        // core setting to allow actions
                        check_callback: true,
                        // https://www.jstree.com/api/#/?f=$.jstree.defaults.core.data
                        data: {
                            url: 'get-tree/',
                            data: {
                                //pageId: 90,
                                language: 'en'
                            }
                        },
                        // strings used within jstree that are called using `get_string`
                        strings: {
                            'Loading ...': 'Loading ...',
                            'New node': 'New node',
                            'nodes': 'nodes'
                        },
                        error: function (error) {
                            that.showError(error.reason);
                        }
                        // TODO need to add theme capabilities
                    },
                    // activate drag and drop plugin
                    plugins : ['dnd', 'search', 'grid', 'options'],
                    // https://github.com/deitch/jstree-grid
                    grid: {
                        // columns are provided from base.html options
                        columns: columns,
                        resizable: true
                    }
                });
            },

            _events: function () {
                var that = this;

                this.ui.container.on('click', '.cms-tree-item-move', function (e) {
                    that._getNode($(e.target));
                });

                this.ui.document.on('dnd_stop.vakata', function () {
                    console.log('stop drag&drop');
                });

                this.ui.container.on('changed.jstree', function () {
                    console.log('trigger open');
                });
            },

            _getNode: function (element) {
                var tree = this.ui.container.jstree();
                var el = element.closest('li');
                var obj = tree.get_node(el);

                // TODO move capabilities
                console.log(obj);

                // mock node
                tree.move_node(obj, tree.get_node(el.prev()), 'last');
            },

            _setFilter: function () {
                // TODO implement search filtering
            },

            /**
             * Sets up general tooltips that can have a list of links or content.
             *
             * @method _setTooltips
             * @private
             */
            _setTooltips: function _setTooltips() {
                var that = this;
                var triggerCls = '.js-cms-tree-tooltip-trigger';
                var containerCls = '.js-cms-tree-tooltip-container';
                var triggers;
                var containers;

                // attach event to the trigger
                this.ui.container.on(this.click, triggerCls, function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();

                    triggers = $(triggerCls);
                    containers = $(containerCls);

                    containers.removeClass('cms-tree-tooltip-container-open')
                        .eq(triggers.index(this))
                        .addClass('cms-tree-tooltip-container-open');

                    that.ui.document.on(that.click, function () {
                        containers.removeClass('cms-tree-tooltip-container-open');
                        that.ui.document.off(that.click);
                    });
                });

                // stop propagnation on the element
                this.ui.container.on(this.click, containerCls, function (e) {
                    e.stopImmediatePropagation();
                });
            },

            /**
             * Triggers the links `href` as ajax post request.
             *
             * @method _setAjaxPost
             * @private
             * @param {jQuery} trigger jQuery link target
             */
            _setAjaxPost: function _setAjaxPost(trigger) {
                var that = this;

                this.ui.container.on(this.click, trigger, function (e) {
                    e.preventDefault();
                    $.post($(this).attr('href')).done(function () {
                        window.location.reload();
                    }).error(function (error) {
                        that.showError(error.statusText);
                    });
                });
            },

            /**
             * Displays an error within the django UI.
             *
             * @method showError
             * @param {String} message string message to display
             */
            showError: function showError(message) {
                var messages = $('.messagelist');
                var breadcrumb = $('.breadcrumbs');
                var tpl = '<ul class="messagelist"><li class="error">{msg}</li></ul>';
                var msg = tpl.replace('{msg}', message);

                if (messages.length) {
                    messages.replaceWith(msg);
                } else {
                    breadcrumb.after(msg);
                }
            }

        });

        // autoload the pagetree
        new CMS.PageTree();

    });

})(CMS.$);

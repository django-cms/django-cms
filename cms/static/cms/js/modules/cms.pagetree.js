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

        /**
         * JSTree plugin used to synchronise the column width depending on the
         * screen size. Hides rows from right to left and displays an additional
         * menu row.
         */
        $.jstree.plugins.gridResize = function (options, parent) {
            var that = this;

            this.ui = {
                window: $(window)
            };
            this.timeout = 100;

            // this is how we register event handlers on jstree plugins
            this.bind = function () {
                parent.bind.call(this);
                // load `synchronise` on first load
                this.element.on('ready.jstree', function () {
                    that.ui.cols = $('.jstree-grid-column');
                    that.ui.container = $('.jstree-grid-wrapper');
                    that.ui.inner = $('.jstree-grid-midwrapper');
                    that.breakpoints = [];
                    that.processed = [];
                    // trigger first `synchronise`
                    that.ui.window.trigger('resize.jstree');
                });
                // TODO attach events on drag&drop or open&close
            };

            function synchronise() {
                var containerWidth = that.ui.container.outerWidth(true);
                var wrapperWidth = that.ui.inner.outerWidth(true);
                // we do not now the smallest size possible at this stage,
                // the "pages" section is automatically adapted to 100% to fill
                // the screen. In order to get the correct breakpoints, we need
                // to make a snapshot at the lowest point
                if (!that.breakpoints.length && (containerWidth < wrapperWidth)) {
                    that.breakpoints = createSnapshot();
                }
                // these vars are available after breakpoints is triggered
                var breakpointSum = that.breakpoints.reduce(function(pv, cv) { return pv + cv; }, 0);
                var colsFiltered = that.ui.cols.filter(':visible');
                var index = colsFiltered.length - 1;

                // hide or show elements according to their sum

                console.clear();
                console.log(that.breakpoints);

                console.log(that.breakpoints[index] || 0);
                console.log(breakpointSum, containerWidth);

                if (containerWidth < breakpointSum) {
                    that.processed.push(that.breakpoints.pop());
                }

                console.log(that.processed);

                /*
                if (wrapper.outerWidth(true) < colsWidth) {
                    cols.eq(colsIndex).addClass('hidden');
                } else if (false) {
                    //cols.removeClass('hidden');
                    //colsArray.pop();
                }
                */
            }

            function createSnapshot() {
                var array = [];
                // we need to get the real size of all visible columns added
                that.ui.cols.each(function () {
                    array.push($(this).outerWidth(true));
                });
                return array;
            }

            // bind resize event
            this.ui.window.on('resize.jstree',
                CMS.API.Helpers.throttle(synchronise, this.timeout));
        };

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

        /**
         * The pagetree is loaded via `/admin/cms/page` and has a custom admin
         * templates stored within `templates/admin/cms/page/tree`.
         *
         * @class PageTree
         * @namespace CMS
         * @uses CMS.API.Helpers
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
                            header: obj.title,
                            width: obj.width || '1%'
                        });
                    } else {
                        columns.push({
                            header: obj.title,
                            value: function (node) {
                                // it needs to have the "colde" format and not "col-de"
                                // as jstree will convert "col-de" to "colDe"
                                return node.data['col' + obj.key];
                            },
                            width: obj.width || '1%'
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
                    plugins : ['dnd', 'search', 'grid', 'gridResize'],
                    // https://github.com/deitch/jstree-grid
                    grid: {
                        // columns are provided from base.html options
                        width: '100%',
                        columns: columns
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

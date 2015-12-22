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
         * screen size. Hides rows from right to left.
         */
        $.jstree.plugins.gridResize = function (options, parent) {
            var that = this;
            // this is how we register event handlers on jstree plugins
            this.bind = function () {
                parent.bind.call(this);
                // store elements after jstree is loaded and trigger initial states
                this.element.on('ready.jstree', function () {
                    that.ui = {
                        window: $(window),
                        cols: $('.jstree-grid-column'),
                        container: $('.jstree-grid-wrapper'),
                        inner: $('.jstree-grid-midwrapper')
                    };
                    that.timeout = 100;
                    that.snapshot = [];

                    // bind resize event and trigger
                    that.ui.window.on('resize.jstree',
                        CMS.API.Helpers.throttle(synchronise, that.timeout))
                        .trigger('resize.jstree');
                });
                // reload snapshot when nodes are updated
                this.element.on('redraw.jstree after_open.jstree after_close.jstree dnd_stop.vakata', function () {
                    that.snapshot = [];
                });
            };

            function synchronise() {
                var containerWidth = that.ui.container.outerWidth(true);
                var wrapperWidth = that.ui.inner.outerWidth(true);
                // we do not now the smallest size possible at this stage,
                // the "pages" section is automatically adapted to 100% to fill
                // the screen. In order to get the correct breakpoints, we need
                // to make a snapshot at the lowest point
                if (!that.snapshot.length && (containerWidth < wrapperWidth)) {
                    // store the current breakpoints
                    that.snapshot = createSnapshot();
                }
                // only recalculate once the snapshot is available to save memory
                if (that.snapshot.length) {
                    var index = that.snapshot.length;
                    // loops from most the most right to the most left column
                    // without incorporating the very first column
                    for (var i = 1; i < that.snapshot.length; i++) {
                        var calc = 0;
                        var condition1;
                        var condition2;
                        var idx = that.snapshot.length - i;

                        for (var x = 1; x < i; x++) {
                            calc = calc + that.snapshot.array[that.snapshot.length - x] || 0;
                        }

                        condition1 = containerWidth < (that.snapshot.width - calc);
                        condition2 = index <= (idx + 1);

                        if (condition1 && condition2) {
                            that.ui.cols.eq(idx).addClass('cms-hidden');
                            index = idx;
                        } else {
                            that.ui.cols.eq(idx).removeClass('cms-hidden');
                        }
                    }
                }
            }

            function createSnapshot() {
                var array = [];
                // we need to get the real size of all visible columns added
                that.ui.cols.each(function () {
                    array.push($(this).outerWidth(true));
                });
                return {
                    array: array,
                    length: array.length,
                    width: array.reduce(function (pv, cv) {
                        return pv + cv;
                    }, 0)
                };
            }
        };

        // TODO implement success feedback when moving a tree item (that.options.lang.success)

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

                // states and events
                this.click = 'click.cms.pagetree';
                this.cache = undefined;
                this.cacheType = '';

                // elements
                this._setupUI();
                this._setup();
                this._events();
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
                    tree: pagetree.find('.js-cms-pagetree'),
                    dialog: $('.js-cms-tree-dialog')
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
                var obj = {
                    language: this.options.lang.code,
                    openNodes: []
                };

                // make sure that ajax request send the csrf token
                this.csrf(this.options.csrf);

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
                            url: this.options.urls.tree,
                            data: function (node) {
                                // '#' is rendered if its the root node, there we only
                                // care about `obj.openNodes`, in the following case
                                // we are requesting a specific node
                                if (node.id !== '#') {
                                    obj.pageId = that._setNode(node.data.id);
                                }

                                // we need to store the opened items inside the localstorage
                                // as we have to load the pagetree with the previous opened
                                // state
                                obj.openNodes = that._getNodes();

                                return obj;
                            }
                        },
                        // strings used within jstree that are called using `get_string`
                        strings: {
                            'Loading ...': this.options.lang.loading,
                            'New node': this.options.lang.newNode,
                            'nodes': this.options.lang.nodes
                        },
                        error: function (error) {
                            that.showError(error.reason);
                        },
                        themes: {
                            name: 'default'
                        }
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

            /**
             * Sets up all the event handlers, such as opening and moving.
             *
             * @method _events
             * @private
             */
            _events: function _events() {
                var that = this;

                // set events for the nodeId updates
                this.ui.tree.on('after_close.jstree', function (e, el) {
                    that._removeNode(el.node.data.id);
                });
                this.ui.tree.on('after_open.jstree', function (e, el) {
                    that._setNode(el.node.data.id);
                });

                // drag and dropping items and saving their states
                $(document).on('dnd_stop.vakata', function (e, el) {
                    that._moveNode(that._getNodeData(el.element));
                });

                // set event for cut and paste
                this.ui.container.on(this.click, '.js-cms-tree-item-cut, .js-cms-tree-item-copy', function () {
                    that.cache = that._getNodeData(that._getNodeId($(this)));
                    if ($(this).hasClass('js-cms-tree-item-cut')) {
                        that.cacheType = 'cut';
                    } else {
                        that.cacheType = 'copy';
                    }
                    that._toggleHelpers();
                });

                // attach events to paste
                this.ui.container.on(this.click, '.cms-tree-item-helpers a', function () {
                    var target = that._getNodeData(that._getNodeId($(this)));
                    var obj = {
                        target: target.id,
                        position: 'last-child',
                        id: that.cache.id
                    };

                    that._toggleHelpers();

                    if (that.cacheType === 'cut') {
                        that._moveNode(obj);
                    }
                    if (that.cacheType === 'copy') {
                        that._copyNode(obj);
                    }
                });

                // additional event handlers
                this._setFilter();
                this._setTooltips();

                // make sure ajax post requests are working
                this._setAjaxPost('.js-cms-tree-item-menu a');
                this._setAjaxPost('.js-cms-tree-lang-trigger');
            },

            /**
             * Retreives a list of nodes from local storage.
             *
             * @method _getNodes
             * @private
             * @return {Array} list of ids
             */
            _getNodes: function _getNodes() {
                var storage = localStorage.getItem('cms_test_storage');

                return (storage) ? storage.split(',') : [];
            },

            /**
             * Stores a node in local storage.
             *
             * @method _setNode
             * @private
             * @param {String} id to be stored
             * @return {String} id that has been stored
             */
            _setNode: function _setNode(id) {
                var number = id.toString();
                var storage = this._getNodes();
                // store value only if it isn't there yet
                if (storage.indexOf(number) === -1) {
                    storage.push(number);
                }

                localStorage.setItem('cms_test_storage', storage);

                return number;
            },

            /**
             * Removes a node in local storage.
             *
             * @method _setNode
             * @private
             * @param {String} id to be stored
             * @return {String} id that has been removed
             */
            _removeNode: function _removeNode(id) {
                var number = id.toString();
                var storage = this._getNodes();
                var index = storage.indexOf(number);

                // remove given id from storage
                if (index !== -1) {
                    storage.splice(index, 1);
                }

                localStorage.setItem('cms_test_storage', storage);

                return number;
            },

            /**
             * Moves a node after drag & drop.
             *
             * @method _moveNode
             * @param {Object} [opts]
             * @param {Number} [opts.id] current element id for url matching
             * @param {Number} [opts.target] target sibling or parent
             * @param {Number} [opts.position] either `left`, `right` or `last-child`
             * @private
             */
            _moveNode: function _moveNode(obj) {
                var that = this;
                obj.site = that.options.site;

                $.ajax({
                    method: 'post',
                    url: that.options.urls.move.replace('{id}', obj.id),
                    data: obj
                }).done(function () {
                    if (that.cache) {
                        that.ui.tree.jstree('move_node',
                            that.ui.tree.find('li[data-id="' + obj.id + '"]'),
                            that.ui.tree.find('li[data-id="' + obj.target + '"]'));
                    }
                    that.cache = undefined;
                }).error(function (error) {
                    that.showError(error.statusText);
                });
            },

            /**
             * Copies a node into the selected node.
             *
             * @method _copyNode
             * @param {Object} [opts]
             * @param {Number} [opts.id] current element id for url matching
             * @param {Number} [opts.target] target sibling or parent
             * @param {Number} [opts.position] either `left`, `right` or `last-child`
             * @private
             */
            _copyNode: function _copyNode(obj) {
                var that = this;
                obj.site = that.options.site;

                $.ajax({
                    method: 'post',
                    url: that.options.urls.copyPermission.replace('{id}', obj.id),
                    data: obj
                // the dialog is loaded via the ajax respons originating from
                // `templates/admin/cms/page/tree/copy_premissions.html`
                }).done(function (data) {
                    that.ui.dialog.append(data);
                }).error(function (error) {
                    that.showError(error.statusText);
                });

                // attach events to the permission dialog
                this.ui.dialog.off(this.click, '.cancel').on(this.click, '.cancel', function (e) {
                    e.preventDefault();
                    $('.js-cms-dialog').remove();
                }).off(this.click, '.submit').on(this.click, '.submit', function (e) {
                    e.preventDefault();
                    var data = $(this).closest('form').serialize().split('&');
                    // loop through form data and attach to obj
                    for (var i = 0; i < data.length; i++) {
                        obj[data[i].split('=')[0]] = data[i].split('=')[1];
                    }
                    // send the real ajax request for copying the plugin
                    $.ajax({
                        method: 'post',
                        url: that.options.urls.copy.replace('{id}', obj.id),
                        data: obj
                    }).done(function () {
                        that.reloadBrowser();
                    }).error(function (error) {
                        that.showError(error.statusText);
                    });
                });
            },

            /**
             * Returns element from any sub nodes.
             *
             * @method _getElement
             * @private
             * @param {jQuery} el jQuery node form where to search
             * @return {String} jsTree node element id
             */
            _getNodeId: function _getElement(el) {
                return el.closest('.jstree-grid-cell')
                    .attr('class')
                    .split(' ')[0]
                    .replace('jsgrid_', '')
                    .replace('_col', '');
            },

            /**
             * Sets up all the event handlers, such as opening and moving.
             *
             * @method _getNodeData
             * @private
             * @param {jQuery} el node to be evaluated
             * @return {Object} evaluated object with params
             */
            _getNodeData: function _getNodeData(el) {
                var obj = {};
                var element = this.ui.tree.jstree('get_node', el);
                var parent = this.ui.tree.jstree('get_parent', element);
                var nextDom = this.ui.tree.jstree('get_next_dom', element, true);
                var prevDom = this.ui.tree.jstree('get_prev_dom', element, true);
                var parentDom = this.ui.tree.jstree('get_node', parent);

                // last-child if there is only one element (nested)
                // left if it can be placed before the get_next_dom (current sibling level)
                // right if it can be placed after the get_prev_dom (current sibling level)
                if (nextDom) {
                    obj.position = 'left';
                    obj.target = nextDom.data().id;
                } else if (prevDom) {
                    obj.position = 'right';
                    obj.target = prevDom.data().id;
                } else {
                    obj.position = 'last-child';
                    obj.target = parentDom.data.id;
                }
                obj.id = element.data.id;

                return obj;
            },

            /**
             * Handles filter button display (Filter: Off).
             *
             * @method _setFilter
             * @private
             */
            _setFilter: function _setFilter() {
                var that = this;
                var trigger = $('.js-cms-tree-filter-trigger');
                var container = $('.js-cms-tree-filter-container');

                trigger.on(this.click, function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();

                    container.toggleClass('hidden');

                    that.ui.document.one(that.click, function () {
                        container.addClass('hidden');
                    });
                });

                container.on(that.click, function (e) {
                    e.stopImmediatePropagation();
                });
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

                    that.ui.document.one(that.click, function () {
                        containers.removeClass('cms-tree-tooltip-container-open');
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
             * Shows and hides paste helpers.
             *
             * @method _toggleHelpers
             * @private
             */
            _toggleHelpers: function _toggleHelpers() {
                $('.cms-tree-item-helpers').toggleClass('cms-hidden');
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
                var msg = tpl.replace('{msg}', this.options.lang.error + ' – ' + message);

                messages.length ? messages.replaceWith(msg) : breadcrumb.after(msg);
            }

        });

        // autoload the pagetree
        new CMS.PageTree();

    });

})(CMS.$);

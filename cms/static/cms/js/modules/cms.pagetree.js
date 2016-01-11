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

    /**
     * The pagetree is loaded via `/admin/cms/page` and has a custom admin
     * templates stored within `templates/admin/cms/page/tree`.
     *
     * @class PageTree
     * @namespace CMS
     * @uses CMS.API.Helpers
     */
    CMS.PageTree = new CMS.Class({
        // TODO add mechanics to set the home page
        initialize: function initialize(options) {
            // options are loaded from the pagetree html node
            this.options = $('.js-cms-pagetree').data('json');
            this.options = $.extend(true, {}, this.options, options);

            // states and events
            this.click = 'click.cms.pagetree';
            this.cacheTarget = null;
            this.cacheType = '';
            this.cacheId = null;
            this.successTimer = 1000;

            // elements
            this._setupUI();
            this._events();

            // cancel if pagtree is not available
            if (!$.isEmptyObject(this.options)) {
                this._setup();
            }
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
            var data = false;

            // make sure that ajax request send the csrf token
            CMS.API.Helpers.csrf(this.options.csrf);

            // setup column headings
            $.each(this.options.columns, function (index, obj) {
                if (obj.key === '') {
                    // the first row is already populated, to avoid overwrites
                    // just leave the "key" param empty
                    columns.push({
                        header: obj.title,
                        width: obj.width || '1%',
                        wideCellClass: obj.cls
                    });
                } else {
                    columns.push({
                        header: obj.title,
                        value: function (node) {
                            // it needs to have the "colde" format and not "col-de"
                            // as jstree will convert "col-de" to "colDe"
                            if (node.data) {
                                return node.data['col' + obj.key];
                            } else {
                                return '';
                            }
                        },
                        width: obj.width || '1%',
                        wideCellClass: obj.cls
                    });
                }
            });

            // prepare data
            if (!this.options.filtered) {
                data = {
                    url: this.options.urls.tree,
                    data: function (node) {
                        // '#' is rendered if its the root node, there we only
                        // care about `obj.openNodes`, in the following case
                        // we are requesting a specific node
                        if (node.id !== '#') {
                            obj.pageId = that._storeNodeId(node.data.id);
                        }

                        // we need to store the opened items inside the localstorage
                        // as we have to load the pagetree with the previous opened
                        // state
                        obj.openNodes = that._getStoredNodeIds();

                        // we need to set the site id to get the correct tree
                        obj.site = that.options.site;

                        return obj;
                    }
                };
            }

            // bind options to the jstree instance
            this.ui.tree.jstree({
                core: {
                    // disable open/close animations
                    animation: 0,
                    // core setting to allow actions
                    check_callback: function () {
                        // cancel dragging when filtering is active by setting `false`
                        return (that.options.filtered) ? false : true;
                    },
                    // https://www.jstree.com/api/#/?f=$.jstree.defaults.core.data
                    data: data,
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
                        name: 'django-cms'
                    },
                    // disable the multi selection of nodes for now
                    multiple: false
                },
                // activate drag and drop plugin
                plugins : ['dnd', 'search', 'grid', 'gridResize'],
                // https://www.jstree.com/api/#/?f=$.jstree.defaults.dnd
                dnd: {
                    inside_pos: 'last',
                    // disable the multi selection of nodes for now
                    drag_selection: false,
                    // disable CMD/CTRL copy
                    copy: false
                },
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
                that._removeNodeId(el.node.data.id);
            });
            this.ui.tree.on('after_open.jstree', function (e, el) {
                that._storeNodeId(el.node.data.id);
                that._checkHelpers();
            });

            // store moved position node
            this.ui.tree.on('move_node.jstree copy_node.jstree', function (e, obj) {
                if (!that.cacheType || that.cacheType === 'cut') {
                    that._moveNode(that._getNodePosition(obj));
                } else {
                    that._copyNode(obj);
                }
                // we need to open the parent node if we trigger an element
                // if not already opened
                that.ui.tree.jstree('open_node', obj.parent);
            });

            // set event for cut and paste
            this.ui.container.on(this.click, '.js-cms-tree-item-cut', function (e) {
                e.preventDefault();
                that._cutOrCopy({ type: 'cut', element: $(this) });
            });

            // set event for cut and paste
            this.ui.container.on(this.click, '.js-cms-tree-item-copy', function (e) {
                e.preventDefault();
                that._cutOrCopy({ type: 'copy', element: $(this) });
            });

            // attach events to paste
            this.ui.container.on(this.click, '.cms-tree-item-helpers a', function (e) {
                e.preventDefault();
                that._paste(e);
            });

            // additional event handlers
            this._setFilter();
            this._setTooltips();

            // make sure ajax post requests are working
            this._setAjaxPost('.js-cms-tree-item-menu a');
            this._setAjaxPost('.js-cms-tree-lang-trigger');
        },

        /**
         * Helper to process the cut and copy events.
         *
         * @method _cutOrCopy
         * @param {Object} [opts]
         * @param {Number} [opts.type] either 'cut' or 'copy'
         * @param {Number} [opts.element] originated trigger element
         * @private
         */
        _cutOrCopy: function _cutOrCopy(obj) {
            var jsTreeId = this._getNodeId(obj.element.closest('.jstree-grid-cell'));
            // resets if we click again
            if (this.cacheType === obj.type && jsTreeId === this.cacheId) {
                this.cacheType = null;
                this._hideHelpers();
            } else {
                // we need to cache the node and type so `_showHelpers`
                // will trigger the correct behaviour
                this.cacheTarget = obj.element;
                this.cacheType = obj.type;
                this.cacheId = jsTreeId;
                this._showHelpers();
                this._checkHelpers();
            }
        },

        /**
         * RHelper to process the paste event.
         *
         * @method _paste
         * @private
         * @return {Object} event originated event handler
         */
        _paste: function _paste(event) {
            // hide helpers after we picked one
            this._hideHelpers();

            var copyFromId = this._getNodeId(this.cacheTarget);
            var copyToId = this._getNodeId($(event.currentTarget));

            // copyToId contains `jstree-1`, assign to root
            if (copyToId.indexOf('jstree-1') > -1) {
                copyToId = '#';
            }

            // TODO it is currently not possible to copy/cut a node to the root
            if (this.cacheType === 'cut') {
                this.ui.tree.jstree('cut', copyFromId);
            } else {
                this.ui.tree.jstree('copy', copyFromId);
            }

            this.ui.tree.jstree('paste', copyToId, 'last');
        },

        /**
         * Retreives a list of nodes from local storage.
         *
         * @method _getStoredNodeIds
         * @private
         * @return {Array} list of ids
         */
        _getStoredNodeIds: function _getStoredNodeIds() {
            return CMS.settings.pagetree || [];
        },

        /**
         * Stores a node in local storage.
         *
         * @method _storeNodeId
         * @private
         * @param {String} id to be stored
         * @return {String} id that has been stored
         */
        _storeNodeId: function _storeNodeId(id) {
            var number = id;
            var storage = this._getStoredNodeIds();

            // store value only if it isn't there yet
            if (storage.indexOf(number) === -1) {
                storage.push(number);
            }

            CMS.settings.pagetree = storage;
            CMS.API.Helpers.setSettings(CMS.settings);

            return number;
        },

        /**
         * Removes a node in local storage.
         *
         * @method _removeNodeId
         * @private
         * @param {String} id to be stored
         * @return {String} id that has been removed
         */
        _removeNodeId: function _removeNodeId(id) {
            var number = id;
            var storage = this._getStoredNodeIds();
            var index = storage.indexOf(number);

            // remove given id from storage
            if (index !== -1) {
                storage.splice(index, 1);
            }

            CMS.settings.pagetree = storage;
            CMS.API.Helpers.setSettings(CMS.settings);

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
                that._showSuccess(obj.id);
            }).fail(function (error) {
                that.showError(error.statusText);
            });
        },

        /**
         * Copies a node into the selected node.
         *
         * @method _copyNode
         * @param {String} copyFromId element to be cut
         * @param {String} copyToId destination to inject
         * @private
         */
        _copyNode: function _copyNode(obj) {
            var that = this;
            var node = that._getNodePosition(obj);
            var data = {
                site: this.options.site,
                // we need to refer to the original item here, as the copied
                // node will have no data attributes stored at it (not a clone)
                id: obj.original.data.id,
                position: node.position
            };

            // if there is no target provided, the node lands in root
            if (node.target) {
                data.target = node.target;
            }

            // we need to load a dialog first, to check if permissions should
            // be copied or not
            $.ajax({
                method: 'post',
                url: that.options.urls.copyPermission.replace('{id}', data.id),
                data: data
            // the dialog is loaded via the ajax respons originating from
            // `templates/admin/cms/page/tree/copy_premissions.html`
            }).done(function (dialog) {
                that.ui.dialog.append(dialog);
            }).fail(function (error) {
                that.showError(error.statusText);
            });

            // attach events to the permission dialog
            this.ui.dialog.off(this.click, '.cancel').on(this.click, '.cancel', function (e) {
                e.preventDefault();
                // remove just copied node
                that.ui.tree.jstree('delete_node', obj.node.id);
                $('.js-cms-dialog').remove();
                $('.js-cms-dialog-dimmer').remove();
            }).off(this.click, '.submit').on(this.click, '.submit', function (e) {
                e.preventDefault();
                var formData = $(this).closest('form').serialize().split('&');
                // loop through form data and attach to obj
                for (var i = 0; i < formData.length; i++) {
                    data[formData[i].split('=')[0]] = formData[i].split('=')[1];
                }
                // send the real ajax request for copying the plugin
                $.ajax({
                    method: 'post',
                    url: that.options.urls.copy.replace('{id}', data.id),
                    data: data
                }).done(function () {
                    CMS.API.Helpers.reloadBrowser();
                }).fail(function (error) {
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
         * @return {String|Boolean} jsTree node element id
         */
        _getNodeId: function _getElement(el) {
            var cls = el.closest('.jstree-grid-cell').attr('class');

            return (cls) ? cls.replace(/.*jsgrid_(.+?)_col.*/, '$1') : false;
        },

        /**
         * Gets the new node position after moving.
         *
         * @method _getNodePosition
         * @private
         * @param {Object} obj jstree move object
         * @return {Object} evaluated object with params
         */
        _getNodePosition: function _getNodePosition(obj) {
            var data = {};
            var node = this.ui.tree.jstree('get_node', obj.node.parent);

            data.position = obj.position;

            // jstree indicates no parent with `#`, in this case we do not
            // need to set the target attribute at all
            if (obj.parent !== '#') {
                data.target = node.data.id;
            }

            // some functions like copy create a new element with a new id,
            // in this case we need to set `data.id` manually
            if (obj.node && obj.node.data) {
                data.id = obj.node.data.id;
            }

            return data;
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

            // attach event for site filtering
            $('.js-cms-tree-search-site select').on('change', function () {
                $(this).closest('form').submit();
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
                $.ajax({
                    method: 'post',
                    url: $(this).attr('href')
                }).done(function () {
                    CMS.API.Helpers.reloadBrowser();
                }).fail(function (error) {
                    that.showError(error.statusText);
                });
            });
        },

        /**
         * Shows paste helpers.
         *
         * @method _showHelpers
         * @private
         */
        _showHelpers: function _showHelpers() {
            // helpers are generated on the fly, so we need to reference
            // them every single time
            $('.cms-tree-item-helpers').removeClass('cms-hidden');
        },

        /**
         * Hides paste helpers.
         *
         * @method _hideHelpers
         * @private
         */
        _hideHelpers: function _hideHelpers() {
            // helpers are generated on the fly, so we need to reference
            // them every single time
            $('.cms-tree-item-helpers').addClass('cms-hidden');
            this.cacheId = null;
        },

        /**
         * Checks the current state of the helpers after `after_open.jstree`
         * or `_cutOrCopy` is triggered.
         *
         * @method _checkHelpers
         * @private
         */
        _checkHelpers: function _checkHelpers() {
            if (this.cacheType) {
                this._showHelpers(this.cacheType);
            }

            // hide cut element if it is visible
            if (this.cacheType === 'cut' && this.cacheTarget) {
                $('.jsgrid_' +
                    this._getNodeId(this.cacheTarget.closest('.jstree-grid-cell')) +
                    '_col .cms-tree-item-helpers').addClass('cms-hidden');
            }
        },

        /**
         * Shows success message on node after successful action.
         *
         * @method _showSuccess
         * @param {Number} id id of the element to add the success class
         * @private
         */
        _showSuccess: function _showSuccess(id) {
            var element = this.ui.tree.find('li[data-id="' + id + '"]');
            element.addClass('cms-tree-node-success');
            setTimeout(function () {
                element.removeClass('cms-tree-node-success');
            }, this.successTimer);
            // hide elements
            this._hideHelpers();
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

    // shorthand for jQuery(document).ready();
    $(function () {
        // load cms settings beforehand
        CMS.config = {};
        CMS.settings = CMS.API.Helpers.getSettings();
        // autoload the pagetree
        new CMS.PageTree();
    });

})(CMS.$);

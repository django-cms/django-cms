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
            this.cache = {
                id: null,
                target: null,
                type: ''
            };
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
                            // as jstree will convert "col-de" to "colde"
                            // also we strip dashes, in case language code contains it
                            // e.g. zh-hans, zh-cn etc
                            if (node.data) {
                                return node.data['col' + obj.key.replace('-', '')];
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
                        } else {
                            obj.pageId = null;
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
                plugins : ['dnd', 'search', 'grid'],
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
                if (!that.cache.type || that.cache.type === 'cut') {
                    that._moveNode(that._getNodePosition(obj)).done(function () {
                        var instance = that.ui.tree.jstree(true);

                        instance._hide_grid(instance.get_node(obj.parent));
                        if (obj.parent === '#') {
                            instance.refresh();
                        } else {
                            // have to refresh parent, because refresh only
                            // refreshes children of the node, never the node itself
                            instance.refresh_node(obj.parent);
                        }
                    });
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

            // advanced settings link handling
            this.ui.container.on(this.click, '.js-cms-tree-advanced-settings', function (e) {
                if (e.shiftKey) {
                    e.preventDefault();
                    window.location.href = $(this).data('url');
                }
            });

            // add events for error reload (messagelist)
            this.ui.document.on(this.click, '.messagelist .cms-tree-reload', function (e) {
                e.preventDefault();
                that._reloadHelper();
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
            // prevent actions if you try to copy a page with an apphook
            if (obj.type === 'copy' && obj.element.data().apphook) {
                this.showError(this.options.lang.apphook);
                return false;
            }

            var jsTreeId = this._getNodeId(obj.element.closest('.jstree-grid-cell'));
            // resets if we click again
            if (this.cache.type === obj.type && jsTreeId === this.cache.id) {
                this.cache.type = null;
                this._hideHelpers();
            } else {
                // we need to cache the node and type so `_showHelpers`
                // will trigger the correct behaviour
                this.cache.target = obj.element;
                this.cache.type = obj.type;
                this.cache.id = jsTreeId;
                this._showHelpers();
                this._checkHelpers();
            }
        },

        /**
         * Helper to process the paste event.
         *
         * @method _paste
         * @private
         * @return {Object} event originated event handler
         */
        _paste: function _paste(event) {
            // hide helpers after we picked one
            this._hideHelpers();

            var copyFromId = this._getNodeId(this.cache.target);
            var copyToId = this._getNodeId($(event.currentTarget));

            // copyToId contains `jstree-1`, assign to root
            if (copyToId.indexOf('jstree-1') > -1) {
                copyToId = '#';
            }

            if (this.cache.type === 'cut') {
                this.ui.tree.jstree('cut', copyFromId);
            } else {
                this.ui.tree.jstree('copy', copyFromId);
            }

            this.ui.tree.jstree('paste', copyToId, 'last');
            this.cache.type = null;
            this.cache.target = null;
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
         * @returns {$.Deferred} ajax request object
         * @private
         */
        _moveNode: function _moveNode(obj) {
            var that = this;
            obj.site = that.options.site;

            return $.ajax({
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

            if (that.options.permission) {
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

                    that._saveCopiedNode(data);
                });
            } else {
                this._saveCopiedNode(data);
            }
        },

        /**
         * Sends the request to copy a node.
         *
         * @method _saveCopiedNode
         * @private
         * @param {Object} data node position information
         */
        _saveCopiedNode: function _saveCopiedNode(data) {
            var that = this;
            // send the real ajax request for copying the plugin
            return $.ajax({
                method: 'post',
                url: that.options.urls.copy.replace('{id}', data.id),
                data: data
            }).done(function () {
                that._reloadHelper();
            }).fail(function (error) {
                that.showError(error.statusText);
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
            var index;

            // attach event to the trigger
            this.ui.container.on(this.click, triggerCls, function (e) {
                e.preventDefault();
                e.stopImmediatePropagation();

                triggers = $(triggerCls);
                containers = $(containerCls);
                index = triggers.index(this);

                // cancel if opened tooltip is triggered again
                if (containers.eq(index).is(':visible')) {
                    containers.removeClass('cms-tree-tooltip-container-open');
                    return false;
                }

                // otherwise show the dropdown
                containers
                    .removeClass('cms-tree-tooltip-container-open')
                    .eq(index)
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
                    if (window.self !== window.top) {
                        // if we're in the sideframe we have to actually
                        // check if we are publishing a page we're currently in
                        // because if the slug did change we would need to
                        // redirect to that new slug
                        // Problem here is that in case of the apphooked page
                        // the model and pk are empty and reloadBrowser doesn't really
                        // do anything - so here we specifically force the data
                        // to be the data about the page and not the model
                        var parent = (window.parent ? window.parent : window);
                        var data = {
                            // FIXME shouldn't be hardcoded
                            model: 'cms.page',
                            pk: parent.CMS.config.request.page_id
                        };
                        CMS.API.Helpers.reloadBrowser(false, false, true, data);
                    } else {
                        // otherwise simply reload the page
                        that._reloadHelper();
                    }
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
            this.cache.id = null;
        },

        /**
         * Checks the current state of the helpers after `after_open.jstree`
         * or `_cutOrCopy` is triggered.
         *
         * @method _checkHelpers
         * @private
         */
        _checkHelpers: function _checkHelpers() {
            if (this.cache.type) {
                this._showHelpers(this.cache.type);
            }

            // hide cut element if it is visible
            if (this.cache.type === 'cut' && this.cache.target) {
                $('.jsgrid_' + this.cache.id + '_col .cms-tree-item-helpers')
                    .addClass('cms-hidden');
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
         * Checks if we should reload the iframe or entire window. For this we
         * need to skip `CMS.API.Helpers.reloadBrowser();`.
         *
         * @method _reloadHelper
         * @private
         */
        _reloadHelper: function _reloadHelper() {
            if (window.self !== window.top) {
                window.location.reload();
            } else {
                CMS.API.Helpers.reloadBrowser();
            }
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
            var reload = this.options.lang.reload;
            var tpl = '' +
                '<ul class="messagelist">' +
                '   <li class="error">' +
                '       {msg} ' +
                '       <a href="#reload" class="cms-tree-reload"> ' + reload + ' </a>' +
                '   </li>' +
                '</ul>';
            var msg = tpl.replace('{msg}', '<strong>' + this.options.lang.error + '</strong> ' + message);

            messages.length ? messages.replaceWith(msg) : breadcrumb.after(msg);
        }

    });

    // shorthand for jQuery(document).ready();
    $(function () {
        // load cms settings beforehand
        // have to set toolbar to "expanded" by default
        // otherwise initialization will be incorrect when you
        // go first to pages and then to normal page
        CMS.config = {
            settings: {
                toolbar: 'expanded'
            },
            urls: {
                settings: $('.js-cms-pagetree').data('settings-url')
            }
        };
        CMS.settings = CMS.API.Helpers.getSettings();
        // autoload the pagetree
        new CMS.PageTree();
    });

})(CMS.$);

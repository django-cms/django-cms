/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';

import Class from 'classjs';
import { Helpers, KEYS } from './cms.base';
import PageTreeDropdowns from './cms.pagetree.dropdown';
import PageTreeStickyHeader from './cms.pagetree.stickyheader';
import { debounce, without } from 'lodash';

import 'jstree';
import '../libs/jstree/jstree.grid.min';

/**
 * The pagetree is loaded via `/admin/cms/page` and has a custom admin
 * templates stored within `templates/admin/cms/page/tree`.
 *
 * @class PageTree
 * @namespace CMS
 */
var PageTree = new Class({
    options: {
        pasteSelector: '.js-cms-tree-item-paste'
    },
    initialize: function initialize(options) {
        // options are loaded from the pagetree html node
        var opts = $('.js-cms-pagetree').data('json');

        this.options = $.extend(true, {}, this.options, opts, options);

        // states and events
        this.click = 'click.cms.pagetree';
        this.clipboard = {
            id: null,
            origin: null,
            type: ''
        };
        this.successTimer = 1000;

        // elements
        this._setupUI();
        this._events();

        Helpers.csrf(this.options.csrf);

        // cancel if pagetree is not available
        if ($.isEmptyObject(opts) || opts.empty) {
            this._getClipboard();
            // attach events to paste
            var that = this;

            this.ui.container.on(this.click, this.options.pasteSelector, function(e) {
                e.preventDefault();
                if ($(this).hasClass('cms-pagetree-dropdown-item-disabled')) {
                    return;
                }
                that._paste(e);
            });
        } else {
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
        var pagetree = $('.cms-pagetree');

        this.ui = {
            container: pagetree,
            document: $(document),
            tree: pagetree.find('.js-cms-pagetree'),
            dialog: $('.js-cms-tree-dialog'),
            siteForm: $('.js-cms-pagetree-site-form')
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

        // setup column headings
        // eslint-disable-next-line no-shadow
        $.each(this.options.columns, function(index, obj) {
            if (obj.key === '') {
                // the first row is already populated, to avoid overwrites
                // just leave the "key" param empty
                columns.push({
                    wideValueClass: obj.wideValueClass,
                    wideValueClassPrefix: obj.wideValueClassPrefix,
                    header: obj.title,
                    width: obj.width || '1%',
                    wideCellClass: obj.cls
                });
            } else {
                columns.push({
                    wideValueClass: obj.wideValueClass,
                    wideValueClassPrefix: obj.wideValueClassPrefix,
                    header: obj.title,
                    value: function(node) {
                        // it needs to have the "colde" format and not "col-de"
                        // as jstree will convert "col-de" to "colde"
                        // also we strip dashes, in case language code contains it
                        // e.g. zh-hans, zh-cn etc
                        if (node.data) {
                            return node.data['col' + obj.key.replace('-', '')];
                        }

                        return '';
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
                cache: false,
                data: function(node) {
                    // '#' is rendered if its the root node, there we only
                    // care about `obj.openNodes`, in the following case
                    // we are requesting a specific node
                    if (node.id === '#') {
                        obj.nodeId = null;
                    } else {
                        obj.nodeId = that._storeNodeId(node.data.nodeId);
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
                // eslint-disable-next-line max-params
                check_callback: function(operation, node, node_parent, node_position, more) {
                    if ((operation === 'move_node' || operation === 'copy_node') && more && more.pos) {
                        if (more.pos === 'i') {
                            $('#jstree-marker').addClass('jstree-marker-child');
                        } else {
                            $('#jstree-marker').removeClass('jstree-marker-child');
                        }
                    }

                    return that._hasPermission(node_parent, 'add');
                },
                // https://www.jstree.com/api/#/?f=$.jstree.defaults.core.data
                data: data,
                // strings used within jstree that are called using `get_string`
                strings: {
                    'Loading ...': this.options.lang.loading,
                    'New node': this.options.lang.newNode,
                    nodes: this.options.lang.nodes
                },
                error: function(error) {
                    // ignore warnings about dragging parent into child
                    var errorData = JSON.parse(error.data);

                    if (error.error === 'check' && errorData && errorData.chk === 'move_node') {
                        return;
                    }
                    that.showError(error.reason);
                },
                themes: {
                    name: 'django-cms'
                },
                // disable the multi selection of nodes for now
                multiple: false
            },
            // activate drag and drop plugin
            plugins: ['dnd', 'search', 'grid'],
            // https://www.jstree.com/api/#/?f=$.jstree.defaults.dnd
            dnd: {
                inside_pos: 'last',
                // disable the multi selection of nodes for now
                drag_selection: false,
                // disable dragging if filtered
                is_draggable: function(nodes) {
                    return that._hasPermission(nodes[0], 'move') && !that.options.filtered;
                },
                large_drop_target: true,
                copy: true,
                touch: 'selected'
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
        this.ui.tree.on('after_close.jstree', function(e, el) {
            that._removeNodeId(el.node.data.nodeId);
        });

        this.ui.tree.on('after_open.jstree', function(e, el) {
            that._storeNodeId(el.node.data.nodeId);

            // `after_open` event can be triggered when pasting
            // is in progress (meaning we are pasting into a leaf node
            // in this case we do not need to update helpers state
            if (this.clipboard && !this.clipboard.isPasting) {
                that._updatePasteHelpersState();
            }
        });

        this.ui.document.on('keydown.pagetree.alt-mode', function(e) {
            if (e.keyCode === KEYS.SHIFT) {
                that.ui.container.addClass('cms-pagetree-alt-mode');
            }
        });

        this.ui.document.on('keyup.pagetree.alt-mode', function(e) {
            if (e.keyCode === KEYS.SHIFT) {
                that.ui.container.removeClass('cms-pagetree-alt-mode');
            }
        });

        $(window)
            .on(
                'mousemove.pagetree.alt-mode',
                debounce(function(e) {
                    if (e.shiftKey) {
                        that.ui.container.addClass('cms-pagetree-alt-mode');
                    } else {
                        that.ui.container.removeClass('cms-pagetree-alt-mode');
                    }
                }, 200) // eslint-disable-line no-magic-numbers
            )
            .on('blur.cms', () => {
                that.ui.container.removeClass('cms-pagetree-alt-mode');
            });

        this.ui.document.on('dnd_start.vakata', function(e, data) {
            var element = $(data.element);
            var node = element.parent();

            that._dropdowns.closeAllDropdowns();

            node.addClass('jstree-is-dragging');
            data.data.nodes.forEach(function(nodeId) {
                var descendantIds = that._getDescendantsIds(nodeId);

                [nodeId].concat(descendantIds).forEach(function(id) {
                    $('.jsgrid_' + id + '_col').addClass('jstree-is-dragging');
                });
            });

            if (!node.hasClass('jstree-leaf')) {
                data.helper.addClass('is-stacked');
            }
        });

        var isCopyClassAdded = false;

        this.ui.document.on('dnd_move.vakata', function(e, data) {
            var isMovingCopy =
                data.data.origin &&
                (data.data.origin.settings.dnd.always_copy ||
                    (data.data.origin.settings.dnd.copy && (data.event.metaKey || data.event.ctrlKey)));

            if (isMovingCopy) {
                if (!isCopyClassAdded) {
                    $('.jstree-is-dragging').addClass('jstree-is-dragging-copy');
                    isCopyClassAdded = true;
                }
            } else if (isCopyClassAdded) {
                $('.jstree-is-dragging').removeClass('jstree-is-dragging-copy');
                isCopyClassAdded = false;
            }
        });

        this.ui.document.on('dnd_stop.vakata', function(e, data) {
            var element = $(data.element);
            var node = element.parent();

            node.removeClass('jstree-is-dragging jstree-is-dragging-copy');
            data.data.nodes.forEach(function(nodeId) {
                var descendantIds = that._getDescendantsIds(nodeId);

                [nodeId].concat(descendantIds).forEach(function(id) {
                    $('.jsgrid_' + id + '_col').removeClass('jstree-is-dragging jstree-is-dragging-copy');
                });
            });
        });

        // store moved position node
        this.ui.tree.on('move_node.jstree copy_node.jstree', function(e, obj) {
            if ((!that.clipboard.type && e.type !== 'copy_node') || that.clipboard.type === 'cut') {
                that._moveNode(that._getNodePosition(obj)).done(function() {
                    var instance = that.ui.tree.jstree(true);

                    instance._hide_grid(instance.get_node(obj.parent));
                    if (obj.parent === '#' || (obj.node && obj.node.data && obj.node.data.isHome)) {
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
        this.ui.container.on(this.click, '.js-cms-tree-item-cut', function(e) {
            e.preventDefault();
            that._cutOrCopy({ type: 'cut', element: $(this) });
        });

        // set event for cut and paste
        this.ui.container.on(this.click, '.js-cms-tree-item-copy', function(e) {
            e.preventDefault();
            that._cutOrCopy({ type: 'copy', element: $(this) });
        });

        // attach events to paste
        this.ui.container.on(this.click, this.options.pasteSelector, function(e) {
            e.preventDefault();
            if ($(this).hasClass('cms-pagetree-dropdown-item-disabled')) {
                return;
            }
            that._paste(e);
        });

        // advanced settings link handling
        this.ui.container.on(this.click, '.js-cms-tree-advanced-settings', function(e) {
            if (e.shiftKey) {
                e.preventDefault();
                var link = $(this);

                if (link.data('url')) {
                    window.location.href = link.data('url');
                }
            }
        });

        // when adding new pages - expand nodes as well
        this.ui.container.on(this.click, '.js-cms-pagetree-add-page', e => {
            const treeId = this._getNodeId($(e.target));

            const nodeData = this.ui.tree.jstree('get_node', treeId);

            this._storeNodeId(nodeData.data.id);
        });

        // add events for error reload (messagelist)
        this.ui.document.on(this.click, '.messagelist .cms-tree-reload', function(e) {
            e.preventDefault();
            that._reloadHelper();
        });

        // propagate the sites dropdown "li > a" entries to the hidden sites form
        this.ui.container.find('.js-cms-pagetree-site-trigger').on(this.click, function(e) {
            e.preventDefault();
            var el = $(this);

            // prevent if parent is active
            if (el.parent().hasClass('active')) {
                return false;
            }
            that.ui.siteForm.find('select').val(el.data().id).end().submit();
        });

        // additional event handlers
        this._setupDropdowns();
        this._setupSearch();

        // make sure ajax post requests are working
        this._setAjaxPost('.js-cms-tree-item-menu a');
        this._setAjaxPost('.js-cms-tree-lang-trigger');
        this._setAjaxPost('.js-cms-tree-item-set-home a');

        this._setupPageView();
        this._setupStickyHeader();

        this.ui.tree.on('ready.jstree', () => this._getClipboard());
    },

    _getClipboard: function _getClipboard() {
        this.clipboard = CMS.settings.pageClipboard || this.clipboard;

        if (this.clipboard.type && this.clipboard.origin) {
            this._enablePaste();
            this._updatePasteHelpersState();
        }
    },

    /**
     * Helper to process the cut and copy events.
     *
     * @method _cutOrCopy
     * @param {Object} [obj]
     * @param {Number} [obj.type] either 'cut' or 'copy'
     * @param {Number} [obj.element] originated trigger element
     * @private
     * @returns {Boolean|void}
     */
    _cutOrCopy: function _cutOrCopy(obj) {
        // prevent actions if you try to copy a page with an apphook
        if (obj.type === 'copy' && obj.element.data().apphook) {
            this.showError(this.options.lang.apphook);
            return false;
        }

        var jsTreeId = this._getNodeId(obj.element.closest('.jstree-grid-cell'));

        // resets if we click again
        if (this.clipboard.type === obj.type && jsTreeId === this.clipboard.id) {
            this.clipboard.type = null;
            this.clipboard.id = null;
            this.clipboard.origin = null;
            this.clipboard.source_site = null;
            this._disablePaste();
        } else {
            this.clipboard.origin = obj.element.data().id; // this._getNodeId(obj.element);
            this.clipboard.type = obj.type;
            this.clipboard.id = jsTreeId;
            this.clipboard.source_site = this.options.site;
            this._updatePasteHelpersState();
        }
        if (this.clipboard.type === 'copy' || !this.clipboard.type) {
            CMS.settings.pageClipboard = this.clipboard;
            Helpers.setSettings(CMS.settings);
        }
    },

    /**
     * Helper to process the paste event.
     *
     * @method _paste
     * @param {$.Event} event click event
     * @private
     */
    _paste: function _paste(event) {
        // hide helpers after we picked one
        this._disablePaste();

        var copyFromId = this._getNodeId(
            $(`.js-cms-pagetree-options[data-id="${this.clipboard.origin}"]`).closest('.jstree-grid-cell')
        );
        var copyToId = this._getNodeId($(event.currentTarget));

        if (this.clipboard.source_site === this.options.site) {
            if (this.clipboard.type === 'cut') {
                this.ui.tree.jstree('cut', copyFromId);
            } else {
                this.ui.tree.jstree('copy', copyFromId);
            }

            this.clipboard.isPasting = true;
            this.ui.tree.jstree('paste', copyToId, 'last');
        } else {
            const dummyId = this.ui.tree.jstree('create_node', copyToId, 'Loading', 'last');

            if (this.ui.tree.length) {
                this.ui.tree.jstree('cut', dummyId);
                this.clipboard.isPasting = true;
                this.ui.tree.jstree('paste', copyToId, 'last');
            } else {
                if (this.clipboard.type === 'copy') {
                    this._copyNode();
                }
                if (this.clipboard.type === 'cut') {
                    this._moveNode();
                }
            }
        }

        this.clipboard.id = null;
        this.clipboard.type = null;
        this.clipboard.origin = null;
        this.clipboard.isPasting = false;
        CMS.settings.pageClipboard = this.clipboard;
        Helpers.setSettings(CMS.settings);
    },

    /**
     * Retreives a list of nodes from local storage.
     *
     * @method _getStoredNodeIds
     * @private
     * @returns {Array} list of ids
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
     * @returns {String} id that has been stored
     */
    _storeNodeId: function _storeNodeId(id) {
        var number = id;
        var storage = this._getStoredNodeIds();

        // store value only if it isn't there yet
        if (storage.indexOf(number) === -1) {
            storage.push(number);
        }

        CMS.settings.pagetree = storage;
        Helpers.setSettings(CMS.settings);

        return number;
    },

    /**
     * Removes a node in local storage.
     *
     * @method _removeNodeId
     * @private
     * @param {String} id to be stored
     * @returns {String} id that has been removed
     */
    _removeNodeId: function _removeNodeId(id) {
        const instance = this.ui.tree.jstree(true);
        const childrenIds = instance.get_node({
            id: CMS.$(`[data-node-id=${id}]`).attr('id')
        }).children_d;

        const idsToRemove = [id].concat(
            childrenIds.map(childId => {
                const node = instance.get_node({ id: childId });

                if (!node || !node.data) {
                    return node;
                }

                return node.data.nodeId;
            })
        );

        const storage = without(this._getStoredNodeIds(), ...idsToRemove);

        CMS.settings.pagetree = storage;
        Helpers.setSettings(CMS.settings);

        return id;
    },

    /**
     * Moves a node after drag & drop.
     *
     * @method _moveNode
     * @param {Object} [obj]
     * @param {Number} [obj.id] current element id for url matching
     * @param {Number} [obj.target] target sibling or parent
     * @param {Number} [obj.position] either `left`, `right` or `last-child`
     * @returns {$.Deferred} ajax request object
     * @private
     */
    _moveNode: function _moveNode(obj) {
        var that = this;

        if (!obj.id && this.clipboard.type === 'cut' && this.clipboard.origin) {
            obj.id = this.clipboard.origin;
            obj.source_site = this.clipboard.source_site;
        } else {
            obj.site = that.options.site;
        }

        return $.ajax({
            method: 'post',
            url: that.options.urls.move.replace('{id}', obj.id),
            data: obj
        })
            .done(function(r) {
                if (r.status && r.status === 400) { // eslint-disable-line
                    that.showError(r.content);
                } else {
                    that._showSuccess(obj.id);
                }
            })
            .fail(function(error) {
                that.showError(error.statusText);
            });
    },

    /**
     * Copies a node into the selected node.
     *
     * @method _copyNode
     * @param {Object} obj page obj
     * @private
     */
    _copyNode: function _copyNode(obj) {
        var that = this;
        var node = { position: 0 };

        if (obj) {
            node = that._getNodePosition(obj);
        }

        var data = {
            // obj.original.data.id is for drag copy
            id: this.clipboard.origin || obj.original.data.id,
            position: node.position
        };

        if (this.clipboard.source_site) {
            data.source_site = this.clipboard.source_site;
        } else {
            data.source_site = this.options.site;
        }

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
            })
                .done(function(dialog) {
                    that.ui.dialog.append(dialog);
                })
                .fail(function(error) {
                    that.showError(error.statusText);
                });

            // attach events to the permission dialog
            this.ui.dialog
                .off(this.click, '.cancel')
                .on(this.click, '.cancel', function(e) {
                    e.preventDefault();
                    // remove just copied node
                    that.ui.tree.jstree('delete_node', obj.node.id);
                    $('.js-cms-dialog').remove();
                    $('.js-cms-dialog-dimmer').remove();
                })
                .off(this.click, '.submit')
                .on(this.click, '.submit', function(e) {
                    e.preventDefault();
                    var submitButton = $(this);
                    var formData = submitButton.closest('form').serialize().split('&');

                    submitButton.prop('disabled', true);

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
     * @returns {$.Deferred}
     */
    _saveCopiedNode: function _saveCopiedNode(data) {
        var that = this;

        // send the real ajax request for copying the plugin
        return $.ajax({
            method: 'post',
            url: that.options.urls.copy.replace('{id}', data.id),
            data: data
        })
            .done(function(r) {
                if (r.status && r.status === 400) { // eslint-disable-line
                    that.showError(r.content);
                } else {
                    that._reloadHelper();
                }
            })
            .fail(function(error) {
                that.showError(error.statusText);
            });
    },

    /**
     * Returns element from any sub nodes.
     *
     * @method _getElement
     * @private
     * @param {jQuery} el jQuery node form where to search
     * @returns {String} jsTree node element id
     */
    _getNodeId: function _getNodeId(el) {
        var cls = el.closest('.jstree-grid-cell').attr('class');

        // if it's not a cell, assume it's the root node
        return cls ? cls.replace(/.*jsgrid_(.+?)_col.*/, '$1') : '#';
    },

    /**
     * Gets the new node position after moving.
     *
     * @method _getNodePosition
     * @private
     * @param {Object} obj jstree move object
     * @returns {Object} evaluated object with params
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
     * Sets up general tooltips that can have a list of links or content.
     *
     * @method _setupDropdowns
     * @private
     */
    _setupDropdowns: function _setupDropdowns() {
        this._dropdowns = new PageTreeDropdowns({
            container: this.ui.container
        });
    },

    /**
     * Handles page view click. Usual use case is that after you click
     * on view page in the pagetree - sideframe is no longer needed,
     * so we close it.
     *
     * @method _setupPageView
     * @private
     */
    _setupPageView: function _setupPageView() {
        var win = Helpers._getWindow();
        var parent = win.parent ? win.parent : win;

        this.ui.container.on(this.click, '.js-cms-pagetree-page-view', function() {
            parent.CMS.API.Helpers.setSettings(
                $.extend(true, {}, CMS.settings, {
                    sideframe: {
                        url: null,
                        hidden: true
                    }
                })
            );
        });
    },

    /**
     * @method _setupStickyHeader
     * @private
     */
    _setupStickyHeader: function _setupStickyHeader() {
        var that = this;

        that.ui.tree.on('ready.jstree', function() {
            that.header = new PageTreeStickyHeader({
                container: that.ui.container
            });
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

        this.ui.container.on(this.click, trigger, function(e) {
            e.preventDefault();

            var element = $(this);

            if (element.closest('.cms-pagetree-dropdown-item-disabled').length) {
                return;
            }

            try {
                window.top.CMS.API.Toolbar.showLoader();
            } catch (err) {}

            $.ajax({
                method: 'post',
                url: $(this).attr('href')
            })
                .done(function() {
                    try {
                        window.top.CMS.API.Toolbar.hideLoader();
                    } catch (err) {}

                    if (window.self === window.top) {
                        // simply reload the page
                        that._reloadHelper();
                    } else {
                        // if we're in the sideframe we have to actually
                        // check if we are publishing a page we're currently in
                        // because if the slug did change we would need to
                        // redirect to that new slug
                        // Problem here is that in case of the apphooked page
                        // the model and pk are empty and reloadBrowser doesn't really
                        // do anything - so here we specifically force the data
                        // to be the data about the page and not the model
                        var parent = window.parent ? window.parent : window;
                        var data = {
                            // this shouldn't be hardcoded, but there is no way around it
                            model: 'cms.page',
                            pk: parent.CMS.config.request.page_id
                        };

                        Helpers.reloadBrowser('REFRESH_PAGE', false, true, data);
                    }
                })
                .fail(function(error) {
                    that.showError(error.statusText);
                });
        });
    },

    /**
     * Sets events for the search on the header.
     *
     * @method _setupSearch
     * @private
     */
    _setupSearch: function _setupSearch() {
        var that = this;
        var click = this.click + '.search';

        var filterActive = false;
        var filterTrigger = this.ui.container.find('.js-cms-pagetree-header-filter-trigger');
        var filterContainer = this.ui.container.find('.js-cms-pagetree-header-filter-container');
        var filterClose = filterContainer.find('.js-cms-pagetree-header-search-close');
        var filterClass = 'cms-pagetree-header-filter-active';
        var pageTreeHeader = $('.cms-pagetree-header');

        var visibleForm = this.ui.container.find('.js-cms-pagetree-header-search');
        var hiddenForm = this.ui.container.find('.js-cms-pagetree-header-search-copy form');

        var searchContainer = this.ui.container.find('.cms-pagetree-header-filter');
        var searchField = searchContainer.find('#field-searchbar');
        var timeout = 200;

        // add active class when focusing the search field
        searchField.on('focus', function(e) {
            e.stopImmediatePropagation();
            pageTreeHeader.addClass(filterClass);
        });
        searchField.on('blur', function(e) {
            e.stopImmediatePropagation();
            // timeout is required to prevent the search field from jumping
            // between enlarging and shrinking
            setTimeout(function() {
                if (!filterActive) {
                    pageTreeHeader.removeClass(filterClass);
                }
            }, timeout);
            that.ui.document.off(click);
        });

        // shows/hides filter box
        filterTrigger.add(filterClose).on(click, function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (filterActive) {
                filterContainer.hide();
                pageTreeHeader.removeClass(filterClass);
                that.ui.document.off(click);
                filterActive = false;
            } else {
                filterContainer.show();
                pageTreeHeader.addClass(filterClass);
                that.ui.document.on(click, function() {
                    filterActive = true;
                    filterTrigger.trigger(click);
                });
                filterActive = true;
            }
        });

        // prevent closing when on filter container
        filterContainer.on('click', function(e) {
            e.stopImmediatePropagation();
        });

        // add hidden fields to the form to maintain filter params
        visibleForm.append(hiddenForm.find('input[type="hidden"]'));
    },

    /**
     * Shows paste helpers.
     *
     * @method _enablePaste
     * @param {String} [selector=this.options.pasteSelector] jquery selector
     * @private
     */
    _enablePaste: function _enablePaste(selector) {
        var sel = typeof selector === 'undefined'
            ? this.options.pasteSelector
            : selector + ' ' + this.options.pasteSelector;
        var dropdownSel = '.js-cms-pagetree-actions-dropdown';

        if (typeof selector !== 'undefined') {
            dropdownSel = selector + ' .js-cms-pagetree-actions-dropdown';
        }

        // helpers are generated on the fly, so we need to reference
        // them every single time
        $(sel).removeClass('cms-pagetree-dropdown-item-disabled');

        var data = {};

        if (this.clipboard.type === 'cut') {
            data.has_cut = true;
        } else {
            data.has_copy = true;
        }
        // not loaded actions dropdown have to be updated as well
        $(dropdownSel).data('lazyUrlData', data);
    },

    /**
     * Hides paste helpers.
     *
     * @method _disablePaste
     * @param {String} [selector=this.options.pasteSelector] jquery selector
     * @private
     */
    _disablePaste: function _disablePaste(selector) {
        var sel = typeof selector === 'undefined'
            ? this.options.pasteSelector
            : selector + ' ' + this.options.pasteSelector;
        var dropdownSel = '.js-cms-pagetree-actions-dropdown';

        if (typeof selector !== 'undefined') {
            dropdownSel = selector + ' .js-cms-pagetree-actions-dropdown';
        }

        // helpers are generated on the fly, so we need to reference
        // them every single time
        $(sel).addClass('cms-pagetree-dropdown-item-disabled');

        // not loaded actions dropdown have to be updated as well
        $(dropdownSel).removeData('lazyUrlData');
    },

    /**
     * Updates the current state of the helpers after `after_open.jstree`
     * or `_cutOrCopy` is triggered.
     *
     * @method _updatePasteHelpersState
     * @private
     */
    _updatePasteHelpersState: function _updatePasteHelpersState() {
        var that = this;

        if (this.clipboard.type && this.clipboard.id) {
            this._enablePaste();
        }

        // hide cut element and it's descendants' paste helpers if it is visible
        if (
            this.clipboard.type === 'cut' &&
            this.clipboard.origin &&
            this.options.site === this.clipboard.source_site
        ) {
            var descendantIds = this._getDescendantsIds(this.clipboard.id);
            var nodes = [this.clipboard.id];

            if (descendantIds && descendantIds.length) {
                nodes = nodes.concat(descendantIds);
            }

            nodes.forEach(function(id) {
                that._disablePaste('.jsgrid_' + id + '_col');
            });
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
        setTimeout(function() {
            element.removeClass('cms-tree-node-success');
        }, this.successTimer);
        // hide elements
        this._disablePaste();
        this.clipboard.id = null;
    },

    /**
     * Checks if we should reload the iframe or entire window. For this we
     * need to skip `CMS.API.Helpers.reloadBrowser();`.
     *
     * @method _reloadHelper
     * @private
     */
    _reloadHelper: function _reloadHelper() {
        if (window.self === window.top) {
            Helpers.reloadBrowser();
        } else {
            window.location.reload();
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
        var tpl =
            '' +
            '<ul class="messagelist">' +
            '   <li class="error">' +
            '       {msg} ' +
            '       <a href="#reload" class="cms-tree-reload"> ' +
            reload +
            ' </a>' +
            '   </li>' +
            '</ul>';
        var msg = tpl.replace('{msg}', '<strong>' + this.options.lang.error + '</strong> ' + message);

        if (messages.length) {
            messages.replaceWith(msg);
        } else {
            breadcrumb.after(msg);
        }
    },

    /**
     * @method _getDescendantsIds
     * @private
     * @param {String} nodeId jstree id of the node, e.g. j1_3
     * @returns {String[]} array of ids
     */
    _getDescendantsIds: function _getDescendantsIds(nodeId) {
        return this.ui.tree.jstree(true).get_node(nodeId).children_d;
    },

    /**
     * @method _hasPermision
     * @private
     * @param {Object} node jstree node
     * @param {String} permission move / add
     * @returns {Boolean}
     */
    _hasPermission: function _hasPermision(node, permission) {
        if (node.id === '#' && permission === 'add') {
            return this.options.hasAddRootPermission;
        } else if (node.id === '#') {
            return false;
        }

        return node.li_attr['data-' + permission + '-permission'] === 'true';
    }
});

PageTree._init = function() {
    new PageTree();
};

// shorthand for jQuery(document).ready();
$(function() {
    // load cms settings beforehand
    // have to set toolbar to "expanded" by default
    // otherwise initialization will be incorrect when you
    // go first to pages and then to normal page
    window.CMS.config = {
        isPageTree: true,
        settings: {
            toolbar: 'expanded',
            version: __CMS_VERSION__
        },
        urls: {
            settings: $('.js-cms-pagetree').data('settings-url')
        }
    };
    window.CMS.settings = Helpers.getSettings();
    // autoload the pagetree
    CMS.PageTree._init();
});

export default PageTree;

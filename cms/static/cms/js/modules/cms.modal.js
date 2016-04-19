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
         * The modal is triggered via API calls from the backend either
         * through the toolbar navigation or from plugins. The APIs allow to
         * open content from a url (iframe) or inject html directly.
         *
         * @class Modal
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.Modal = new CMS.Class({

            implement: [CMS.API.Helpers],

            options: {
                onClose: false,
                minHeight: 400,
                minWidth: 800,
                modalDuration: 200,
                newPlugin: false,
                resizable: true,
                maximizable: true,
                minimizable: true
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);

                // elements
                this._setupUI();
                // event emitter
                this._setupEventEmitter();

                // states and events
                this.click = 'click.cms.modal';
                this.pointerDown = 'pointerdown.cms.modal contextmenu.cms.modal';
                this.pointerUp = 'pointerup.cms.modal pointercancel.cms.modal';
                this.pointerMove = 'pointermove.cms.modal';
                this.doubleClick = 'dblclick.cms.modal';
                this.touchEnd = 'touchend.cms.modal';
                this.maximized = false;
                this.minimized = false;
                this.triggerMaximized = false;
                this.saved = false;
            },

            /**
             * Setup event pubsub mechanism for the instance.
             *
             * @private
             * @method _setupEventEmitter
             */
            _setupEventEmitter: function _setupEventEmitter() {
                var that = this;
                var bus = $({});

                function proxy(name) {
                    return function () {
                        bus[name].apply(bus, arguments);
                        return that;
                    };
                }

                this.trigger = proxy('trigger');
                this.one = proxy('one');
                this.on = proxy('on');
                this.off = proxy('off');
            },

            /**
             * Stores all jQuery references within `this.ui`.
             *
             * @method _setupUI
             * @private
             */
            _setupUI: function _setupUI() {
                var modal = $('.cms-modal');
                this.ui = {
                    modal: modal,
                    body: $('html'),
                    window: $(window),
                    toolbarLeftPart: $('.cms-toolbar-left'),
                    minimizeButton: modal.find('.cms-modal-minimize'),
                    maximizeButton: modal.find('.cms-modal-maximize'),
                    title: modal.find('.cms-modal-title'),
                    titlePrefix: modal.find('.cms-modal-title-prefix'),
                    titleSuffix: modal.find('.cms-modal-title-suffix'),
                    resize: modal.find('.cms-modal-resize'),
                    breadcrumb: modal.find('.cms-modal-breadcrumb'),
                    closeAndCancel: modal.find('.cms-modal-close, .cms-modal-cancel'),
                    modalButtons: modal.find('.cms-modal-buttons'),
                    modalBody: modal.find('.cms-modal-body'),
                    frame: modal.find('.cms-modal-frame'),
                    shim: modal.find('.cms-modal-shim')
                };
            },

            /**
             * Sets up all the event handlers, such as maximize/minimize and resizing.
             *
             * @method _events
             * @private
             */
            _events: function _events() {
                var that = this;

                // modal behaviours
                this.ui.minimizeButton.
                    off(this.click + ' ' + this.touchEnd)
                    .on(this.click + ' ' + this.touchEnd, function (e) {
                    e.preventDefault();
                    that.minimize();
                });
                this.ui.maximizeButton
                    .off(this.click + ' ' + this.touchEnd)
                    .on(this.click + ' ' + this.touchEnd, function (e) {
                    e.preventDefault();
                    that.maximize();
                });

                this.ui.title.off(this.pointerDown).on(this.pointerDown, function (e) {
                    e.preventDefault();
                    that._startMove(e);
                });
                this.ui.title.off(this.doubleClick).on(this.doubleClick, function () {
                    that.maximize();
                });

                this.ui.resize.off(this.pointerDown).on(this.pointerDown, function (e) {
                    e.preventDefault();
                    that._startResize(e);
                });

                this.ui.closeAndCancel
                    .off(this.click + ' ' + this.touchEnd)
                    .on(this.click + ' ' + this.touchEnd, function (e) {
                    that.options.onClose = null;
                    e.preventDefault();
                    that.close();
                });

                // elements within the window
                this.ui.breadcrumb.off(this.click, 'a').on(this.click, 'a', function (e) {
                    e.preventDefault();
                    that._changeIframe($(this));
                });
            },

            /**
             * Opens the modal either in an iframe or renders markup.
             *
             * @method open
             * @chainable
             * @param {Object} opts either `opts.url` or `opts.html` are required
             * @param {Object[]} [opts.breadcrumbs] collection of breadcrumb items
             * @param {String|HTMLNode|jQuery} [opts.html] html markup to render
             * @param {String} [opts.title] modal window main title (bold)
             * @param {String} [opts.subtitle] modal window secondary title (normal)
             * @param {String} [opts.url] url to render iframe, takes precedence over `opts.html`
             * @param {Number} [opts.width] sets the width of the modal
             * @param {Number} [opts.height] sets the height of the modal
             */
            open: function open(opts) {
                // setup internals
                if (!(opts && opts.url || opts && opts.html)) {
                    throw new Error('The arguments passed to "open" were invalid.');
                }

                // handle remove option when plugin is new
                // cancel open process when switching context
                if (CMS._newPlugin && !this._deletePlugin()) {
                    return false;
                }

                // We have to rebind events every time we open a modal
                // because the event handlers contain references to the instance
                // and since we reuse the same markup we need to update
                // that instance reference every time.
                this._events();

                this.trigger('cms.modal.load');
                // trigger the event also on the dom element,
                // because if we load another modal while one is already open
                // the older instance won't receive any updates
                this.ui.modal.trigger('cms.modal.load');

                // common elements state
                this.ui.resize.toggle(this.options.resizable);
                this.ui.minimizeButton.toggle(this.options.minimizable);
                this.ui.maximizeButton.toggle(this.options.maximizable);

                var position = this._calculateNewPosition(opts);

                this.ui.maximizeButton.removeClass('cms-modal-maximize-active');
                this.maximized = false;

                // new plugin will freeze the creation process
                if (this.options.newPlugin) {
                    CMS._newPlugin = this.options.newPlugin;
                }

                // because a new instance is called, we have to ensure minimized state is removed #3620
                if (this.ui.body.hasClass('cms-modal-minimized')) {
                    this.minimized = true;
                    this.minimize();
                }

                // clear elements
                this.ui.modalButtons.empty();
                this.ui.breadcrumb.empty();

                // remove class from modal when no breadcrumbs is rendered
                this.ui.modal.removeClass('cms-modal-has-breadcrumb');

                // hide tooltip
                CMS.API.Tooltip.hide();

                // redirect to iframe rendering if url is provided
                if (opts.url) {
                    this._loadIframe({
                        url: opts.url,
                        title: opts.title,
                        breadcrumbs: opts.breadcrumbs
                    });
                } else {
                    // if url is not provided we go for html
                    this._loadMarkup({
                        html: opts.html,
                        title: opts.title,
                        subtitle: opts.subtitle
                    });
                }

                this.trigger('cms.modal.loaded');

                // display modal
                this._show($.extend({
                    duration: this.options.modalDuration
                }, position));

                return this;
            },

            /**
             * Calculates coordinates and dimensions for modal placement
             *
             * @method _calculateNewPosition
             * @private
             * @param {Object} [opts]
             * @param {Number} [opts.width] desired width of the modal
             * @param {Number} [opts.height] desired height of the modal
             */
            _calculateNewPosition: function (opts) {
                // lets set the modal width and height to the size of the browser
                var widthOffset = 300; // adds margin left and right
                var heightOffset = 300; // adds margin top and bottom;
                var screenWidth = this.ui.window.width();
                var screenHeight = this.ui.window.height();
                var modalWidth = opts.width || this.options.minWidth;
                var modalHeight = opts.height || this.options.minHeight;
                // screen width and height calculation, WC = width
                var screenWidthCalc = screenWidth >= (modalWidth + widthOffset);
                var screenHeightCalc = screenHeight >= (modalHeight + heightOffset);

                var width = screenWidthCalc && !opts.width ? screenWidth - widthOffset : modalWidth;
                var height = screenHeightCalc && !opts.height ? screenHeight - heightOffset : modalHeight;

                var currentLeft = this.ui.modal.css('left');
                var currentTop = this.ui.modal.css('top');
                var newLeft;
                var newTop;

                // jquery made me do it
                if (currentLeft === '50%') {
                    currentLeft = screenWidth / 2;
                }
                if (currentTop === '50%') {
                    currentTop = screenHeight / 2;
                }

                currentTop = parseInt(currentTop);
                currentLeft = parseInt(currentLeft);

                // if new width/height go out of the screen - reset position to center of screen
                if ((width / 2 + currentLeft > screenWidth) || (height / 2 + currentTop > screenHeight) ||
                    (currentLeft - width / 2 < 0) || (currentTop - height / 2 < 0)) {
                    newLeft = screenWidth / 2;
                    newTop = screenHeight / 2;
                }

                // in case, the modal is larger than the window, we trigger fullscreen mode
                if (width >= screenWidth || height >= screenHeight) {
                    this.triggerMaximized = true;
                }

                return {
                    width: width,
                    height: height,
                    top: newTop,
                    left: newLeft
                };
            },

            /**
             * Animation helper for opening the sideframe.
             *
             * @method _show
             * @private
             * @param {Object} opts
             * @param {Number} opts.width width of the modal
             * @param {Number} opts.height height of the modal
             * @param {Number} opts.left left in px of the center of the modal
             * @param {Number} opts.top top in px of the center of the modal
             * @param {Number} opts.duration speed of opening, ms (not really used yet)
             */
            _show: function _show(opts) {
                // we need to position the modal in the center
                var that = this;
                var width = opts.width;
                var height = opts.height;
                // TODO make use of transitionDuration, currently capped at 0.2s
                var speed = opts.duration;
                var top = opts.top;
                var left = opts.left;


                if (this.ui.modal.hasClass('cms-modal-open')) {
                    this.ui.modal.addClass('cms-modal-morphing');
                }

                this.ui.modal.css({
                    'display': 'block',
                    'width': width,
                    'height': height,
                    'top': top,
                    'left': left,
                    // TODO animate translateX if possible instead of margin
                    'margin-left': -(width / 2),
                    'margin-top': -(height / 2)
                });
                // setImmediate is required to go into the next frame
                setTimeout(function () {
                    that.ui.modal.addClass('cms-modal-open');
                }, 0);

                this.ui.modal.one('cmsTransitionEnd', function () {
                    that.ui.modal.removeClass('cms-modal-morphing');
                    that.ui.modal.css({
                        'margin-left': -(width / 2),
                        'margin-top': -(height / 2)
                    });

                    // check if we should maximize
                    if (that.triggerMaximized) {
                        that.maximize();
                    }

                    // changed locked status to allow other modals again
                    CMS.API.locked = false;
                    that.trigger('cms.modal.shown');
                }).emulateTransitionEnd(speed);

                // add esc close event
                this.ui.body.off('keydown.cms.close').on('keydown.cms.close', function (e) {
                    if (e.keyCode === CMS.KEYS.ESC) {
                        that.options.onClose = null;
                        that.close();
                    }
                });

                // set focus to modal
                this.ui.modal.focus();
            },

            /**
             * Closes the current instance.
             *
             * @method close
             */
            close: function close() {
                // handle refresh option
                if (this.options.onClose) {
                    this.reloadBrowser(this.options.onClose, false, true);
                }

                // handle remove option when plugin is new
                if (CMS._newPlugin) {
                    this._deletePlugin({
                        hideAfter: true
                    });
                } else {
                    this._hide({
                        duration: this.options.modalDuration / 2
                    });
                }
            },

            /**
             * Animation helper for closing the iframe.
             *
             * @method _hide
             * @private
             * @param {Object} opts
             * @param {Number} [opts.duration=this.options.modalDuration] animation duration
             */
            _hide: function _hide(opts) {
                var that = this;
                var duration = this.options.modalDuration;

                if (opts && opts.duration) {
                    duration = opts.duration;
                }

                this.ui.frame.empty();
                this.ui.modalBody.removeClass('cms-loader');
                this.ui.modal.removeClass('cms-modal-open');
                this.ui.modal.one('cmsTransitionEnd', function () {
                    that.ui.modal.css('display', 'none');
                }).emulateTransitionEnd(duration);

                // reset maximize or minimize states for #3111
                setTimeout(function () {
                    if (that.minimized) {
                        that.minimize();
                    }
                    if (that.maximized) {
                        that.maximize();
                    }
                    that.trigger('cms.modal.closed');
                }, this.options.duration);

                this.ui.body.off('keydown.cms.close');
            },

            /**
             * Minimizes the modal onto the toolbar.
             *
             * @method minimize
             */
            minimize: function minimize() {
                // cancel action if maximized
                if (this.maximized) {
                    return false;
                }

                if (this.minimized === false) {
                    // ensure toolbar is shown
                    CMS.API.Toolbar.open();

                    // save initial state
                    this.ui.modal.data('css', this.ui.modal.css([
                        'left', 'top', 'margin-left', 'margin-top'
                    ]));

                    // minimize
                    this.ui.body.addClass('cms-modal-minimized');
                    this.ui.modal.css({
                        'left': this.ui.toolbarLeftPart.outerWidth(true) + 50
                    });

                    this.minimized = true;
                } else {
                    // maximize
                    this.ui.body.removeClass('cms-modal-minimized');
                    this.ui.modal.css(this.ui.modal.data('css'));

                    this.minimized = false;
                }
            },

            /**
             * Maximizes the window according to the browser size.
             *
             * @method maximize
             */
            maximize: function maximize() {
                // cancel action when minimized
                if (this.minimized) {
                    return false;
                }

                if (this.maximized === false) {
                    // save initial state
                    this.ui.modal.data('css', this.ui.modal.css([
                        'left', 'top', 'margin-left', 'margin-top',
                        'width', 'height'
                    ]));

                    this.ui.body.addClass('cms-modal-maximized');

                    this.maximized = true;
                    this.dispatchEvent('modal-maximized', { instance: this });
                } else {
                    // minimize
                    this.ui.body.removeClass('cms-modal-maximized');
                    this.ui.modal.css(this.ui.modal.data('css'));

                    this.maximized = false;
                    this.dispatchEvent('modal-restored', { instance: this });
                }
            },

            /**
             * Initiates the start move event from `_events`.
             *
             * @method _startMove
             * @private
             * @param {Object} pointerEvent passes starting event
             */
            _startMove: function _startMove(pointerEvent) {
                // cancel if maximized or minimized
                if (this.maximized || this.minimized) {
                    return false;
                }

                var that = this;
                var position = this.ui.modal.position();
                var left;
                var top;

                this.ui.shim.show();

                // create event for stopping
                this.ui.body.on(this.pointerUp, function (e) {
                    that._stopMove(e);
                });

                this.ui.body.on(this.pointerMove, function (e) {
                    left = position.left - (pointerEvent.originalEvent.pageX - e.originalEvent.pageX);
                    top = position.top - (pointerEvent.originalEvent.pageY - e.originalEvent.pageY);

                    that.ui.modal.css({
                        'left': left,
                        'top': top
                    });
                }).attr('data-touch-action', 'none');
            },

            /**
             * Initiates the stop move event from `_startResize`.
             *
             * @method _stopMove
             * @private
             */
            _stopMove: function _stopMove() {
                this.ui.shim.hide();
                this.ui.body
                    .off(this.pointerMove + ' ' + this.pointerUp)
                    .removeAttr('data-touch-action');
            },

            /**
             * Initiates the start resize event from `_events`.
             *
             * @method _startResize
             * @private
             * @param {Object} pointerEvent passes starting event
             */
            _startResize: function _startResize(pointerEvent) {
                // cancel if in fullscreen
                if (this.maximized) {
                    return false;
                }
                // continue
                var that = this;
                var width = this.ui.modal.width();
                var height = this.ui.modal.height();
                var modalLeft = this.ui.modal.position().left;
                var modalTop = this.ui.modal.position().top;

                // create event for stopping
                this.ui.body.on(this.pointerUp, function (e) {
                    that._stopResize(e);
                });

                this.ui.shim.show();

                this.ui.body.on(this.pointerMove, function (e) {
                    var mvX = pointerEvent.originalEvent.pageX - e.originalEvent.pageX;
                    var mvY = pointerEvent.originalEvent.pageY - e.originalEvent.pageY;
                    var w = width - (mvX * 2);
                    var h = height - (mvY * 2);
                    var wMin = that.options.minWidth;
                    var hMin = that.options.minHeight;
                    var left = mvX + modalLeft;
                    var top = mvY + modalTop;

                    // add some limits
                    if (w <= wMin) {
                        w = wMin;
                        left = modalLeft + width / 2 - w / 2;
                    }
                    if (h <= hMin) {
                        h = hMin;
                        top = modalTop + height / 2 - h / 2;
                    }

                    // set centered animation
                    that.ui.modal.css({
                        width: w,
                        height: h,
                        left: left,
                        top: top
                    });
                }).attr('data-touch-action', 'none');
            },

            /**
             * Initiates the stop resize event from `_startResize`.
             *
             * @method _stopResize
             * @private
             */
            _stopResize: function _stopResize() {
                this.ui.shim.hide();
                this.ui.body
                    .off(this.pointerMove + ' ' + this.pointerUp)
                    .removeAttr('data-touch-action');
            },

            /**
             * Sets the breadcrumb inside the modal.
             *
             * @method _setBreadcrumb
             * @private
             * @param {Object[]} breadcrumbs renderes breadcrumb on modal
             */
            _setBreadcrumb: function _setBreadcrumb(breadcrumbs) {
                var crumb = '';
                var template = '<a href="{1}" class="{2}"><span>{3}</span></a>';

                // cancel if there is no breadcrumbs)
                if (!breadcrumbs || breadcrumbs.length <= 1) {
                    return false;
                }
                if (!breadcrumbs[0].title) {
                    return false;
                }

                // add class to modal
                this.ui.modal.addClass('cms-modal-has-breadcrumb');

                // load breadcrumbs
                $.each(breadcrumbs, function (index, item) {
                    // check if the item is the last one
                    var last = (index >= breadcrumbs.length - 1) ? 'active' : '';
                    // render breadcrumbs
                    crumb += template
                        .replace('{1}', item.url)
                        .replace('{2}', last)
                        .replace('{3}', item.title);
                });

                // attach elements
                this.ui.breadcrumb.html(crumb);
            },

            /**
             * Sets the buttons inside the modal.
             *
             * @method _setButtons
             * @private
             * @param {jQuery} iframe loaded iframe element
             */
            _setButtons: function _setButtons(iframe) {
                var djangoSuit = iframe.contents().find('.suit-columns').length > 0;
                var that = this;
                var group = $('<div class="cms-modal-item-buttons"></div>');
                var render = $('<div class="cms-modal-buttons-inner"></div>');
                var cancel = $('<a href="#" class="cms-btn">' + CMS.config.lang.cancel + '</a>');
                var row;
                var tmp;

                if (!djangoSuit) {
                    row = iframe.contents().find('.submit-row:eq(0)');
                } else {
                    row = iframe.contents().find('.save-box:eq(0)');
                }
                var form = iframe.contents().find('form');
                //avoids conflict between the browser's form validation and Django's validation
                form.on('submit', function () {
                    // default submit button was clicked
                    // meaning, if you have save - it should close the iframe,
                    // if you hit save and continue editing it should be default form behaviour
                    if (that.hideFrame) {
                        that.ui.modal.find('.cms-modal-frame iframe').hide();
                        // page has been saved, run checkup
                        that.saved = true;
                    }
                });
                var buttons = row.find('input, a, button');
                // these are the buttons _inside_ the iframe
                // we need to listen to this click event to support submitting
                // a form by pressing enter inside of a field
                // click is actually triggered by submit
                buttons.on('click', function () {
                    if ($(this).hasClass('default')) {
                        that.hideFrame = true;
                    }
                });

                // hide all submit-rows
                iframe.contents().find('.submit-row').hide();

                // if there are no given buttons within the submit-row area
                // scan deeper within the form itself
                if (!buttons.length) {
                    row = iframe.contents().find('body:not(.change-list) #content form:eq(0)');
                    buttons = row.find('input[type="submit"], button[type="submit"]');
                    buttons.addClass('deletelink').hide();
                }

                // loop over input buttons
                buttons.each(function (index, item) {
                    item = $(item);
                    item.attr('data-rel', '_' + index);

                    // cancel if item is a hidden input
                    if (item.attr('type') === 'hidden') {
                        return false;
                    }

                    var title = item.attr('value') || item.text();
                    var cls = 'cms-btn';

                    if (item.is('button')) {
                        title = item.text();
                    }

                    // set additional special css classes
                    if (item.hasClass('default')) {
                        cls = 'cms-btn cms-btn-action';
                    }
                    if (item.hasClass('deletelink')) {
                        cls = 'cms-btn cms-btn-caution';
                    }

                    var el = $('<a href="#" class="' + cls + ' ' + item.attr('class') + '">' + title + '</a>');

                    el.on(that.click + ' ' + that.touchEnd, function (e) {
                        e.preventDefault();

                        if (item.is('a')) {
                            that._loadIframe({
                                url: item.prop('href'),
                                name: title
                            });
                        }

                        // trigger only when blue action buttons are triggered
                        if (item.hasClass('default') || item.hasClass('deletelink')) {
                            if (!item.hasClass('default')) { // hide iframe when using buttons other than submit
                                that.ui.modal.find('.cms-modal-frame iframe').hide();
                                // page has been saved or deleted, run checkup
                                that.saved = true;
                            } else { // submit button uses the form's submit event
                                that.hideFrame = true;
                            }
                        }

                        if (item.is('input') || item.is('button')) {
                            // we need to use native `.click()` event specifically
                            // as we are inside an iframe and magic is happening
                            item[0].click();
                        }

                    });
                    el.wrap(group);

                    // append element
                    render.append(el.parent());
                });

                // manually add cancel button at the end
                cancel.on(that.click, function (e) {
                    e.preventDefault();
                    that.options.onClose = false;
                    that.close();
                });
                cancel.wrap(group);
                render.append(cancel.parent());

                // prepare groups
                render.find('.cms-btn-group').unwrap();
                tmp = render.find('.cms-btn-group').clone(true, true);
                render.find('.cms-btn-group').remove();
                render.append(tmp.wrapAll(group.clone().addClass('cms-modal-item-buttons-left')).parent());

                // render buttons
                this.ui.modalButtons.html(render);
            },

            /**
             * Version where the modal loads an iframe.
             *
             * @method _loadIframe
             * @private
             * @param {Object} opts
             * @param {String} opts.url url to render iframe, takes presedence over opts.html
             * @param {Object[]} [opts.breadcrumbs] collection of breadcrumb items
             * @param {String} [opts.title] modal window main title (bold)
             */
            _loadIframe: function _loadIframe(opts) {
                var that = this;

                opts.url = this.makeURL(opts.url);
                opts.title = opts.title || '';
                opts.breadcrumbs = opts.breadcrumbs || '';

                // show loader
                CMS.API.Toolbar.showLoader();

                // set classes
                this.ui.modal.removeClass('cms-modal-markup');
                this.ui.modal.addClass('cms-modal-iframe');

                // we need to render the breadcrumb
                this._setBreadcrumb(opts.breadcrumbs);

                // now refresh the content
                var holder = this.ui.frame;
                var iframe = $('<iframe src="' + opts.url + '" class="" frameborder="0" />');

                // set correct title
                var titlePrefix = this.ui.titlePrefix;
                var titleSuffix = this.ui.titleSuffix;

                iframe.css('visibility', 'hidden');
                titlePrefix.text(opts.title || '');
                titleSuffix.text('');

                // ensure previous iframe is hidden
                holder.find('iframe').css('visibility', 'hidden');
                that.ui.modalBody.addClass('cms-loader');

                // attach load event for iframe to prevent flicker effects
                iframe.on('load', function () {
                    var messages;
                    var messageList;
                    var contents;
                    var body;
                    var innerTitle;
                    var bc;

                    // check if iframe can be accessed
                    try {
                        iframe.contents();
                    } catch (error) {
                        CMS.API.Messages.open({
                            message: '<strong>' + error + '</strong>',
                            error: true
                        });
                        that.close();
                    }

                    CMS.Modal._setupCtrlEnterSave(document);
                    CMS.Modal._setupCtrlEnterSave(iframe[0].contentWindow.document);
                    // for ckeditor we need to go deeper
                    if (iframe[0].contentWindow.CMS && iframe[0].contentWindow.CMS.CKEditor) {
                        $(iframe[0].contentWindow.document).ready(function () {
                            // setTimeout is required to battle CKEditor initialisation
                            setTimeout(function () {
                                var editor = iframe[0].contentWindow.CMS.CKEditor.editor;
                                if (editor) {
                                    editor.on('loaded', function (e) {
                                        CMS.Modal._setupCtrlEnterSave(
                                            $(e.editor.container.$).find('iframe')[0].contentWindow.document
                                        );
                                    });
                                }
                            }, 100);
                        });
                    }

                    // hide loader
                    CMS.API.Toolbar.hideLoader();

                    // show messages in toolbar if provided
                    messageList = iframe.contents().find('.messagelist');
                    messages = messageList.find('li');
                    if (messages.length) {
                        CMS.API.Messages.open({
                            message: messages.eq(0).html()
                        });
                    }
                    messageList.remove();
                    contents = iframe.contents();
                    body = contents.find('body');

                    // inject css class
                    body.addClass('cms-admin cms-admin-modal');

                    // determine if we should close the modal or reload
                    if (messages.length && that.enforceReload) {
                        that.reloadBrowser();
                    }
                    if (messages.length && that.enforceClose) {
                        that.close();
                        return false;
                    }

                    // adding django hacks
                    contents.find('.viewsitelink').attr('target', '_top');

                    // set modal buttons
                    that._setButtons($(this));

                    // when an error occurs, reset the saved status so the form can be checked and validated again
                    if (iframe.contents().find('.errornote').length || iframe.contents().find('.errorlist').length) {
                        that.saved = false;
                    }

                    // when the window has been changed pressing the blue or red button, we need to run a reload check
                    // also check that no delete-confirmation is required
                    if (that.saved && !contents.find('.delete-confirmation').length) {
                        that.reloadBrowser(
                            that.options.onClose ? that.options.onClose : window.location.href,
                            false,
                            true
                        );
                    } else {
                        iframe.show();
                        // set title of not provided
                        innerTitle = iframe.contents().find('#content h1:eq(0)');

                        // case when there is no prefix
                        if (opts.title === undefined && that.ui.titlePrefix.text() === '') {
                            bc = iframe.contents().find('.breadcrumbs').contents();
                            that.ui.titlePrefix.text(bc.eq(bc.length - 1).text().replace('›', '').trim());
                        }

                        if (titlePrefix.text().trim() === '') {
                            titlePrefix.text(innerTitle.text());
                        } else {
                            titleSuffix.text(innerTitle.text());
                        }
                        innerTitle.remove();

                        // than show
                        iframe.css('visibility', 'visible');

                        // append ready state
                        iframe.data('ready', true);

                        // attach close event
                        body.on('keydown.cms', function (e) {
                            if (e.keyCode === CMS.KEYS.ESC) {
                                that.close();
                            }
                        });

                        // figure out if .object-tools is available
                        if (contents.find('.object-tools').length) {
                            contents.find('#content').css('padding-top', 38);
                        }
                    }
                });

                // inject
                holder.html(iframe);
            },

            /**
             * Version where the modal loads an url within an iframe.
             *
             * @method _changeIframe
             * @private
             * @param {jQuery} el originated element
             */
            _changeIframe: function _changeIframe(el) {
                if (el.hasClass('active')) {
                    return false;
                }

                var parents = el.parent().find('a');
                parents.removeClass('active');

                el.addClass('active');

                this._loadIframe({
                    url: el.attr('href')
                });

                this.ui.titlePrefix.text(el.text());
            },

            /**
             * Version where the modal loads html markup.
             *
             * @method _loadMarkup
             * @private
             * @param {Object} opts
             * @param {String|HTMLNode|jQuery} opts.html html markup to render
             * @param {String} opts.title modal window main title (bold)
             * @param {String} [opts.subtitle] modal window secondary title (normal)
             */
            _loadMarkup: function _loadMarkup(opts) {
                this.ui.modal.removeClass('cms-modal-iframe');
                this.ui.modal.addClass('cms-modal-markup');
                this.ui.modalBody.removeClass('cms-loader');

                // set content
                // empty to remove events, append to keep events
                this.ui.frame.empty().append(opts.html);
                this.ui.titlePrefix.text(opts.title || '');
                this.ui.titleSuffix.text(opts.subtitle || '');
            },

            /**
             * _deletePlugin removes a plugin once created when clicking
             * on delete or the close item. If we don't do this, an empty
             * plugin is generated
             * https://github.com/divio/django-cms/pull/4381 will eventually
             * provide a better solution
             *
             * @method _deletePlugin
             * @private
             * @param {Object} [opts] general objects element that holds settings
             * @param {Boolean} [opts.hideAfter] hides the modal after the ajax requests succeeds
             */
            _deletePlugin: function _deletePlugin(opts) {
                var that = this;
                var data = CMS._newPlugin;
                var post = '{ "csrfmiddlewaretoken": "' + CMS.config.csrf + '" }';
                var text = CMS.config.lang.confirmEmpty.replace(
                    '{1}', CMS._newPlugin.breadcrumb[CMS._newPlugin.breadcrumb.length - 1].title
                );

                // trigger an ajax request
                return CMS.API.Toolbar.openAjax({
                    url: data['delete'],
                    post: post,
                    text: text,
                    callback: function () {
                        CMS._newPlugin = false;
                        if (opts && opts.hideAfter) {
                            that._hide({
                                duration: 100
                            });
                        }
                    }
                });
            }
        });

        /**
         * Sets up keyup/keydown listeners so you're able to save whatever you're
         * editing inside of an iframe by pressing `ctrl + enter` on windows and `cmd + enter` on mac.
         *
         * It only works with default button (e.g. action), not the `delete` button,
         * even though sometimes it's the only actionable button in the modal.
         *
         * @method _setupCtrlEnterSave
         * @private
         * @static
         * @param {HTMLElement} document document element (iframe or parent window);
         */
        CMS.Modal._setupCtrlEnterSave = function _setupCtrlEnterSave(doc) {
            var cmdPressed = false;
            var mac = (navigator.platform.toLowerCase().indexOf('mac') + 1);

            $(doc).on('keydown.cms.submit', function (e) {
                if (e.ctrlKey && e.keyCode === CMS.KEYS.ENTER && !mac) {
                    $('.cms-modal-buttons .cms-btn-action:first').trigger('click');
                }

                if (mac) {
                    if (e.keyCode === CMS.KEYS.CMD_LEFT ||
                        e.keyCode === CMS.KEYS.CMD_RIGHT ||
                        e.keyCode === CMS.KEYS.CMD_FIREFOX) {
                        cmdPressed = true;
                    }

                    if (e.keyCode === CMS.KEYS.ENTER && cmdPressed) {
                        $('.cms-modal-buttons .cms-btn-action:first').trigger('click');
                    }
                }
            }).on('keyup.cms.submit', function (e) {
                if (mac) {
                    if (e.keyCode === CMS.KEYS.CMD_LEFT || e.keyCode === CMS.KEYS.CMD_RIGHT) {
                        cmdPressed = false;
                    }
                }
            });

        };
    });

})(CMS.$);

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
                newPlugin: false
            },

            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;
                this.settings = CMS.settings;

                // elements
                this._setupUI();

                // states and events
                this.click = 'click.cms.modal';
                this.pointerDown = 'pointerdown.cms.modal contextmenu.cms.modal';
                this.pointerUp = 'pointerup.cms.modal pointercancel.cms.modal';
                this.pointerMove = 'pointermove.cms.modal';
                this.doubleClick = 'dblclick.cms.modal';
                this.maximized = false;
                this.minimized = false;
                this.triggerMaximized = false;
                this.saved = false;

                // if the modal is initialized the first time, set the events
                if (!this.ui.modal.data('ready')) {
                    this._events();
                }

                // set a state to determine if we need to reinitialize this._events();
                this.ui.modal.data('ready', true);
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
                this.ui.minimizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that.minimize();
                });
                this.ui.maximizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that.maximize();
                });

                this.ui.title.on(this.pointerDown, function (e) {
                    e.preventDefault();
                    that._startMove(e);
                });
                this.ui.title.on(this.doubleClick, function () {
                    that.maximize();
                });

                this.ui.resize.on(this.pointerDown, function (e) {
                    e.preventDefault();
                    that._startResize(e);
                });

                // elements within the window
                this.ui.breadcrumb.on(this.click, 'a', function (e) {
                    e.preventDefault();
                    that._changeIframe($(this));
                });

                this.ui.closeAndCancel.on(this.click, function (e) {
                    that.options.onClose = null;
                    e.preventDefault();
                    that.close();
                });
            },

            /**
             * Opens the modal either in an iframe or renders markup.
             *
             * @method open
             * @param opts either `opts.url` or `opts.html` are required
             * @param [opts.breadcrumbs] {Object[]} collection of breadcrumb items
             * @param [opts.html] {String|HTMLNode|jQuery} html markup to render
             * @param [opts.title] {String} modal window main title (bold)
             * @param [opts.subtitle] {String} modal window secondary title (normal)
             * @param [opts.url] {String} url to render iframe, takes precedence over `opts.html`
             * @param [opts.width] {Number} sets the width of the modal
             * @param [opts.height] {Number} sets the height of the modal
             */
            open: function open(opts) {
                // setup internals
                if (!(opts && opts.url || opts && opts.html)) {
                    throw new Error('The arguments passed to "open" were invalid.');
                }

                // cancel if another lightbox is already being opened
                if (CMS.API.locked) {
                    CMS.API.locked = false;
                    return false;
                } else {
                    CMS.API.locked = true;
                }

                // handle remove option when plugin is new
                if (CMS._newPlugin) {
                    if (this._deletePlugin() === false) {
                        // cancel open process when switching context
                        return false;
                    }
                }

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

                // show loader
                CMS.API.Toolbar._loader(true);

                // hide tooltip
                this.hideTooltip();

                // lets set the modal width and height to the size of the browser
                var widthOffset = 300; // adds margin left and right
                var heightOffset = 300; // adds margin top and bottom;
                var screenWidth = this.ui.window.width();
                var screenHeight = this.ui.window.height();
                // screen width and height calculation, WC = width
                var screenWidthCalc = screenWidth >= (this.options.minWidth + widthOffset);
                var screenHeightCalc = screenHeight >= (this.options.minHeight + heightOffset);

                var width = screenWidthCalc ? screenWidth - widthOffset : this.options.minWidth;
                var height = screenHeightCalc ? screenHeight - heightOffset : this.options.minHeight;

                this.ui.maximizeButton.removeClass('cms-modal-maximize-active');
                this.maximized = false;

                // in case, the modal is larger than the window, we trigger fullscreen mode
                if (height >= screenHeight) {
                    this.triggerMaximized = true;
                }

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

                // display modal
                this._show({
                    width: opts.width || width,
                    height: opts.height || height,
                    duration: this.options.modalDuration
                });
            },

            /**
             * Animation helper for opening the sideframe.
             *
             * @method _show
             * @private
             * @param opts
             * @param opts.width {Number} width of the modal
             * @param opts.height {Number} height of the modal
             * @param opts.duration {Number} speed of opening, ms (not really used yet)
             */
            _show: function _show(opts) {
                // we need to position the modal in the center
                var that = this;
                var width = opts.width;
                var height = opts.height;
                // TODO make use of transitionDuration
                var speed = opts.duration;

                this.ui.modal.css({
                    'display': 'block',
                    'width': width,
                    'height': height,
                    // TODO animate translateX if possible instead of margin
                    'margin-left': -(width / 2),
                    'margin-top': -(height / 2)
                });
                // setImmediate is required to go into the next frame
                setTimeout(function () {
                    that.ui.modal.addClass('cms-modal-open');
                }, 0);

                this.ui.modal.one('cmsTransitionEnd', function () {
                    that.ui.modal.css({
                        'margin-left': -(width / 2),
                        'margin-top': -(height / 2)
                    });

                    // hide loader
                    CMS.API.Toolbar._loader(false);

                    // check if we should maximize
                    if (that.triggerMaximized) {
                        that.maximize();
                    }

                    // changed locked status to allow other modals again
                    CMS.API.locked = false;
                }).emulateTransitionEnd(speed);

                // add esc close event
                this.ui.body.on('keydown.cms', function (e) {
                    if (e.keyCode === CMS.KEYS.ESC) {
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
                var that = this;

                // handle remove option when plugin is new
                if (CMS._newPlugin) {
                    this._deletePlugin({ hideAfter: true });
                } else {
                    this._hide({
                        duration: 100
                    });
                }

                // handle refresh option
                if (this.options.onClose) {
                    this.reloadBrowser(this.options.onClose, false, true);
                }

                // reset maximize or minimize states for #3111
                setTimeout(function () {
                    if (that.minimized) {
                        that.minimize();
                    }
                    if (that.maximized) {
                        that.maximize();
                    }
                }, this.options.duration);

                this.ui.modal.trigger('cms.modal.closed');
            },

            /**
             * Animation helper for closing the iframe.
             *
             * @method _hide
             * @private
             * @param opts
             * @param [opts.duration=this.options.modalDuration] {Number} animation duration
             */
            _hide: function _hide(opts) {
                var that = this;
                var duration = this.options.modalDuration;

                if (opts && opts.duration) {
                    duration = opts.duration;
                }

                that.ui.modal.removeClass('cms-modal-open');

                that.ui.modal.one('cmsTransitionEnd', function () {
                    that.ui.modal.css('display', 'none');
                }).emulateTransitionEnd(duration);

                that.ui.frame.empty();
                that.ui.modalBody.removeClass('cms-loader');
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
                    CMS.API.Toolbar.toggleToolbar(true);

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
                    // minimize
                    this.ui.body.removeClass('cms-modal-minimized');

                    // reattach css
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
                var container = this.ui.modal;

                // cancel action when minimized
                if (this.minimized) {
                    return false;
                }

                if (this.maximized === false) {
                    // maximize
                    this.maximized = true;

                    container.data('css', this.ui.modal.css([
                        'left', 'top', 'margin-left', 'margin-top',
                        'width', 'height'
                    ]));

                    this.ui.body.addClass('cms-modal-maximized');
                } else {
                    // restore
                    this.maximized = false;
                    this.ui.body.removeClass('cms-modal-maximized');

                    // reattach css
                    container.css(container.data('css'));
                }
            },

            /**
             * Initiates the start move event from `_events`.
             *
             * @method _startMove
             * @private
             * @param pointerEvent {Object} passes starting event
             */
            _startMove: function _startMove(pointerEvent) {
                // cancel if maximized
                if (this.maximized) {
                    return false;
                }
                // cancel action when minimized
                if (this.minimized) {
                    return false;
                }

                var that = this;
                var position = that.ui.modal.position();

                // create event for stopping
                this.ui.body.on(this.pointerUp, function (e) {
                    that._stopMove(e);
                });

                this.ui.shim.show();

                this.ui.body.attr('data-touch-action', 'none').on(this.pointerMove, function (e) {
                    var left = position.left - (pointerEvent.originalEvent.pageX - e.originalEvent.pageX);
                    var top = position.top - (pointerEvent.originalEvent.pageY - e.originalEvent.pageY);

                    that.ui.modal.css({
                        'left': left,
                        'top': top
                    });
                });
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
             * @param pointerEvent {Object} passes starting event
             */
            _startResize: function _startResize(pointerEvent) {
                // cancel if in fullscreen
                if (this.maximized) {
                    return false;
                }
                // continue
                var that = this;
                var container = this.ui.modal;
                var width = container.width();
                var height = container.height();
                var modalLeft = this.ui.modal.position().left;
                var modalTop = this.ui.modal.position().top;

                // create event for stopping
                this.ui.body.on(this.pointerUp, function (e) {
                    that._stopResize(e);
                });

                this.ui.shim.show();

                this.ui.body.attr('data-touch-action', 'none').on(this.pointerMove, function (e) {
                    var mvX = pointerEvent.originalEvent.pageX - e.originalEvent.pageX;
                    var mvY = pointerEvent.originalEvent.pageY - e.originalEvent.pageY;

                    var w = width - (mvX * 2);
                    var h = height - (mvY * 2);
                    var wMax = 680;
                    var hMax = 150;

                    // add some limits
                    if (w <= wMax || h <= hMax) {
                        return false;
                    }

                    // set centered animation
                    container.css({
                        'width': width - (mvX * 2),
                        'height': height - (mvY * 2),
                        'left': modalLeft + mvX,
                        'top': modalTop + mvY
                    });
                });
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
             * @param breadcrumbs {Object[]} renderes breadcrumb on modal
             */
            _setBreadcrumb: function _setBreadcrumb(breadcrumbs) {
                var bread = this.ui.breadcrumb;
                var crumb = '';

                // remove class from modal when no breadcrumbs is rendered
                if (!this.ui.breadcrumb.find('a').length) {
                    this.ui.modal.removeClass('cms-modal-has-breadcrumb');
                }

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
                    crumb += '<a href="' + item.url + '" class="' + last + '"><span>' + item.title + '</span></a>';
                });

                // attach elements
                this.ui.breadcrumb.html(crumb);

                // show breadcrumbs
                bread.show();
            },

            /**
             * Sets the buttons inside the modal.
             *
             * @method _setButtons
             * @private
             * @param iframe {jQuery} loaded iframe element
             */
            _setButtons: function _setButtons(iframe) {
                var djangoSuit = iframe.contents().find('.suit-columns').length > 0;
                var that = this;
                var group = $('<div class="cms-modal-item-buttons"></div>');
                var render = $('<div class="cms-modal-buttons-inner"></div>');
                var row;
                var tmp;
                if (!djangoSuit) {
                    row = iframe.contents().find('.submit-row:eq(0)');
                } else {
                    row = iframe.contents().find('.save-box:eq(0)');
                }
                var buttons = row.find('input, a, button');

                // hide all submit-rows
                iframe.contents().find('.submit-row').hide();

                // if there are no given buttons within the submit-row area
                // scan deeper within the form itself
                if (!buttons.length) {
                    row = iframe.contents().find('body:not(.change-list) #content form:eq(0)');
                    buttons = row.find('input[type="submit"], button[type="submit"]');
                    buttons.addClass('deletelink').hide();
                }
                // attach relation id
                buttons.each(function (index, item) {
                    $(item).attr('data-rel', '_' + index);
                });

                // loop over input buttons
                buttons.each(function (index, item) {
                    item = $(item);

                    // cancel if item is a hidden input
                    if (item.attr('type') === 'hidden') {
                        return false;
                    }

                    // create helper variables
                    var title = item.attr('value') || item.text();
                    var cls = 'cms-btn';

                    // set additional special css classes
                    if (item.hasClass('default')) {
                        cls = 'cms-btn cms-btn-action';
                    }
                    if (item.hasClass('deletelink')) {
                        cls = 'cms-btn cms-btn-caution';
                    }

                    // create the element and attach events
                    var el = $('<a href="#" class="' + cls + ' ' + item.attr('class') + '">' + title + '</a>');
                    el.on(that.click, function () {
                        if (item.is('input') || item.is('button')) {
                            item[0].click();
                        }
                        if (item.is('a')) {
                            that._loadIframe({
                                url: item.prop('href'),
                                name: title
                            });
                        }

                        // trigger only when blue action buttons are triggered
                        if (item.hasClass('default') || item.hasClass('deletelink')) {
                            // reset onClose when delete is triggered
                            if (item.hasClass('deletelink')) {
                                that.options.onClose = null;
                            }
                            // hide iframe
                            that.ui.frame.find('iframe').hide();
                            // page has been saved or deleted, run checkup
                            that.saved = true;
                        }
                    });
                    el.wrap(group);

                    // append element
                    render.append(el.parent());
                });

                // manually add cancel button at the end
                var cancel = $('<a href="#" class="cms-btn">' + that.config.lang.cancel + '</a>');
                cancel.on(that.click, function () {
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
             * Sanitise the ampersand within the url for #3404.
             *
             * @method _prepareUrl
             * @private
             * @param url {String}
             */
            _prepareUrl: function _prepareUrl(url) {
                // FIXME: A better fix is needed for '&' being interpreted as the
                url = url.replace('&', '&amp;');
                return url;
            },

            /**
             * Version where the modal loads an iframe.
             *
             * @method _loadIframe
             * @param opts
             * @param opts.url {String} url to render iframe, takes presedence over opts.html
             * @param [opts.breadcrumbs] {Object[]} collection of breadcrumb items
             * @param [opts.title] {String} modal window main title (bold)
             */
            _loadIframe: function _loadIframe(opts) {
                var that = this;

                opts.url = this._prepareUrl(opts.url);
                opts.title = opts.title || '';
                opts.breadcrumbs = opts.breadcrumbs || '';

                // set classes
                this.ui.modal.removeClass('cms-modal-markup');
                this.ui.modal.addClass('cms-modal-iframe');

                // we need to render the breadcrumb
                this._setBreadcrumb(opts.breadcrumbs);

                // now refresh the content
                var iframe = $('<iframe src="' + opts.url + '" class="" frameborder="0" />');
                iframe.css('visibility', 'hidden');
                var holder = this.ui.frame;

                // set correct title
                var titlePrefix = this.ui.titlePrefix;
                var titleSuffix = this.ui.titleSuffix;
                titlePrefix.text(opts.title || '');
                titleSuffix.text('');

                // ensure previous iframe is hidden
                holder.find('iframe').css('visibility', 'hidden');
                that.ui.modalBody.addClass('cms-loader');

                // attach load event for iframe to prevent flicker effects
                iframe.on('load', function () {
                    // check if iframe can be accessed
                    try {
                        iframe.contents();
                    } catch (error) {
                        CMS.API.Toolbar.showError('<strong>' + error + '</strong>');
                        that.close();
                    }

                    // show messages in toolbar if provided
                    var messages = iframe.contents().find('.messagelist li');
                    if (messages.length) {
                        CMS.API.Toolbar.openMessage(messages.eq(0).text());
                    }
                    messages.remove();
                    var contents = iframe.contents();
                    var body = contents.find('body');

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
                        that.reloadBrowser(window.location.href, false, true);
                    } else {
                        iframe.show();
                        // set title of not provided
                        var innerTitle = iframe.contents().find('#content h1:eq(0)');

                        // case when there is no prefix
                        if (opts.title === undefined && that.ui.titlePrefix.text() === '') {
                            var bc = iframe.contents().find('.breadcrumbs').contents();
                            that.ui.titlePrefix.text(bc.eq(bc.length - 1).text().replace('›', '').trim());
                        }

                        titleSuffix.text(innerTitle.text());
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

                this.ui.modal.trigger('cms.modal.loaded');
            },

            /**
             * Version where the modal loads an url within an iframe.
             *
             * @method _changeIframe
             * @private
             * @param el {jQuery} originated element
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

                // update title
                this.ui.titlePrefix.text(el.text());
            },

            /**
             * Version where the modal loads html markup.
             *
             * @method _loadMarkup
             * @param opts
             * @param opts.html {String|HTMLNode|jQuery} html markup to render
             * @param opts.title {String} modal window main title (bold)
             * @param [opts.subtitle] {String} modal window secondary title (normal)
             */
            _loadMarkup: function _loadMarkup(opts) {
                this.ui.modal.removeClass('cms-modal-iframe');
                this.ui.modal.addClass('cms-modal-markup');

                // set content
                this.ui.frame.html(opts.html);
                this.ui.titlePrefix.text(opts.title);
                this.ui.titleSuffix.text(opts.subtitle || '');

                this.ui.modal.trigger('cms.modal.loaded');
            },

            /**
             * _deletePlugin removes a plugin once created when clicking
             * on delete or the close item. If we don't do this, an empty
             * plugin is generated
             * https://github.com/divio/django-cms/pull/4381 will eventually
             * provide a better solution
             *
             * @param [opts] {Object} general objects element that holds settings
             * @param [opts.hideAfter] {Object} hides the modal after the ajax requests succeeds
             */
            _deletePlugin: function _deletePlugin(opts) {
                var that = this;
                var data = CMS._newPlugin;
                var post = '{ "csrfmiddlewaretoken": "' + this.config.csrf + '" }';
                var text = this.config.lang.confirmEmpty.replace(
                    '{1}', CMS._newPlugin.breadcrumb[0].title
                );

                // trigger an ajax request
                return CMS.API.Toolbar.openAjax(data['delete'], post, text, function () {
                    CMS._newPlugin = false;
                    if (opts && opts.hideAfter) {
                        that._hide({
                            duration: 100
                        });
                    }
                });
            }
        });

    });
})(CMS.$);

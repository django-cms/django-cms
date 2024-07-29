/*
 * Copyright https://github.com/divio/django-cms
 */

import ChangeTracker from './cms.changetracker';
import keyboard from './keyboard';

import $ from 'jquery';
import './jquery.transition';
import './jquery.trap';

import { Helpers, KEYS } from './cms.base';
import { showLoader, hideLoader } from './loader';

var previousKeyboardContext;
var previouslyFocusedElement;

/**
 * The modal is triggered via API calls from the backend either
 * through the toolbar navigation or from plugins. The APIs allow to
 * open content from a url (iframe) or inject html directly.
 *
 * @class Modal
 * @namespace CMS
 */
class Modal {
    constructor(options) {
        this.options = $.extend(true, {}, Modal.options, options);

        // elements
        this._setupUI();

        // states and events
        this.click = 'click.cms.modal';
        this.pointerDown = 'pointerdown.cms.modal contextmenu.cms.modal';
        this.pointerUp = 'pointerup.cms.modal pointercancel.cms.modal';
        this.pointerMove = 'pointermove.cms.modal';
        this.doubleClick = 'dblclick.cms.modal';
        this.touchEnd = 'touchend.cms.modal';
        this.keyUp = 'keyup.cms.modal';
        this.maximized = false;
        this.minimized = false;
        this.triggerMaximized = false;
        this.saved = false;

        this._beforeUnloadHandler = this._beforeUnloadHandler.bind(this);
    }

    /**
     * Stores all jQuery references within `this.ui`.
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
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
    }

    /**
     * Sets up all the event handlers, such as maximize/minimize and resizing.
     *
     * @method _events
     * @private
     */
    _events() {
        var that = this;

        // modal behaviours
        this.ui.minimizeButton
            .off(this.click + ' ' + this.touchEnd + ' ' + this.keyUp)
            .on(this.click + ' ' + this.touchEnd + ' ' + this.keyUp, function(e) {
                if (e.type !== 'keyup' || (e.type === 'keyup' && e.keyCode === KEYS.ENTER)) {
                    e.preventDefault();
                    that.minimize();
                }
            });
        this.ui.maximizeButton
            .off(this.click + ' ' + this.touchEnd + ' ' + this.keyUp)
            .on(this.click + ' ' + this.touchEnd + ' ' + this.keyUp, function(e) {
                if (e.type !== 'keyup' || (e.type === 'keyup' && e.keyCode === KEYS.ENTER)) {
                    e.preventDefault();
                    that.maximize();
                }
            });

        this.ui.title.off(this.pointerDown).on(this.pointerDown, function(e) {
            e.preventDefault();
            that._startMove(e);
        });
        this.ui.title.off(this.doubleClick).on(this.doubleClick, function() {
            that.maximize();
        });

        this.ui.resize.off(this.pointerDown).on(this.pointerDown, function(e) {
            e.preventDefault();
            that._startResize(e);
        });

        this.ui.closeAndCancel
            .off(this.click + ' ' + this.touchEnd + ' ' + this.keyUp)
            .on(this.click + ' ' + this.touchEnd + ' ' + this.keyUp, function(e) {
                if (e.type !== 'keyup' || (e.type === 'keyup' && e.keyCode === KEYS.ENTER)) {
                    e.preventDefault();
                    that._cancelHandler();
                }
            });

        // elements within the window
        this.ui.breadcrumb.off(this.click, 'a').on(this.click, 'a', function(e) {
            e.preventDefault();
            that._changeIframe($(this));
        });
    }

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
     * @returns {Class} this
     */
    open(opts) {
        // setup internals
        if (!((opts && opts.url) || (opts && opts.html))) {
            throw new Error('The arguments passed to "open" were invalid.');
        }

        // We have to rebind events every time we open a modal
        // because the event handlers contain references to the instance
        // and since we reuse the same markup we need to update
        // that instance reference every time.
        this._events();

        Helpers.dispatchEvent('modal-load', { instance: this });
        // // trigger the event also on the dom element,
        // // because if we load another modal while one is already open
        // // the older instance won't receive any updates
        // this.ui.modal.trigger('cms.modal.load');

        // common elements state
        this.ui.resize.toggle(this.options.resizable);
        this.ui.minimizeButton.toggle(this.options.minimizable);
        this.ui.maximizeButton.toggle(this.options.maximizable);

        var position = this._calculateNewPosition(opts);

        this.ui.maximizeButton.removeClass('cms-modal-maximize-active');
        this.maximized = false;

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

        Helpers.dispatchEvent('modal-loaded', { instance: this });

        var currentContext = keyboard.getContext();

        if (currentContext !== 'modal') {
            previousKeyboardContext = keyboard.getContext();
            previouslyFocusedElement = $(document.activeElement);
        }

        // display modal
        this._show(
            $.extend(
                {
                    duration: this.options.modalDuration
                },
                position
            )
        );

        keyboard.setContext('modal');
        this.ui.modal.trap();

        return this;
    }

    /**
     * Calculates coordinates and dimensions for modal placement
     *
     * @method _calculateNewPosition
     * @private
     * @param {Object} [opts]
     * @param {Number} [opts.width] desired width of the modal
     * @param {Number} [opts.height] desired height of the modal
     * @returns {Object}
     */
    // eslint-disable-next-line complexity
    _calculateNewPosition(opts) {
        // lets set the modal width and height to the size of the browser
        var widthOffset = 300; // adds margin left and right
        var heightOffset = 300; // adds margin top and bottom;
        var screenWidth = this.ui.window.width();
        var screenHeight = this.ui.window.height();
        var modalWidth = opts.width || this.options.minWidth;
        var modalHeight = opts.height || this.options.minHeight;
        // screen width and height calculation, WC = width
        var screenWidthCalc = screenWidth >= modalWidth + widthOffset;
        var screenHeightCalc = screenHeight >= modalHeight + heightOffset;

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

        currentTop = parseInt(currentTop, 10);
        currentLeft = parseInt(currentLeft, 10);

        // if new width/height go out of the screen - reset position to center of screen
        if (
            width / 2 + currentLeft > screenWidth ||
            height / 2 + currentTop > screenHeight ||
            currentLeft - width / 2 < 0 ||
            currentTop - height / 2 < 0
        ) {
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
    }

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
    _show(opts) {
        // we need to position the modal in the center
        var that = this;
        var width = opts.width;
        var height = opts.height;
        var speed = opts.duration;
        var top = opts.top;
        var left = opts.left;

        if (this.ui.modal.hasClass('cms-modal-open')) {
            this.ui.modal.addClass('cms-modal-morphing');
        }

        this.ui.modal.css({
            display: 'block',
            width: width,
            height: height,
            top: top,
            left: left,
            'margin-left': -(width / 2),
            'margin-top': -(height / 2)
        });
        // setImmediate is required to go into the next frame
        setTimeout(function() {
            that.ui.modal.addClass('cms-modal-open');
        }, 0);

        this.ui.modal
            .one('cmsTransitionEnd', function() {
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
                Helpers.dispatchEvent('modal-shown', { instance: that });
            })
            .emulateTransitionEnd(speed);

        // add esc close event
        this.ui.body.off('keydown.cms.close').on('keydown.cms.close', function(e) {
            if (e.keyCode === KEYS.ESC && that.options.closeOnEsc) {
                e.stopPropagation();
                if (that._confirmDirtyEscCancel()) {
                    that._cancelHandler();
                }
            }
        });

        // set focus to modal
        this.ui.modal.focus();
    }

    /**
     * Closes the current instance.
     *
     * @method close
     * @returns {Boolean|void}
     */
    close() {
        var event = Helpers.dispatchEvent('modal-close', { instance: this });

        if (event.isDefaultPrevented()) {
            return false;
        }

        Helpers._getWindow().removeEventListener('beforeunload', this._beforeUnloadHandler);

        // handle refresh option
        if (this.options.onClose) {
            Helpers.reloadBrowser(this.options.onClose, false);
        }

        this._hide({
            duration: this.options.modalDuration / 2
        });

        this.ui.modal.untrap();
        keyboard.setContext(previousKeyboardContext);
        try {
            previouslyFocusedElement.focus();
        } catch (e) {}
    }

    /**
     * Animation helper for closing the iframe.
     *
     * @method _hide
     * @private
     * @param {Object} opts
     * @param {Number} [opts.duration=this.options.modalDuration] animation duration
     */
    _hide(opts) {
        var that = this;
        var duration = this.options.modalDuration;

        if (opts && opts.duration) {
            duration = opts.duration;
        }

        this.ui.frame.empty();
        this.ui.modalBody.removeClass('cms-loader');
        this.ui.modal.removeClass('cms-modal-open');
        this.ui.modal
            .one('cmsTransitionEnd', function() {
                that.ui.modal.css('display', 'none');
            })
            .emulateTransitionEnd(duration);

        // reset maximize or minimize states for #3111
        setTimeout(function() {
            if (that.minimized) {
                that.minimize();
            }
            if (that.maximized) {
                that.maximize();
            }
            hideLoader();
            Helpers.dispatchEvent('modal-closed', { instance: that });
        }, this.options.duration);

        this.ui.body.off('keydown.cms.close');
    }

    /**
     * Minimizes the modal onto the toolbar.
     *
     * @method minimize
     * @returns {Boolean|void}
     */
    minimize() {
        var MINIMIZED_OFFSET = 50;

        // cancel action if maximized
        if (this.maximized) {
            return false;
        }

        if (this.minimized === false) {
            // save initial state
            this.ui.modal.data('css', this.ui.modal.css(['left', 'top', 'margin-left', 'margin-top']));

            // minimize
            this.ui.body.addClass('cms-modal-minimized');
            this.ui.modal.css({
                left: this.ui.toolbarLeftPart.outerWidth(true) + MINIMIZED_OFFSET
            });

            this.minimized = true;
        } else {
            // maximize
            this.ui.body.removeClass('cms-modal-minimized');
            this.ui.modal.css(this.ui.modal.data('css'));

            this.minimized = false;
        }
    }

    /**
     * Maximizes the window according to the browser size.
     *
     * @method maximize
     * @returns {Boolean|void}
     */
    maximize() {
        // cancel action when minimized
        if (this.minimized) {
            return false;
        }

        if (this.maximized === false) {
            // save initial state
            this.ui.modal.data(
                'css',
                this.ui.modal.css(['left', 'top', 'margin-left', 'margin-top', 'width', 'height'])
            );

            this.ui.body.addClass('cms-modal-maximized');

            this.maximized = true;
            Helpers.dispatchEvent('modal-maximized', { instance: this });
        } else {
            // minimize
            this.ui.body.removeClass('cms-modal-maximized');
            this.ui.modal.css(this.ui.modal.data('css'));

            this.maximized = false;
            Helpers.dispatchEvent('modal-restored', { instance: this });
        }
    }

    /**
     * Initiates the start move event from `_events`.
     *
     * @method _startMove
     * @private
     * @param {Object} pointerEvent passes starting event
     * @returns {Boolean|void}
     */
    _startMove(pointerEvent) {
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
        this.ui.body.on(this.pointerUp, function(e) {
            that._stopMove(e);
        });

        this.ui.body
            .on(this.pointerMove, function(e) {
                left = position.left - (pointerEvent.originalEvent.pageX - e.originalEvent.pageX);
                top = position.top - (pointerEvent.originalEvent.pageY - e.originalEvent.pageY);

                that.ui.modal.css({
                    left: left,
                    top: top
                });
            })
            .attr('data-touch-action', 'none');
    }

    /**
     * Initiates the stop move event from `_startMove`.
     *
     * @method _stopMove
     * @private
     */
    _stopMove() {
        this.ui.shim.hide();
        this.ui.body.off(this.pointerMove + ' ' + this.pointerUp).removeAttr('data-touch-action');
    }

    /**
     * Initiates the start resize event from `_events`.
     *
     * @method _startResize
     * @private
     * @param {Object} pointerEvent passes starting event
     * @returns {Boolean|void}
     */
    _startResize(pointerEvent) {
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
        var resizeDir = this.ui.resize.css('direction') === 'rtl' ? -1 : +1;

        // create event for stopping
        this.ui.body.on(this.pointerUp, function(e) {
            that._stopResize(e);
        });

        this.ui.shim.show();

        this.ui.body
            .on(this.pointerMove, function(e) {
                var mvX = pointerEvent.originalEvent.pageX - e.originalEvent.pageX;
                var mvY = pointerEvent.originalEvent.pageY - e.originalEvent.pageY;
                var w = width - resizeDir * mvX * 2;
                var h = height - mvY * 2;
                var wMin = that.options.minWidth;
                var hMin = that.options.minHeight;
                var left = resizeDir * mvX + modalLeft;
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
            })
            .attr('data-touch-action', 'none');
    }

    /**
     * Initiates the stop resize event from `_startResize`.
     *
     * @method _stopResize
     * @private
     */
    _stopResize() {
        this.ui.shim.hide();
        this.ui.body.off(this.pointerMove + ' ' + this.pointerUp).removeAttr('data-touch-action');
    }

    /**
     * Sets the breadcrumb inside the modal.
     *
     * @method _setBreadcrumb
     * @private
     * @param {Object[]} breadcrumbs renderes breadcrumb on modal
     * @returns {Boolean|void}
     */
    _setBreadcrumb(breadcrumbs) {
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
        $.each(breadcrumbs, function(index, item) {
            // check if the item is the last one
            var last = index >= breadcrumbs.length - 1 ? 'active' : '';

            // render breadcrumbs
            crumb += template.replace('{1}', item.url).replace('{2}', last).replace('{3}', item.title);
        });

        // attach elements
        this.ui.breadcrumb.html(crumb);
    }

    /**
     * Sets the buttons inside the modal.
     *
     * @method _setButtons
     * @private
     * @param {jQuery} iframe loaded iframe element
     */
    _setButtons(iframe) {
        var djangoSuit = iframe.contents().find('.suit-columns').length > 0;
        var that = this;
        var group = $('<div class="cms-modal-item-buttons"></div>');
        var render = $('<div class="cms-modal-buttons-inner"></div>');
        var cancel = $('<a href="#" class="cms-btn">' + CMS.config.lang.cancel + '</a>');
        var row;
        var tmp;

        // istanbul ignore if
        if (djangoSuit) {
            row = iframe.contents().find('.save-box:eq(0)');
        } else {
            row = iframe.contents().find('.submit-row:eq(0)');
        }
        var form = iframe.contents().find('form');

        // avoids conflict between the browser's form validation and Django's validation
        form.on('submit', function() {
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
        buttons.on('click', function() {
            if ($(this).hasClass('default')) {
                that.hideFrame = true;
            }
        });

        // hide all submit-rows
        iframe.contents().find('.submit-row').hide();

        // if there are no given buttons within the submit-row area
        // scan deeper within the form itself
        // istanbul ignore next
        if (!buttons.length) {
            row = iframe.contents().find('body:not(.change-list) #content form:eq(0)');
            buttons = row.find('input[type="submit"], button[type="submit"]');
            buttons.addClass('deletelink').hide();
        }

        // loop over input buttons
        buttons.each(function(index, btn) {
            var item = $(btn);

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

            // eslint-disable-next-line complexity
            el.on(that.click + ' ' + that.touchEnd, function(e) {
                e.preventDefault();

                if (item.is('a')) {
                    that._loadIframe({
                        url: Helpers.updateUrlWithPath(item.prop('href')),
                        name: title
                    });
                }

                // trigger only when blue action buttons are triggered
                if (item.hasClass('default') || item.hasClass('deletelink')) {
                    // hide iframe when using buttons other than submit
                    if (item.hasClass('default')) {
                        // submit button uses the form's submit event
                        that.hideFrame = true;
                    } else {
                        that.ui.modal.find('.cms-modal-frame iframe').hide();
                        // page has been saved or deleted, run checkup
                        that.saved = true;
                        if (item.hasClass('deletelink')) {
                            that.justDeleted = true;

                            var action = item.closest('form').prop('action');

                            // in case action is an input (see https://github.com/jquery/jquery/issues/3691)
                            // it's definitely not a plugin/placeholder deletion
                            if (typeof action === 'string' && action.match(/delete-plugin/)) {
                                that.justDeletedPlugin = /delete-plugin\/(\d+)\//gi.exec(action)[1];
                            }
                            if (typeof action === 'string' && action.match(/clear-placeholder/)) {
                                that.justDeletedPlaceholder = /clear-placeholder\/(\d+)\//gi.exec(action)[1];
                            }
                        }
                    }
                }

                if (item.is('input') || item.is('button')) {
                    that.ui.modalBody.addClass('cms-loader');
                    var frm = item.closest('form');

                    // In Firefox with 1Password extension installed (FF 45 1password 4.5.6 at least)
                    // the item[0].click() doesn't work, which notably breaks
                    // deletion of the plugin. Workaround is that if the clicked button
                    // is the only button in the form - submit a form, otherwise
                    // click on the button
                    if (frm.find('button, input[type="button"], input[type="submit"]').length > 1) {
                        // we need to use native `.click()` event specifically
                        // as we are inside an iframe and magic is happening
                        item[0].click();
                    } else {
                        // have to dispatch native submit event so all the submit handlers
                        // can be fired, see #5590
                        var evt = document.createEvent('HTMLEvents');

                        evt.initEvent('submit', false, true);
                        if (frm[0].dispatchEvent(evt)) {
                            // triggering submit event in webkit based browsers won't
                            // actually submit the form, while in Gecko-based ones it
                            // will and calling frm.submit() would throw NS_ERROR_UNEXPECTED
                            try {
                                frm[0].submit();
                            } catch (err) {}
                        }
                    }
                }
            });
            el.wrap(group);

            // append element
            render.append(el.parent());
        });

        // manually add cancel button at the end
        cancel.on(that.click, function(e) {
            e.preventDefault();
            that._cancelHandler();
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
    }

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
    _loadIframe(opts) {
        var that = this;
        const SHOW_LOADER_TIMEOUT = 500;

        opts.url = Helpers.makeURL(opts.url);
        opts.title = opts.title || '';
        opts.breadcrumbs = opts.breadcrumbs || '';

        showLoader();

        // set classes
        this.ui.modal.removeClass('cms-modal-markup');
        this.ui.modal.addClass('cms-modal-iframe');

        // we need to render the breadcrumb
        this._setBreadcrumb(opts.breadcrumbs);

        // now refresh the content
        var holder = this.ui.frame;
        var iframe = $('<iframe tabindex="0" src="' + opts.url + '" class="" frameborder="0" />');

        // set correct title
        var titlePrefix = this.ui.titlePrefix;
        var titleSuffix = this.ui.titleSuffix;

        iframe.css('visibility', 'hidden');
        titlePrefix.text(opts.title || '');
        titleSuffix.text('');

        // ensure previous iframe is hidden
        holder.find('iframe').css('visibility', 'hidden');
        const loaderTimeout = setTimeout(() => that.ui.modalBody.addClass('cms-loader'), SHOW_LOADER_TIMEOUT);

        // attach load event for iframe to prevent flicker effects
        // eslint-disable-next-line complexity
        iframe.on('load', function() {
            clearTimeout(loaderTimeout);
            var messages;
            var messageList;
            var contents;
            var body;
            var innerTitle;
            var bc;

            // check if iframe can be accessed
            try {
                contents = iframe.contents();
                body = contents.find('body');
            } catch (error) {
                CMS.API.Messages.open({
                    message: '<strong>' + CMS.config.lang.errorLoadingEditForm + '</strong>',
                    error: true,
                    delay: 0
                });
                that.close();
                return;
            }

            // check if we are redirected - should only happen after successful form submission
            var redirect = body.find('a.cms-view-new-object').attr('href');

            if (redirect) {
                Helpers.reloadBrowser(redirect, false);
                return true;
            }

            // tabindex is required for keyboard navigation
            // body.attr('tabindex', '0');
            iframe.on('focus', function() {
                if (this.contentWindow) {
                    this.contentWindow.focus();
                }
            });

            Modal._setupCtrlEnterSave(document);
            // istanbul ignore else
            if (iframe[0].contentWindow && iframe[0].contentWindow.document) {
                Modal._setupCtrlEnterSave(iframe[0].contentWindow.document);
            }
            // for ckeditor we need to go deeper
            // istanbul ignore next
            if (iframe[0].contentWindow && iframe[0].contentWindow.CMS && iframe[0].contentWindow.CMS.CKEditor) {
                $(iframe[0].contentWindow.document).ready(function() {
                    // setTimeout is required to battle CKEditor initialisation
                    setTimeout(function() {
                        var editor = iframe[0].contentWindow.CMS.CKEditor.editor;

                        if (editor) {
                            editor.on('instanceReady', function(e) {
                                Modal._setupCtrlEnterSave(
                                    $(e.editor.container.$).find('iframe')[0].contentWindow.document
                                );
                            });
                        }
                    }, 100); // eslint-disable-line
                });
            }

            var saveSuccess = Boolean(contents.find('.messagelist :not(".error")').length);

            // in case message didn't appear, assume that admin page is actually a success
            // istanbul ignore if
            if (!saveSuccess) {
                saveSuccess =
                    Boolean(contents.find('.dashboard #content-main').length) &&
                    !contents.find('.messagelist .error').length;
            }

            // show messages in toolbar if provided
            messageList = contents.find('.messagelist');
            messages = messageList.find('li');
            if (messages.length) {
                CMS.API.Messages.open({
                    message: messages.eq(0).html()
                });
            }
            messageList.remove();

            // inject css class
            body.addClass('cms-admin cms-admin-modal');

            // hide loaders
            that.ui.modalBody.removeClass('cms-loader');
            hideLoader();

            // determine if we should close the modal or reload
            if (messages.length && that.enforceReload) {
                that.ui.modalBody.addClass('cms-loader');
                showLoader();
                Helpers.reloadBrowser();
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
            if (
                contents.find('.errornote').length ||
                contents.find('.errorlist').length ||
                (that.saved && !saveSuccess)
            ) {
                that.saved = false;
            }

            // when the window has been changed pressing the blue or red button, we need to run a reload check
            // also check that no delete-confirmation is required
            if (that.saved && saveSuccess && !contents.find('.delete-confirmation').length) {
                that.ui.modalBody.addClass('cms-loader');
                if (that.options.onClose) {
                    showLoader();
                    Helpers.reloadBrowser(
                        that.options.onClose ? that.options.onClose : window.location.href,
                        false,
                        true
                    );
                } else {
                    setTimeout(function() {
                        if (that.justDeleted && (that.justDeletedPlugin || that.justDeletedPlaceholder)) {
                            CMS.API.StructureBoard.invalidateState(
                                that.justDeletedPlaceholder ? 'CLEAR_PLACEHOLDER' : 'DELETE',
                                {
                                    plugin_id: that.justDeletedPlugin,
                                    placeholder_id: that.justDeletedPlaceholder,
                                    deleted: true
                                }
                            );
                        }
                        // hello ckeditor
                        Helpers.removeEventListener('modal-close.text-plugin');
                        that.close();
                    // must be more than 100ms
                    }, 150); // eslint-disable-line
                }
            } else {
                iframe.show();
                // set title of not provided
                innerTitle = contents.find('#content h1:eq(0)');

                // case when there is no prefix
                // istanbul ignore next: never happens
                if (opts.title === undefined && that.ui.titlePrefix.text() === '') {
                    bc = contents.find('.breadcrumbs').contents();
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
                body.on('keydown.cms', function(e) {
                    if (e.keyCode === KEYS.ESC && that.options.closeOnEsc) {
                        e.stopPropagation();
                        if (that._confirmDirtyEscCancel()) {
                            that._cancelHandler();
                        }
                    }
                });

                // figure out if .object-tools is available
                if (contents.find('.object-tools').length) {
                    contents.find('#content').css('padding-top', 38); // eslint-disable-line
                }

                // this is required for IE11. we assume that when the modal is opened the user is going to interact
                // with it. if we don't focus the body directly the next time the user clicks on a field inside
                // the iframe the focus will be stolen by body thus requiring two clicks. this immediately focuses the
                // iframe body on load except if something is already focused there
                // (django tries to focus first field by default)
                setTimeout(() => {
                    if (!iframe[0] || !iframe[0].contentDocument || !iframe[0].contentDocument.documentElement) {
                        return;
                    }
                    if ($(iframe[0].contentDocument.documentElement).find(':focus').length) {
                        return;
                    }
                    iframe.trigger('focus');
                }, 0); // eslint-disable-line
            }

            that._attachContentPreservingHandlers(iframe);
        });

        // inject
        holder.html(iframe);
    }

    /**
     * Adds handlers to prevent accidental refresh / modal close
     * that could lead to loss of data.
     *
     * @method _attachContentPreservingHandlers
     * @private
     * @param {jQuery} iframe
     */
    _attachContentPreservingHandlers(iframe) {
        var that = this;

        that.tracker = new ChangeTracker(iframe);

        Helpers._getWindow().addEventListener('beforeunload', this._beforeUnloadHandler);
    }

    /**
     * @method _beforeUnloadHandler
     * @private
     * @param {Event} e
     * @returns {String|void}
     */
    _beforeUnloadHandler(e) {
        if (this.tracker.isFormChanged()) {
            e.returnValue = CMS.config.lang.confirmDirty;
            return e.returnValue;
        }
    }

    /**
     * Similar functionality as in `_attachContentPreservingHandlers` but for canceling
     * the modal with the ESC button.
     *
     * @method _confirmDirtyEscCancel
     * @private
     * @returns {Boolean}
     */
    _confirmDirtyEscCancel() {
        if (this.tracker && this.tracker.isFormChanged()) {
            return Helpers.secureConfirm(CMS.config.lang.confirmDirty + '\n\n' + CMS.config.lang.confirmDirtyESC);
        }
        return true;
    }

    /**
     * Version where the modal loads an url within an iframe.
     *
     * @method _changeIframe
     * @private
     * @param {jQuery} el originated element
     * @returns {Boolean|void}
     */
    _changeIframe(el) {
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
    }

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
    _loadMarkup(opts) {
        this.ui.modal.removeClass('cms-modal-iframe');
        this.ui.modal.addClass('cms-modal-markup');
        this.ui.modalBody.removeClass('cms-loader');

        // set content
        // empty to remove events, append to keep events
        this.ui.frame.empty().append(opts.html);
        this.ui.titlePrefix.text(opts.title || '');
        this.ui.titleSuffix.text(opts.subtitle || '');
    }

    /**
     * Called whenever default modal action is canceled.
     *
     * @method _cancelHandler
     * @private
     */
    _cancelHandler() {
        this.options.onClose = null;
        this.close();
    }

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
     * @param {HTMLElement} doc document element (iframe or parent window);
     */
    static _setupCtrlEnterSave(doc) {
        var cmdPressed = false;
        var mac = navigator.platform.toLowerCase().indexOf('mac') + 1;

        $(doc)
            .on('keydown.cms.submit', function(e) {
                if (e.ctrlKey && e.keyCode === KEYS.ENTER && !mac) {
                    $('.cms-modal-buttons .cms-btn-action:first').trigger('click');
                }

                if (mac) {
                    if (e.keyCode === KEYS.CMD_LEFT || e.keyCode === KEYS.CMD_RIGHT || e.keyCode === KEYS.CMD_FIREFOX) {
                        cmdPressed = true;
                    }

                    if (e.keyCode === KEYS.ENTER && cmdPressed) {
                        $('.cms-modal-buttons .cms-btn-action:first').trigger('click');
                    }
                }
            })
            .on('keyup.cms.submit', function(e) {
                if (mac) {
                    if (e.keyCode === KEYS.CMD_LEFT || e.keyCode === KEYS.CMD_RIGHT || e.keyCode === KEYS.CMD_FIREFOX) {
                        cmdPressed = false;
                    }
                }
            });
    }
}

Modal.options = {
    onClose: false,
    closeOnEsc: true,
    minHeight: 400,
    minWidth: 800,
    modalDuration: 200,
    resizable: true,
    maximizable: true,
    minimizable: true
};

export default Modal;

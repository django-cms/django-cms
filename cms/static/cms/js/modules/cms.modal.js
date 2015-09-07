//##################################################################################################################
// #MODAL#
/* global CMS */

(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(function () {
        /*!
         * Modal
         * Controls a cms specific modal
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

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;

                // elements
                this._setupUI();

                // states
                this.click = 'click.cms';
                this.maximized = false;
                this.minimized = false;
                this.triggerMaximized = false;
                this.saved = false;

                // if the modal is initialized the first time, set the events
                if (!this.ui.modal.data('ready')) {
                    this._events();
                }

                // ready modal
                this.ui.modal.data('ready', true);
            },

            _setupUI: function setupUI() {
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
                    iframeHolder: modal.find('.cms-modal-frame'),
                    shim: modal.find('.cms-modal-shim')
                };
            },

            // initial methods
            _events: function () {
                var that = this;

                // attach events to window
                this.ui.minimizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that._minimize();
                });
                this.ui.title.on('pointerdown.cms contextmenu.cms', function (e) {
                    e.preventDefault();
                    that._startMove(e);
                });
                this.ui.title.on('dblclick.cms', function () {
                    that._maximize();
                });
                this.ui.resize.on('pointerdown.cms contextmenu.cms', function (e) {
                    e.preventDefault();
                    that._startResize(e);
                });
                this.ui.maximizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that._maximize();
                });
                this.ui.breadcrumb.on(this.click, 'a', function (e) {
                    e.preventDefault();
                    that._changeContent($(this));
                });
                this.ui.closeAndCancel.on(this.click, function (e) {
                    that.options.onClose = null;
                    e.preventDefault();
                    that.close();
                });

                // stopper events
                this.ui.body.on('pointerup.cms pointercancel.cms', function (e) {
                    that._endMove(e);
                    that._endResize(e);
                });
            },

            // public methods
            open: function (url, name, breadcrumb) {
                // cancel if another lightbox is already being opened
                if (CMS.API.locked) {
                    CMS.API.locked = false;
                    return false;
                } else {
                    CMS.API.locked = true;
                }

                // because a new instance is called, we have to ensure minimized state is removed #3620
                if (this.ui.body.hasClass('cms-modal-minimized')) {
                    this.minimized = true;
                    this._minimize();
                }

                // show loader
                CMS.API.Toolbar._loader(true);

                // hide tooltip
                this.hideTooltip();

                this._loadContent(url, name);

                // lets set the modal width and height to the size of the browser
                var widthOffset = 300; // adds margin left and right
                var heightOffset = 350; // adds margin top and bottom;
                var screenWidth = this.ui.window.width();
                var screenHeight = this.ui.window.height();

                var width = (screenWidth >= this.options.minWidth + widthOffset) ?
                    screenWidth - widthOffset :
                    this.options.minWidth;
                var height = (screenHeight >= this.options.minHeight + heightOffset) ?
                    screenHeight - heightOffset :
                    this.options.minHeight;

                this.ui.maximizeButton.removeClass('cms-modal-maximize-active');
                this.maximized = false;

                // in case, the modal is larger than the window, we trigger fullscreen mode
                if (height >= screenHeight) {
                    this.triggerMaximized = true;
                }

                // we need to render the breadcrumb
                this._setBreadcrumb(breadcrumb);

                // display modal
                this._show({
                    width: width,
                    height: height,
                    duration: this.options.modalDuration
                });
            },

            close: function () {
                var that = this;
                // handle remove option when plugin is new
                if (this.options.newPlugin) {
                    var data = this.options.newPlugin;
                    var post = '{ "csrfmiddlewaretoken": "' + this.config.csrf + '" }';
                    var text = this.config.lang.confirm;

                    // trigger an ajax request
                    CMS.API.Toolbar.openAjax(data['delete'], post, text, function () {
                        that._hide(100);
                    });
                } else {
                    this._hide(100);
                }

                // handle refresh option
                if (this.options.onClose) {
                    this.reloadBrowser(this.options.onClose, false, true);
                }

                // reset maximize or minimize states for #3111
                setTimeout(function () {
                    if (that.minimized) {
                        that._minimize();
                    }
                    if (that.maximized) {
                        that._maximize();
                    }
                }, 300);
            },

            // private methods
            /**
             * _show animates the modal to given size
             *
             * @param opts
             * @param opts.width Number width of the modal
             * @param opts.height Number height of the modal
             * @param opts.duration Number speed of opening, ms (not really used yet)
             */
            _show: function (opts) {
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
                        that._maximize();
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

            _hide: function (duration) {
                var that = this;

                that.ui.modal.removeClass('cms-modal-open');

                that.ui.modal.one('cmsTransitionEnd', function () {
                    that.ui.modal.css('display', 'none');
                }).emulateTransitionEnd(duration);

                that.ui.iframeHolder.find('iframe').remove();
                that.ui.modalBody.removeClass('cms-loader');
            },

            _minimize: function () {
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

            _maximize: function () {
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

            _startMove: function (initial) {
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

                this.ui.shim.show();

                this.ui.body.attr('data-touch-action', 'none').on('pointermove.cms', function (e) {
                    var left = position.left - (initial.originalEvent.pageX - e.originalEvent.pageX);
                    var top = position.top - (initial.originalEvent.pageY - e.originalEvent.pageY);

                    that.ui.modal.css({
                        'left': left,
                        'top': top
                    });
                });
            },

            _endMove: function () {
                this.ui.shim.hide();

                this.ui.body.off('pointermove.cms').removeAttr('data-touch-action');
            },

            _startResize: function (initial) {
                // cancel if in fullscreen
                if (this.maximized) {
                    return false;
                }
                // continue
                var container = this.ui.modal;
                var width = container.width();
                var height = container.height();
                var modalLeft = this.ui.modal.position().left;
                var modalTop = this.ui.modal.position().top;

                this.ui.shim.show();

                this.ui.body.attr('data-touch-action', 'none').on('pointermove.cms', function (e) {
                    var mvX = initial.originalEvent.pageX - e.originalEvent.pageX;
                    var mvY = initial.originalEvent.pageY - e.originalEvent.pageY;

                    var w = width - (mvX * 2);
                    var h = height - (mvY * 2);
                    var wMax = 680;
                    var hMax = 100;

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

            _endResize: function () {
                this.ui.shim.hide();

                this.ui.body.off('pointermove.cms').removeAttr('data-touch-action');
            },

            _setBreadcrumb: function (breadcrumb) {
                var bread = this.ui.breadcrumb;
                var crumb = '';

                // remove class from modal
                this.ui.modal.removeClass('cms-modal-has-breadcrumb');

                // cancel if there is no breadcrumb)
                if (!breadcrumb || breadcrumb.length <= 0) {
                    return false;
                }
                if (!breadcrumb[0].title) {
                    return false;
                }

                // add class to modal
                this.ui.modal.addClass('cms-modal-has-breadcrumb');

                // load breadcrumb
                $.each(breadcrumb, function (index, item) {
                    // check if the item is the last one
                    var last = (index >= breadcrumb.length - 1) ? 'active' : '';
                    // render breadcrumb
                    crumb += '<a href="' + item.url + '" class="' + last + '"><span>' + item.title + '</span></a>';
                });

                // attach elements
                this.ui.breadcrumb.html(crumb);

                // show breadcrumb
                bread.show();
            },

            _setButtons: function (iframe) {
                var djangoSuit = iframe.contents().find('.suit-columns').length > 0;
                var that = this;
                var row;
                if (!djangoSuit) {
                    row = iframe.contents().find('.submit-row:eq(0)');
                } else {
                    row = iframe.contents().find('.save-box:eq(0)');
                }
                // hide all submit-rows
                iframe.contents().find('.submit-row').hide();
                var buttons = row.find('input, a, button');
                var render = $('<span />'); // seriously jquery...

                // if there are no given buttons within the submit-row area
                // scan deeper within the form itself
                if (!buttons.length) {
                    row = iframe.contents().find('body:not(.change-list) #content form:eq(0)');
                    buttons = row.find('input[type="submit"], button[type="submit"]');
                    buttons.addClass('deletelink')
                        .hide();
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
                    var el = $('' +
                        '<div class="cms-modal-item-buttons">' +
                        '   <a href="#" class="' + cls + ' ' + item.attr('class') + '">' + title + '</a>' +
                        '</div>');
                    el.on(that.click, function () {
                        if (item.is('input') || item.is('button')) {
                            item[0].click();
                        }
                        if (item.is('a')) {
                            that._loadContent(item.prop('href'), title);
                        }

                        // trigger only when blue action buttons are triggered
                        if (item.hasClass('default') || item.hasClass('deletelink')) {
                            that.options.newPlugin = null;
                            // reset onClose when delete is triggered
                            if (item.hasClass('deletelink')) {
                                that.options.onClose = null;
                            }
                            // hide iframe
                            that.ui.iframeHolder.find('iframe').hide();
                            // page has been saved or deleted, run checkup
                            that.saved = true;
                        }
                    });

                    // append element
                    render.append(el);
                });

                // manually add cancel button at the end
                var cancel = $('' +
                    '<div class="cms-modal-item-buttons">' +
                    '   <a href="#" class="cms-btn">' + that.config.lang.cancel + '</a>' +
                    '</div>');
                cancel.on(that.click, function () {
                    that.options.onClose = false;
                    that.close();
                });
                render.append(cancel);

                // render buttons
                this.ui.modalButtons.html(render);
            },

            /**
             * _prepareUrl adds `?modal=1` get param to the url, which is then got by the backend
             * and additional "modal" stylesheet is then inserted into a template that is loaded
             * inside of an iframe
             *
             * @param url String
             */
            _prepareUrl: function (url) {
                if (url.indexOf('?') === -1) {
                    url += '?modal=1';
                } else {
                    url += '&modal=1';
                }
                // FIXME: A better fix is needed for '&' being interpreted as the
                // start of en entity by jQuery. See #3404
                url = url.replace('&', '&amp;');
                return url;
            },

            _loadContent: function (url, name) {
                var that = this;
                url = this._prepareUrl(url);

                // now refresh the content
                var iframe = $('<iframe src="' + url + '" class="" frameborder="0" />');
                iframe.css('visibility', 'hidden');
                var holder = this.ui.iframeHolder;

                // set correct title
                var titlePrefix = this.ui.titlePrefix;
                var titleSuffix = this.ui.titleSuffix;
                titlePrefix.text(name || '');
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
                        if (name === undefined && that.ui.titlePrefix.text() === '') {
                            var bc = iframe.contents().find('.breadcrumbs').text().split('›');
                            console.log(bc);
                            that.ui.titlePrefix.text(bc[bc.length - 1]);
                        }

                        titleSuffix.text(innerTitle.text());
                        innerTitle.remove();

                        // than show
                        iframe.css('visibility', 'visible');

                        // append ready state
                        iframe.data('ready', true);

                        // attach close event
                        contents.find('body').on('keydown.cms', function (e) {
                            if (e.keyCode === CMS.KEYS.ESC) {
                                that.close();
                            }
                        });
                        contents.find('body').addClass('cms-modal-window');

                        // figure out if .object-tools is available
                        if (contents.find('.object-tools').length) {
                            contents.find('#content').css('padding-top', 38);
                        }
                    }
                });

                // inject
                holder.html(iframe);
            },

            _changeContent: function (el) {
                if (el.hasClass('active')) {
                    return false;
                }

                var parents = el.parent().find('a');
                parents.removeClass('active');

                el.addClass('active');

                this._loadContent(el.attr('href'));

                // update title
                this.ui.titlePrefix.text(el.text());
            }
        });

    });
})(CMS.$);

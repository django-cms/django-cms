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
                newPlugin: false,
                urls: {
                    //FIXME wtf, async request for css is bad for perceived performance
                    css_modal: 'cms/css/cms.toolbar.modal.css'
                }
            },

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);
                this.config = CMS.config;

                // elements
                this._setupUI();

                // states
                this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms click.cms';
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
                this.ui = {};
                this.ui.modal = $('.cms-modal');
                this.ui.body = $('html');
                this.ui.window = $(window);
                this.ui.toolbar = $('.cms-toolbar');

                this.ui.minimizeButton = this.ui.modal.find('.cms-modal-collapse');
                this.ui.maximizeButton = this.ui.modal.find('.cms-modal-maximize');
                this.ui.title = this.ui.modal.find('.cms-modal-title');
                this.ui.resize = this.ui.modal.find('.cms-modal-resize');
                this.ui.breadcrumb = this.ui.modal.find('.cms-modal-breadcrumb');
                this.ui.breadcrumbItems = this.ui.modal.find('.cms-modal-breadcrumb-items');
                this.ui.closeAndCancel = this.ui.modal.find('.cms-modal-close, .cms-modal-cancel');
                this.ui.modalButtons = this.ui.modal.find('.cms-modal-buttons');
                this.ui.modalContents = this.ui.modal.find('.cms-modal-body, .cms-modal-foot');
                this.ui.modalBody = this.ui.modal.find('.cms-modal-body');
                this.ui.iframeHolder = this.ui.modal.find('.cms-modal-frame');
                this.ui.shim = this.ui.modal.find('.cms-modal-shim');
            },

            // initial methods
            _events: function () {
                var that = this;

                // attach events to window
                this.ui.minimizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that._minimize();
                });
                this.ui.title.on('mousedown.cms', function (e) {
                    e.preventDefault();
                    that._startMove(e);
                });
                this.ui.title.on('dblclick.cms', function () {
                    that._maximize();
                });
                this.ui.resize.on('mousedown.cms', function (e) {
                    e.preventDefault();
                    that._startResize(e);
                });
                this.ui.maximizeButton.on(this.click, function (e) {
                    e.preventDefault();
                    that._maximize();
                });
                this.ui.breadcrumbItems.on(this.click, 'a', function (e) {
                    e.preventDefault();
                    that._changeContent($(this));
                });
                this.ui.closeAndCancel.on(this.click, function (e) {
                    that.options.onClose = null;
                    e.preventDefault();
                    that.close();
                });

                // stopper events
                this.ui.body.on('mouseup.cms', function (e) {
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
                if (this.ui.modal.is(':visible') && this.ui.modal.find('.cms-modal-collapsed').length) {
                    this.minimized = true;
                    this._minimize();
                }

                // show loader
                CMS.API.Toolbar._loader(true);

                // hide tooltip
                this.hideTooltip();

                // reset breadcrumb
                // this.ui.breadcrumb.hide();
                // this.ui.breadcrumbItems.html('');

                // empty buttons
                // this.ui.modalButtons.html('');

                // var contents = this.ui.modalContents;
                // contents.show();

                this._loadContent(url, name);

                // ensure modal is not maximized
                if (this.ui.modal.find('.cms-modal-collapsed').length) {
                    this._minimize();
                }

                // // reset styles
                // this.ui.modal.css({
                //     'left': '50%',
                //     'top': '50%',
                //     'mergin-left': 0,
                //     'margin-right': 0
                // });

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
                // this.ui.modalBody.css({
                //     'width': width,
                //     'height': height
                // });
                // this.ui.modalBody.removeClass('cms-loader');
                this.ui.maximizeButton.removeClass('cms-modal-maximize-active');
                this.maximized = false;
                // in case, the window is larger than the windows height, we trigger fullscreen mode
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
                // make use of transitionDuration
                var speed = opts.duration;

                // // animates and sets the modal
                // this.ui.modal.show().css({
                //     'width': 0,
                //     'height': 0,
                //     'margin-left': 0,
                //     'margin-top': 0
                // }).stop(true, true).animate({
                //     'width': width,
                //     'height': height,
                //     'margin-left': -(width / 2),
                //     'margin-top': -(height / 2)
                // }, speed, );
                this.ui.modal.css({
                    'display': 'block',
                    'width': width,
                    'height': height,
                    // FIXME animate translateX if possible instead of margin
                    'margin-left': -(width / 2),
                    'margin-top': -(height / 2)
                });
                // setImmediate is required to go into the next frame
                setTimeout(function () {
                    that.ui.modal.addClass('cms-modal-open');
                }, 0);

                //FIXME listen to the transitionEnd event
                setTimeout(function () {
                    $(this).removeAttr('style');

                    that.ui.modal.css({
                        'margin-left': -(width / 2),
                        'margin-top': -(height / 2)
                    });

                    // fade in modal window
                    // that.ui.modal.show();

                    // hide loader
                    CMS.API.Toolbar._loader(false);

                    // check if we should maximize
                    if (that.triggerMaximized) {
                        that._maximize();
                    }

                    // changed locked status to allow other modals again
                    CMS.API.locked = false;
                }, speed);

                // add esc close event
                this.ui.body.on('keydown.cms', function (e) {
                    if (e.keyCode === 27) {
                        that.close();
                    }
                });

                // set focus to modal
                this.ui.modal.focus();
            },

            _hide: function (duration) {
                var that = this;
                this.ui.modal.removeClass('cms-modal-open');
                //FIXME listen to transitionEnd event
                setTimeout(function () {
                    that.ui.modal.css('display', 'none');
                }, duration);
                this.ui.iframeHolder.find('iframe').remove();
                this.ui.modalBody.removeClass('cms-loader');
            },

            _minimize: function () {
                var trigger = this.ui.minimizeButton;
                var maximize = this.ui.maximizeButton;

                // cancel action if maximized
                if (this.maximized) {
                    return false;
                }

                if (this.minimized === false) {
                    // ensure toolbar is shown
                    CMS.API.Toolbar.toggleToolbar(true);

                    // save initial state
                    this.ui.modal.data('css', this.ui.modal.css([
                        'left', 'top', 'margin'
                    ]));

                    // minimize
                    trigger.addClass('cms-modal-collapsed');
                    this.ui.body.addClass('cms-modal-minimized');

                    // contents.hide();
                    this.ui.modal.css({
                        'left': this.ui.toolbar.find('.cms-toolbar-left').outerWidth(true) + 50,
                        'top': (this.config.debug) ? 6 : 1
                    });

                    // ensure maximize element is hidden #3111
                    maximize.hide();

                    this.minimized = true;
                } else {
                    // minimize
                    trigger.removeClass('cms-modal-collapsed');
                    this.ui.body.removeClass('cms-modal-minimized');
                    // contents.show();

                    // reattach css
                    this.ui.modal.css(this.ui.modal.data('css'));

                    // ensure maximize element is shown #3111
                    maximize.show();

                    this.minimized = false;
                }
            },

            _maximize: function () {
                var debug = (this.config.debug) ? 5 : 0; //FIXME incorrect
                var container = this.ui.modal;
                var minimize = this.ui.minimizeButton;
                var trigger = this.ui.maximizeButton;
                var title = this.ui.title;

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

                    trigger.addClass('cms-modal-maximize-active');
                    this.ui.body.addClass('cms-modal-maximized');

                    // container.data('css', {
                    //     'width': container.width(),
                    //     'height': container.height()
                    // });

                    // reset
                    container.css({
                        'left': 0,
                        'top': debug,
                        'margin': 0
                    });
                    // bind resize event
                    // FIXME: just add a class :/
                    // this.ui.window.on('resize.cms.modal', function () {
                    //     container.css({
                    //         width: that.ui.window.width(),
                    //         height: that.ui.window.height() - debug
                    //     });
                    // });
                    // this.ui.window.trigger('resize.cms.modal');

                    // ensure maximize element is hidden #3111
                    minimize.hide();
                    // set correct cursor when maximized #3111
                    title.css('cursor', 'default');
                } else {
                    // restore
                    this.maximized = false;
                    trigger.removeClass('cms-modal-maximize-active');
                    this.ui.body.removeClass('cms-modal-maximized');

                    // this.ui.window.off('resize.cms.modal');

                    // reattach css
                    container.css(container.data('css'));

                    // ensure maximize element is shown #3111
                    minimize.show();
                    // set correct cursor when maximized #3111
                    title.css('cursor', 'move');
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

                this.ui.body.on('mousemove.cms', function (e) {
                    var left = position.left - (initial.pageX - e.pageX);
                    var top = position.top - (initial.pageY - e.pageY);

                    that.ui.modal.css({
                        'left': left,
                        'top': top
                    });
                });
            },

            _endMove: function () {
                this.ui.shim.hide();

                this.ui.body.off('mousemove.cms');
            },

            _startResize: function (initial) {
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

                this.ui.shim.show();

                this.ui.body.on('mousemove.cms', function (e) {
                    var mvX = initial.pageX - e.pageX;
                    var mvY = initial.pageY - e.pageY;

                    var w = width - (mvX * 2);
                    var h = height - (mvY * 2);
                    var max = 680;

                    // add some limits
                    if (w <= max || h <= 100) {
                        return false;
                    }

                    // set centered animation
                    container.css({
                        'width': width - (mvX * 2),
                        'height': height - (mvY * 2)
                    });
                    that.ui.modal.css({
                        'left': modalLeft + mvX,
                        'top': modalTop + mvY
                    });
                });
            },

            _endResize: function () {
                this.ui.shim.hide();

                this.ui.body.off('mousemove.cms');
            },

            _setBreadcrumb: function (breadcrumb) {
                var bread = this.ui.breadcrumb;
                var crumb = '';

                // cancel if there is no breadcrumb)
                if (!breadcrumb || breadcrumb.length <= 0) {
                    return false;
                }
                if (!breadcrumb[0].title) {
                    return false;
                }

                // load breadcrumb
                $.each(breadcrumb, function (index, item) {
                    // check if the item is the last one
                    var last = (index >= breadcrumb.length - 1) ? 'cms-modal-breadcrumb-last' : '';
                    // render breadcrumb
                    crumb += '<a href="' + item.url + '" class="' + last + '"><span>' + item.title + '</span></a>';
                });

                // attach elements
                this.ui.breadcrumbItems.html(crumb);

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
                    var el = $('<div class="' + cls + ' ' + item.attr('class') + '">' + title + '</div>');
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
                var cancel = $('<div class="cms-btn">' + that.config.lang.cancel + '</div>');
                cancel.on(that.click, function () {
                    that.options.onClose = false;
                    that.close();
                });
                render.append(cancel);

                // render buttons
                this.ui.modalButtons.html(render);
            },

            _loadContent: function (url, name) {
                var that = this;

                // FIXME: A better fix is needed for '&' being interpreted as the
                // start of en entity by jQuery. See #3404
                url = url.replace('&', '&amp;');
                // now refresh the content
                var iframe = $('<iframe src="' + url + '" class="" frameborder="0" />');
                iframe.css('visibility', 'hidden');
                var holder = this.ui.iframeHolder;

                // set correct title
                var title = this.ui.title;
                title.html(name || '&nbsp;');

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

                    // after iframe is loaded append css
                    contents.find('head').append(
                        $('<link rel="stylesheet" type="text/css" href="' +
                          that.config.urls.static +
                          that.options.urls.css_modal + '" />')
                    );

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
                        if (name === undefined) {
                            title.html(innerTitle.text());
                        }
                        innerTitle.remove();

                        // than show
                        iframe.css('visibility', 'visible');

                        // append ready state
                        iframe.data('ready', true);

                        // attach close event
                        contents.find('body').on('keydown.cms', function (e) {
                            if (e.keyCode === 27) {
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
                if (el.hasClass('cms-modal-breadcrumb-last')) {
                    return false;
                }

                var parents = el.parent().find('a');
                parents.removeClass('cms-modal-breadcrumb-last');

                el.addClass('cms-modal-breadcrumb-last');

                this._loadContent(el.attr('href'));

                // update title
                this.ui.title.text(el.text());
            }

        });

    });
})(CMS.$);

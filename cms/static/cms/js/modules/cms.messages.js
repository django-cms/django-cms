/*
 * Copyright https://github.com/divio/django-cms
 */

var $ = require('jquery');
var Class = require('classjs');

/**
 * Displays a message underneath the toolbar.
 *
 * @class Messages
 * @namespace CMS
 */
var Messages = new Class({

    options: {
        messageDuration: 300,
        messageDelay: 3000
    },

    initialize: function initialize(options) {
        this.options = $.extend(true, {}, this.options, options);

        // states and events
        this.click = 'click.cms.message';

        // elements
        this._setupUI();
    },

    /**
     * Stores all jQuery references within `this.ui`.
     *
     * @method _setupUI
     * @private
     */
    _setupUI: function _setupUI() {
        var container = $('.cms');

        this.ui = {
            container: container,
            body: $('html'),
            toolbar: container.find('.cms-toolbar'),
            messages: container.find('.cms-messages')
        };
    },

    /**
     * Opens a message window underneath the toolbar.
     *
     * @method open
     * @param {Object} opts
     * @param {String|HTMLNode} opts.message message to be displayed
     * @param {String} [opts.dir='center'] direction to be displayed `center` `left` or `right`
     * @param {Number} [opts.delay=this.options.messageDelay] delay until message is closed, 0 leaves it open
     * @param {Boolean} [opts.error] if true sets the style to `.cms-messages-error`
     */
    open: function open(opts) {
        if (!(opts && opts.message)) {
            throw new Error('The arguments passed to "open" were invalid.');
        }

        var that = this;

        var msg = opts.message;
        var dir = opts.dir === undefined ? 'center' : opts.dir;
        var delay = opts.delay === undefined ? this.options.messageDelay : opts.delay;
        var error = opts.error === undefined ? false : opts.error;

        var width = 320;
        var height = this.ui.messages.outerHeight(true);
        var top = this.ui.toolbar.outerHeight(true);
        var close = this.ui.messages.find('.cms-messages-close');

        // add content to element
        this.ui.messages.find('.cms-messages-inner').html(msg);

        // error handling
        this.ui.messages.removeClass('cms-messages-error');
        if (error) {
            this.ui.messages.addClass('cms-messages-error');
        }

        // clear timeout
        clearTimeout(this.timer);

        close.hide();
        close.off(this.click).on(this.click, function () {
            that.close();
        });

        // set top to 0 if toolbar is collapsed
        if (CMS.settings.toolbar === 'collapsed') {
            top = 0;
        }

        // set correct position and show
        this.ui.messages.css('top', -height).show();

        // set correct direction and animation
        switch (dir) {
            case 'left':
                this.ui.messages.css({
                    'top': top,
                    'left': -width,
                    'right': 'auto',
                    'margin-left': 0
                });
                this.ui.messages.animate({ left: 0 });
                break;
            case 'right':
                this.ui.messages.css({
                    'top': top,
                    'right': -width,
                    'left': 'auto',
                    'margin-left': 0
                });
                this.ui.messages.animate({ right: 0 });
                break;
            default:
                this.ui.messages.css({
                    'left': '50%',
                    'right': 'auto',
                    'margin-left': -(width / 2)
                });
                this.ui.messages.animate({ top: top });
        }

        // cancel autohide if delay is <= 0
        if (delay <= 0) {
            close.show();
        } else {
            // add delay to hide if delay > 0
            this.timer = setTimeout(function () {
                that.close();
            }, delay);
        }
    },

    /**
     * Closes the message window underneath the toolbar.
     *
     * @method close
     */
    close: function close() {
        this.ui.messages.fadeOut(this.options.messageDuration);
    }

});

module.exports = Messages;

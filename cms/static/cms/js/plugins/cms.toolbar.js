/*##################################################|*/
/* #CMS.TOOLBAR# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Toolbar
	 * @version: 2.0.0
	 * @description: Adds toolbar, sideframe, messages and modal
	 */
	CMS.Toolbar = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'csrf': '',
			'authenticated': false,
			'debug': false, // not yet required
			'preventSwitch': false,
			'preventSwitchMessage': 'Switching is disabled.',
			'clipboard': null,
			'sideframeDuration': 300,
			'sideframeWidth': 320,
			'messageDelay': 2000,
			'modalDuration': 300,
			'modalWidth': 800,
			'modalHeight': 400,
			'urls': {
				'settings': '', // url to save settings
				'static': '/static/',
				'css_modal': 'cms/css/plugins/cms.toolbar.modal.css',
				'css_sideframe': 'cms/css/plugins/cms.toolbar.sideframe.css'
			},
			'settings': {
				'version': '3.0.0', // this is required to flush storage on new releases
				'toolbar': 'expanded', // expanded or collapsed
				'mode': 'edit', // live, draft, edit or layout
				'states': [],
				'sideframe': {
					'url': null,
					'hidden': false,
					'maximized': false
				},
				'position': null
			}
		},

		initialize: function (container, options) {
			this.container = $(container);
			this.options = $.extend(true, {}, this.options, options);
			this.settings = this.getSettings() || this.setSettings(this.options.settings);
			// class variables
			this.toolbar = this.container.find('.cms_toolbar');
			this.toolbar.hide();
			this.toolbarTrigger = this.container.find('.cms_toolbar-trigger');

			this.navigations = this.container.find('.cms_toolbar-item-navigation');
			this.buttons = this.container.find('.cms_toolbar-item-buttons');
			this.modes = this.container.find('.cms_toolbar-item-cms-mode-switcher a');
			this.switcher = this.container.find('.cms_toolbar-item_switch');

			this.body = $('html');
			this.sideframe = this.container.find('.cms_sideframe');
			this.messages = this.container.find('.cms_messages');
			this.modal = this.container.find('.cms_modal');
			this.tooltip = this.container.find('.cms_placeholders-tooltip');
			this.bars = $('.cms_placeholder-bar');

			this.plugins = $('.cms_plugin');
			this.placeholders = $('.cms_placeholder');

			this.lockToolbar = false;
			this.minimized = false;
			this.maximized = false;
			this.timer = function () {};

			// setup initial stuff
			this._setup();

			// setup events
			this._events();
		},

		// initial methods
		_setup: function () {
			// reset settings if version does not match
			if(this.settings.version !== this.options.settings.version) this.resetSettings();

			// setup toolbar visibility, we need to reverse the options to set the correct state
			(this.settings.toolbar === 'expanded') ? this._showToolbar(0, true) : this._hideToolbar(0, true);
			// setup toolbar mode
			(this.settings.mode === 'drag') ? this._enableDragMode(300, true) : this._enableEditMode(300, true);

			// load initial states
			this._load();

			// check if modes should be visible
			if($('.cms_placeholder-bar').length) {
				this.container.find('.cms_toolbar-item-cms-mode-switcher').show();
			}

			// hide publish button
			var publishBtn = $('.cms_btn-publish').parent();
				publishBtn.hide();
			if($('.cms_btn-publish-active').length) publishBtn.show();

			// add toolbar ready class to body
			$('body').addClass('cms_toolbar-ready');

			// check if debug is true
			if(this.options.debug) this._debug();
		},

		_load: function () {
			// reset some settings if not authenticated
			if(!this.options.authenticated) this._reset();
			// check if we should show the sideframe
			if(this.settings.sideframe.url) {
				this.openSideframe(this.settings.sideframe.url, false);
			}
		},

		_events: function () {
			var that = this;

			// attach event to the trigger handler
			this.toolbarTrigger.bind('click', function (e) {
				e.preventDefault();
				that.toggleToolbar();
			});

			// attach event to the navigation elements
			this.navigations.each(function () {
				var item = $(this);
				var lists = item.find('li');
				var hover = 'cms_toolbar-item-navigation-hover';
				var disabled = 'cms_toolbar-item-navigation-disabled';
				var children = 'cms_toolbar-item-navigation-children';

				// attach delegate event
				item.find('li ul a').bind('click', function (e) {
					e.preventDefault();
					if(!$(this).parent().hasClass(disabled)) that._delegate($(this));
				});
				// remove events from first level
				item.find('> li > a').bind('click', function (e) {
					e.preventDefault();
					if($(this).attr('href') !== ''
						&& $(this).attr('href') !== '#'
						&& !$(this).parent().hasClass(disabled)
						&& !$(this).parent().hasClass(disabled)) that._delegate($(this));
				});

				// handle hover states
				lists.bind('click', function (e) {
					e.stopImmediatePropagation();

					lists.removeClass(hover);
					$(this).addClass(hover);

					// add hover mechanism
					lists.bind('mouseenter', function () {
						// handle levels
						$(this).siblings().removeClass(hover);
						$(this).addClass(hover);
					});
					lists.find('> ul').bind('mouseleave', function () {
						$(this).find('li').removeClass(hover);
					});
					// adds escape mechanism fors children
					item.find('> li > a').add('> li li > a').bind('mouseenter', function () {
						if($(this).parent().hasClass(hover)) return false;
						lists.filter('.'+children).find('> ul').hide();
					});

					// ad sublevel mechanism
					lists.find('.'+children).bind('mouseenter', function () {
						$(this).find('> ul').show();
					});

					// add escape mechanism
					$(document).bind('click.cms', function () {
						lists.removeClass(hover);
						lists.unbind('mouseenter');
						$(document).unbind('click.cms');
					});
				});
			});

			// attach event to the switcher elements
			this.switcher.each(function () {
				$(this).bind('click', function (e) {
					e.preventDefault();
					that._setSwitcher($(e.currentTarget));
				});
			});

			// module events
			this._eventsSideframe();
			this._eventsModal();

			// stopper events
			$(document).bind('mouseup.cms', function (e) {
				that._stopSideframeResize();
				that._endModalMove(e);
				that._endModalResize(e);
			});

			this.modes.eq(0).bind('click', function (e) {
				e.preventDefault();
				that._enableEditMode(300);
			});
			this.modes.eq(1).bind('click', function (e) {
				e.preventDefault();
				that._enableDragMode(300);
			});

			// keyboard handling
			$(document).bind('keydown', function (e) {
				// check if we have an important focus
				var fields = $('*:focus');
				// 32 = space
				if(e.keyCode === 32 && that.settings.mode === 'drag' && !fields.length) {
					e.preventDefault();
					that._enableEditMode(300);
				} else if(e.keyCode === 32 && that.settings.mode === 'edit' && !fields.length) {
					e.preventDefault();
					that._enableDragMode(300);
				}
			});
		},

		_eventsSideframe: function () {
			var that = this;

			// attach close event
			this.sideframe.find('.cms_sideframe-close').bind('click', function () {
				that.closeSideframe(true);
			});

			// attach hide event
			this.sideframe.find('.cms_sideframe-hide').bind('click', function () {
				if($(this).hasClass('cms_sideframe-hidden')) {
					that.settings.sideframe.hidden = false;
					that._showSideframe(that.options.sideframeWidth, true);
				} else {
					that.settings.sideframe.hidden = true;
					that._hideSideframe();
				}
				that.setSettings();
			});

			// attach maximize event
			this.sideframe.find('.cms_sideframe-maximize').bind('click', function () {
				if($(this).hasClass('cms_sideframe-minimize')) {
					that.settings.sideframe.maximized = false;
					that._minimizeSideframe();
				} else {
					that.settings.sideframe.maximized = true;
					that.settings.sideframe.hidden = false;
					that._maximizeSideframe();
				}
				that.setSettings();
			});

			this.sideframe.find('.cms_sideframe-resize').bind('mousedown', function (e) {
				e.preventDefault();
				that._startSideframeResize();
			});
		},

		_eventsModal: function () {
			var that = this;

			// attach events to window
			this.modal.find('.cms_modal-close').bind('click', function (e) {
				e.preventDefault();
				that.closeModal();
			});
			this.modal.find('.cms_modal-collapse').bind('click', function (e) {
				e.preventDefault();
				that._minimizeModal();
			});
			this.modal.find('.cms_modal-title').bind('mousedown.cms', function (e) {
				e.preventDefault();
				that._startModalMove(e);
			});
			this.modal.find('.cms_modal-resize').bind('mousedown.cms', function (e) {
				e.preventDefault();
				that._startModalResize(e);
			});
			this.modal.find('.cms_modal-maximize').bind('click', function (e) {
				e.preventDefault();
				that._maximizeModal();
			});
			this.modal.find('.cms_modal-breadcrumb-items a').live('click', function (e) {
				e.preventDefault();
				that._changeModalContent($(this));
			});
			this.modal.find('.cms_modal-cancel').bind('click', function (e) {
				e.preventDefault();
				that.closeModal();
			});
		},

		// public methods
		toggleToolbar: function (show) {
			// overwrite state when provided
			if(show) this.settings.toolbar = 'collapsed';
			// toggle bar
			(this.settings.toolbar === 'collapsed') ? this._showToolbar(200) : this._hideToolbar(200);
		},

		setSettings: function (settings) {
			// cancel if local storage is not available
			if(!window.localStorage) return false;

			// set settings
			settings = $.extend({}, this.settings, settings);
			// save inside local storage
			localStorage.setItem('cms_cookie', JSON.stringify(settings));

			return settings;
		},

		getSettings: function () {
			// cancel if local storage is not available
			if(!window.localStorage) return false;

			// get settings
			return JSON.parse(localStorage.getItem('cms_cookie'));
		},

		resetSettings: function () {
			// cancel if local storage is not available
			if(!window.localStorage) return false;

			// reset settings
			window.localStorage.removeItem('cms_cookie');
			this.settings = this.setSettings(this.options.settings);

			// enforce reload to apply changes
			CMS.API.Helpers.reloadBrowser();
		},

		openSideframe: function (url, animate) {
			// prepare iframe
			var that = this;
			var holder = this.sideframe.find('.cms_sideframe-frame');
			var iframe = $('<iframe src="'+url+'" class="" frameborder="0" />');
				iframe.hide();
			var width = this.options.sideframeWidth;

			// attach load event to iframe
			iframe.bind('load', function () {
				// after iframe is loaded append css
				iframe.contents().find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.options.urls.static + that.options.urls.css_sideframe + '" />'));
				// remove loader
				that.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');
				// than show
				iframe.show();
				// if a message is triggerd, refresh
				var messages = iframe.contents().find('.messagelist li');
				if(messages.length || that.enforceReload) {
					that.enforceReload = true;
				} else {
					that.enforceReload = false;
				}

				// add debug infos
				if(that.options.debug) iframe.contents().find('body').addClass('cms_debug');

				// save url in settings
				that.settings.sideframe.url = iframe.get(0).contentWindow.location.href;
				that.setSettings();
			});

			// cancel animation if sideframe is already shown
			if(this.sideframe.is(':visible')) {
				// sideframe is already open
				insertHolder(iframe);
				// reanimate the frame
				if(parseInt(this.sideframe.css('width')) <= width) this._showSideframe(width, animate);
			} else {
				// load iframe after frame animation is done
				setTimeout(function () {
					insertHolder(iframe);
				}, this.options.sideframeDuration);
				// display the frame
				this._showSideframe(width, animate);
			}

			function insertHolder(iframe) {
				// show iframe after animation
				that.sideframe.find('.cms_sideframe-frame').addClass('cms_loader');
				holder.html(iframe);
			}
		},

		closeSideframe: function () {
			this._hideSideframe(true);

			// remove url in settings
			this.settings.sideframe = {
				'url': null,
				'hidden': false,
				'maximized': false
			};
			this.setSettings();
		},

		openMessage: function (msg, dir, delay, error) {
			// set toolbar freeze
			this.lockToolbar = true;

			// add content to element
			this.messages.find('.cms_messages-inner').html(msg);

			// clear timeout
			clearTimeout(this.timer);

			// determine width
			var that = this;
			var width = 320;
			var height = this.messages.outerHeight(true);
			var top = this.toolbar.outerHeight(true);
			var close = this.messages.find('.cms_messages-close');
				close.hide();
				close.bind('click', function () {
					that.closeMessage();
				});

			// set top to 0 if toolbar is collapsed
			if(this.settings.toolbar === 'collapsed') top = 0;

			// do we need to add debug styles?
			if(this.options.debug) top = top + 5;

			// set correct position and show
			this.messages.css('top', -height).show();

			// error handling
			this.messages.removeClass('cms_messages-error');
			if(error) this.messages.addClass('cms_messages-error');

			// dir should be left, center, right
			dir = dir || 'center';
			// set correct direction and animation
			switch(dir) {
				case 'left':
					this.messages.css({
						'top': top,
						'left': -width,
						'right': 'auto',
						'margin-left': 0
					});
					this.messages.animate({ 'left': 0 });
					break;
				case 'right':
					this.messages.css({
						'top': top,
						'right': -width,
						'left': 'auto',
						'margin-left': 0
					});
					this.messages.animate({ 'right': 0 });
					break;
				default:
					this.messages.css({
						'left': '50%',
						'right': 'auto',
						'margin-left': -(width / 2)
					});
					this.messages.animate({ 'top': top });
			}

			// cancel autohide if delay is 0
			if(delay === 0) {
				close.show();
				return false
			}
			// add delay to hide
			this.timer = setTimeout(function () {
				that.closeMessage();
			}, delay || this.options.messageDelay);
		},

		closeMessage: function () {
			this.messages.fadeOut(300);
			// unlock toolbar
			this.lockToolbar = false;
		},

		openModal: function (url, name, breadcrumb) {
			// reset breadcrumb
			this.modal.find('.cms_modal-breadcrumb').hide();
			this.modal.find('.cms_modal-breadcrumb-items').html('');

			// empty buttons
			this.modal.find('.cms_modal-buttons').html('');

			var contents = this.modal.find('.cms_modal-body, .cms_modal-foot');
				contents.show();

			this._loadModalContent(url, name);

			// insure modal is not maximized
			if(this.modal.find('.cms_modal-collapsed').length) this._minimizeModal();

			// reset styles
			this.modal.css({
				'left': '50%',
				'top': '50%',
				'mergin-left': 0,
				'margin-right': 0
			});
			this.modal.find('.cms_modal-body').css({
				'width': this.options.modalWidth,
				'height': this.options.modalHeight
			});
			this.modal.find('.cms_modal-body').removeClass('cms_loader');
			this.modal.find('.cms_modal-maximize').removeClass('cms_modal-maximize-active');
			this.maximized = false;

			// we need to render the breadcrumb
			this._setModalBreadcrumb(breadcrumb);

			// display modal
			this._showModal(this.options.modalDuration);
		},

		closeModal: function () {
			this._hideModal(100);
		},

		openAjax: function (url, post, text) {
			var that = this;

			// check if we have a confirmation text
			var question = (text) ? confirm(text) : true;
			// cancel if question has been denied
			if(!question) return false;

			$.ajax({
				'type': 'POST',
				'url': url,
				'data': (post) ? JSON.parse(post) : {},
				'success': function () {
					CMS.API.Helpers.reloadBrowser();
				},
				'error': function (jqXHR) {
					that.showError(jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText);
				}
			});
		},

		setActive: function (id) {
			// reset active statesdragholders
			$('.cms_draggable').removeClass('cms_draggable-selected');
			$('.cms_plugin').removeClass('cms_plugin-active');

			// if false is provided, only remove classes
			if(id === false) return false;

			// attach active class to current element
			var dragitem = $('#cms_draggable-' + id);
			var plugin = $('#cms_plugin-' + id);

			// collapse all previous elements
			var collapsed = dragitem.parents().siblings().filter('.cms_dragitem-collapsed');
				collapsed.trigger('click');

			// set new classes
			dragitem.addClass('cms_draggable-selected');
			plugin.addClass('cms_plugin-active');

			// set new position
			var pos = plugin.position('body').top;
			var bound = $(window).height();
			var offset = 200;
			if(bound - pos <= 0) $(window).scrollTop(pos - offset);
		},

		showError: function (msg) {
			this.openMessage(msg, 'center', this.options.messageDelay, true);
		},

		// private methods
		_showToolbar: function (speed, init) {
			this.toolbarTrigger.addClass('cms_toolbar-trigger-expanded');
			this.toolbar.slideDown(speed);
			// set messages top to toolbar height
			this.messages.css('top', 31);
			// set new settings
			this.settings.toolbar = 'expanded';
			if(!init) this.setSettings();
		},

		_hideToolbar: function (speed, init) {
			// cancel if sideframe is active
			if(this.lockToolbar) return false;

			this.toolbarTrigger.removeClass('cms_toolbar-trigger-expanded');
			this.toolbar.slideUp(speed);
			// set messages top to 0
			this.messages.css('top', 0);
			// set new settings
			this.settings.toolbar = 'collapsed';
			if(!init) this.setSettings();
		},

		_enableEditMode: function (speed, init) {
			this.bars.hide();
			this.plugins.stop(true, true).fadeIn(speed);
			this.placeholders.hide();

			// set active item
			this.modes.removeClass('cms_btn-active').eq(0).addClass('cms_btn-active');
			this.settings.mode = 'edit';

			// set correct position
			$('body').scrollTop(this.settings.position || 0);

			// hide clipboard if in edit mode
			this.container.find('.cms_clipboard').hide();

			if(!init) this.setSettings();
		},

		_enableDragMode: function (speed, init) {
			// we need to save the position first
			this.settings.position = $('body').scrollTop();

			this.bars.fadeIn(speed);
			this.plugins.hide();
			this.placeholders.stop(true, true).fadeIn(speed);

			// set active item
			this.modes.removeClass('cms_btn-active').eq(1).addClass('cms_btn-active');
			this.settings.mode = 'drag';

			// show clipboard in build mode
			this.container.find('.cms_clipboard').fadeIn(speed);

			if(!init) this.setSettings();
		},

		_setSwitcher: function (el) {
			// save local vars
			var active = el.hasClass('cms_toolbar-item_switch-active');
			var anchor = el.find('a');
			var knob = el.find('.cms_toolbar-item_switch-knob');
			var duration = 300;

			// prevent if switchopstion is passed
			if(this.options.preventSwitch) {
				this.openMessage(this.options.preventSwitchMessage, 'right');
				return false;
			}

			// determin what to trigger
			if(active) {
				knob.animate({
					'right': anchor.outerWidth(true) - (knob.outerWidth(true) + 2)
				}, duration);
				// move anchor behind the knob
				anchor.css('z-index', 1).animate({
					'padding-top': 6,
					'padding-right': 14,
					'padding-bottom': 4,
					'padding-left': 28
				}, duration);
			} else {
				knob.animate({
					'left': anchor.outerWidth(true) - (knob.outerWidth(true) + 2)
				}, duration);
				// move anchor behind the knob
				anchor.css('z-index', 1).animate({
					'padding-top': 6,
					'padding-right': 28,
					'padding-bottom': 4,
					'padding-left': 14
				}, duration);
			}

			// reload
			setTimeout(function () {
				window.location.href = anchor.attr('href');
			}, duration);
		},

		_delegate: function (el) {
			// save local vars
			var target = el.attr('data-rel');

			// reset states
			this._reset();

			switch(target) {
				case 'modal':
					this.openModal(el.attr('href'), el.attr('data-name'));
					break;
				case 'message':
					this.openMessage(el.attr('data-text'));
					break;
				case 'sideframe':
					this.openSideframe(el.attr('href'), true);
					break;
				case 'ajax':
					this.openAjax(el.attr('href'), el.attr('data-post'), el.attr('data-text'));
					break;
				default:
					window.location.href = el.attr('href');
			}
		},

		_reset: function () {
			// reset sideframe settings
			this.settings.sideframe = {
				'url': null,
				'hidden': false,
				'maximized': this.settings.sideframe.maximized // we need to keep the default value
			};
		},

		_showSideframe: function (width, animate) {
			// add class
			this.sideframe.find('.cms_sideframe-hide').removeClass('cms_sideframe-hidden');

			// check if sideframe should be hidden
			if(this.settings.sideframe.hidden) this._hideSideframe();
			// check if sideframe should be maximized
			if(this.settings.sideframe.maximized) this._maximizeSideframe();
			// otherwise do normal behaviour
			if(!this.settings.sideframe.hidden && !this.settings.sideframe.maximized) {
				if(animate) {
					this.sideframe.animate({ 'width': width }, this.options.sideframeDuration);
					this.body.animate({ 'margin-left': width }, this.options.sideframeDuration);
				} else {
					this.sideframe.animate({ 'width': width }, 0);
					this.body.animate({ 'margin-left': width }, 0);
				}
				this.sideframe.find('.cms_sideframe-btn').css('right', -20);
			}

			this.lockToolbar = true;
		},

		_hideSideframe: function (close) {
			// add class
			this.sideframe.find('.cms_sideframe-hide').addClass('cms_sideframe-hidden');

			var duration = this.options.sideframeDuration;
			// remove the iframe
			if(close && this.sideframe.width() <= 0) duration = 0;
			if(close) this.sideframe.find('iframe').remove();
			this.sideframe.animate({ 'width': 0 }, duration, function () {
				if(close) $(this).hide();
			});
			this.body.animate({ 'margin-left': 0 }, duration);
			this.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');

			// should we reload
			if(this.enforceReload) CMS.API.Helpers.reloadBrowser();

			this.lockToolbar = false;
		},

		_minimizeSideframe: function () {
			this.sideframe.find('.cms_sideframe-maximize').removeClass('cms_sideframe-minimize');
			this.sideframe.find('.cms_sideframe-hide').show();

			// hide scrollbar
			this.body.css('overflow', 'auto');

			// reset to first state
			this._showSideframe(this.options.sideframeWidth, true);

			// remove event
			$(window).unbind('resize.cms');
		},

		_maximizeSideframe: function () {
			var that = this;

			this.sideframe.find('.cms_sideframe-maximize').addClass('cms_sideframe-minimize');
			this.sideframe.find('.cms_sideframe-hide').hide();

			// reset scrollbar
			this.body.css('overflow', 'hidden');

			this.sideframe.find('.cms_sideframe-hide').removeClass('cms_sideframe-hidden').hide();
			// do custom animation
			this.sideframe.animate({ 'width': $(window).width() }, 0);
			this.body.animate({ 'margin-left': 0 }, 0);
			// invert icon position
			this.sideframe.find('.cms_sideframe-btn').css('right', -2);
			// attach resize event
			$(window).bind('resize.cms', function () {
				that.sideframe.css('width', $(window).width());
			});
		},

		_startSideframeResize: function () {
			var that = this;
			// this prevents the iframe from being focusable
			this.sideframe.find('.cms_sideframe-shim').css('z-index', 20);

			$(document).bind('mousemove.cms', function (e) {
				if(e.clientX <= 320) e.clientX = 320;

				that.sideframe.css('width', e.clientX);
				that.body.css('margin-left', e.clientX);
			});
		},

		_stopSideframeResize: function () {
			this.sideframe.find('.cms_sideframe-shim').css('z-index', 1);

			$(document).unbind('mousemove.cms');
		},

		_showModal: function (speed) {
			// we need to position the modal in the center
			var that = this;
			var width = this.modal.width();
			var height = this.modal.height();

			// animates and sets the modal
			this.modal.css({
				'width': 0,
				'height': 0,
				'margin-left': 0,
				'margin-top': 0
			}).stop(true, true).animate({
				'width': width,
				'height': height,
				'margin-left': -(width / 2),
				'margin-top': -(height / 2)
			}, speed, function () {
				$(this).removeAttr('style');

				that.modal.css({
					'margin-left': -(width / 2),
					'margin-top': -(height / 2)
				});

				// fade in modal window
				that.modal.show();
			});
		},

		_hideModal: function (speed) {
			this.modal.fadeOut(speed);
			this.modal.find('.cms_modal-frame iframe').remove();
			this.modal.find('.cms_modal-body').removeClass('cms_loader');
		},

		_minimizeModal: function () {
			var trigger = this.modal.find('.cms_modal-collapse');
			var contents = this.modal.find('.cms_modal-body, .cms_modal-foot');

			// cancel action if maximized
			if(this.maximized) return false;

			if(this.minimized === false) {
				// minimize
				trigger.addClass('cms_modal-collapsed');
				contents.hide();

				// save initial state
				this.modal.data('css', {
					'left': this.modal.css('left'),
					'top': this.modal.css('top'),
					'margin': this.modal.css('margin')
				});

				this.modal.css({
					'left': this.toolbar.find('.cms_toolbar-left').outerWidth(true) + 50,
					'top': (this.options.debug) ? 6 : 1,
					'margin': 0
				});

				this.minimized = true;
			} else {
				// minimize
				trigger.removeClass('cms_modal-collapsed');
				contents.show();

				// reattach css
				this.modal.css(this.modal.data('css'));

				this.minimized = false;
			}
		},

		_maximizeModal: function () {
			var debug = (this.options.debug) ? 5 : 0;
			var container = this.modal.find('.cms_modal-body');
			var trigger = this.modal.find('.cms_modal-maximize');
			var btnCk = this.modal.find('iframe').contents().find('.cke_button__maximize');

			// cancel action when minimized
			if(this.minimized) return false;

			if(this.maximized === false) {
				// maximize
				this.maximized = true;
				trigger.addClass('cms_modal-maximize-active');

				this.modal.data('css', {
					'left': this.modal.css('left'),
					'top': this.modal.css('top'),
					'margin': this.modal.css('margin')
				});
				container.data('css', {
					'width': container.width(),
					'height': container.height()
				});

				// reset
				this.modal.css({
					'left': 0,
					'top': debug,
					'margin': 0
				});
				// bind resize event
				$(window).bind('resize.cms.modal', function () {
					container.css({
						'width': $(window).width(),
						'height': $(window).height() - 60 - debug
					});
				});
				$(window).trigger('resize.cms.modal');

				// trigger wysiwyg fullscreen
				if(btnCk.hasClass('cke_button_off')) btnCk.trigger('click');
			} else {
				// minimize
				this.maximized = false;
				trigger.removeClass('cms_modal-maximize-active');

				$(window).unbind('resize.cms.modal');

				// reattach css
				this.modal.css(this.modal.data('css'));
				container.css(container.data('css'));

				// trigger wysiwyg fullscreen
				if(btnCk.hasClass('cke_button_on')) btnCk.trigger('click');
			}
		},

		_startModalMove: function (initial) {
			// cancel if maximized
			if(this.maximized) return false;
			// cancel action when minimized
			if(this.minimized) return false;

			var that = this;
			var position = that.modal.position();

			this.modal.find('.cms_modal-shim').show();

			$(document).bind('mousemove.cms', function (e) {
				var left = position.left - (initial.pageX - e.pageX) - $(window).scrollLeft();
				var top = position.top - (initial.pageY - e.pageY) - $(window).scrollTop();

				that.modal.css({
					'left': left,
					'top': top
				});
			});
		},

		_endModalMove: function () {
			this.modal.find('.cms_modal-shim').hide();

			$(document).unbind('mousemove.cms');
		},

		_startModalResize: function (initial) {
			// cancel if in fullscreen
			if(this.maximized) return false;
			// continue
			var that = this;
			var container = this.modal.find('.cms_modal-body');
			var width = container.width();
			var height = container.height();
			var modalLeft = this.modal.position().left;
			var modalTop = this.modal.position().top;

			this.modal.find('.cms_modal-shim').show();

			$(document).bind('mousemove.cms', function (e) {
				var mvX = initial.pageX - e.pageX;
				var mvY = initial.pageY - e.pageY;

				var w = width - (mvX * 2);
				var h = height - (mvY * 2);
				var max = 680;

				// add some limits
				if(w <= max || h <= 100) return false;

				// set centered animation
				container.css({
					'width': width - (mvX * 2),
					'height': height - (mvY * 2)
				});
				that.modal.css({
					'left': modalLeft + mvX,
					'top': modalTop + mvY
				});
			});
		},

		_endModalResize: function () {
			this.modal.find('.cms_modal-shim').hide();

			$(document).unbind('mousemove.cms');
		},

		_setModalBreadcrumb: function (breadcrumb) {
			var bread = this.modal.find('.cms_modal-breadcrumb');
			var crumb = '';

			// cancel if there is no breadcrumb)
			if(!breadcrumb || breadcrumb.length <= 0) return false;
			if(!breadcrumb[0].title) return false;

			// load breadcrumb
			$.each(breadcrumb, function (index, item) {
				// check if the item is the last one
				var last = (index >= breadcrumb.length - 1) ? 'cms_modal-breadcrumb-last' : '';
				// render breadcrumb
				crumb += '<a href="' + item.url + '" class="' + last + '"><span>' + item.title + '</span></a>';
			});

			// attach elements
			bread.find('.cms_modal-breadcrumb-items').html(crumb);

			// show breadcrumb
			bread.show();
		},

		_setModalButtons: function (iframe) {
			var that = this;
			var row = iframe.contents().find('.submit-row:eq(0)');
			var buttons = row.find('input, a');
			var render = $('<span />'); // seriously jquery...

			// if there are no buttons, try again
			if(!buttons.length) {
				row = iframe.contents().find('form:eq(0)');
				buttons = row.find('input[type="submit"]');
				buttons.attr('name', '_save')
					.addClass('deletelink')
					.hide();
				this.enforceReload = true;
			} else {
				this.enforceReload = false;
			}

			// attach relation id
			buttons.each(function (index, item) {
				$(item).attr('data-rel', '_' + index);
			});

			// loop over input buttons
			buttons.each(function (index, item) {
				item = $(item);

				// cancel if item is a hidden input
				if(item.attr('type') === 'hidden') return false;

				// create helper variables
				var title = item.attr('value') || item.text();
				var cls = 'cms_btn';

				// set additional special css classes
				if(item.hasClass('default')) cls = 'cms_btn cms_btn-action';
				if(item.hasClass('deletelink')) cls = 'cms_btn cms_btn-caution';

				// create the element
				var el = $('<div class="'+cls+' '+item.attr('class')+'">'+title+'</div>');
					el.bind('click', function () {
						if(item.is('input')) item.click();
						if(item.is('anchor')) iframe.attr('src', item.attr('href'));

						// trigger only when blue action buttons are triggered
						if(item.hasClass('default') || item.hasClass('deletelink')) {
							that.enforceClose = true;
						} else {
							that.enforceClose = false;
						}

						// hide iframe again
						that.modal.find('iframe').hide();
					});

				// append element
				render.append(el);
			});

			// manually add cancel button at the end
			var cancel = $('<div class="cms_btn">'+this.options.lang.cancel+'</div>');
				cancel.bind('click', function () {
					that.closeModal();
				});
			render.append(cancel);

			// unwrap helper and ide row
			row.hide();

			// render buttons
			this.modal.find('.cms_modal-buttons').html(render);
		},

		_loadModalContent: function (url, name) {
			var that = this;

			// now refresh the content
			var iframe = $('<iframe src="'+url+'" class="" frameborder="0" />');
				iframe.hide();
			var holder = this.modal.find('.cms_modal-frame');

			// set correct title
			var title = this.modal.find('.cms_modal-title');
				title.html(name);

			// insure previous iframe is hidden
			holder.find('iframe').hide();

			// attach load event for iframe to prevent flicker effects
			iframe.bind('load', function () {
				// show messages in toolbar if provided
				var messages = iframe.contents().find('.messagelist li');
					if(messages.length) that.openMessage(messages.eq(0).text());
					messages.remove();

				// determine if we should close the modal or reload
				if(messages.length && that.enforceReload) window.location.href = '/'; // redirect to home
				if(messages.length && that.enforceClose) {
					that.closeModal();
					return false;
				}

				// after iframe is loaded append css
				iframe.contents().find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.options.urls.static + that.options.urls.css_modal + '" />'));

				// set title of not provided
				var innerTitle = iframe.contents().find('#content h1:eq(0)');
				if(name === undefined) {
					if(title.text().replace(/^\s+|\s+$/g, '') === '') title.html(innerTitle.text());
				}
				innerTitle.remove();

				// set modal buttons
				that._setModalButtons($(this));

				// than show
				iframe.show();

				// append ready state
				iframe.data('ready', true);
			});

			// inject
			setTimeout(function () {
				that.modal.find('.cms_modal-body').addClass('cms_loader');
				holder.html(iframe);
			}, this.options.modalDuration);
		},

		_changeModalContent: function (el) {
			if(el.hasClass('cms_modal-breadcrumb-last')) return false;

			var parents = el.parent().find('a');
				parents.removeClass('cms_modal-breadcrumb-last');

			el.addClass('cms_modal-breadcrumb-last');

			this._loadModalContent(el.attr('href'));

			// update title
			this.modal.find('.cms_modal-title').text(el.text());
		},

		_debug: function () {
			var that = this;
			var timeout = 1000;
			var timer = function () {};

			// add top margin
			$('html').css('margin-top', 5);

			// bind message event
			var debug = this.container.find('.cms_debug-bar');
				debug.bind('mouseenter mouseleave', function (e) {
					clearTimeout(timer);

					if(e.type === 'mouseenter') {
						timer = setTimeout(function () {
							that.openMessage(that.options.lang.debug);
						}, timeout);
					}
				});
		}

	});

});
})(CMS.$);
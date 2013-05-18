/*##################################################|*/
/* #CMS.TOOLBAR# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Toolbar
	 * @version: 2.0.0
	 * @description: Adds toolbar, sidebar, messages and modal
	 */
	CMS.Toolbar = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'csrf': '',
			'debug': false, // not yet required
			'settings': {
				'toolbar': 'expanded', // expanded or collapsed
				'mode': 'edit', // live, draft, edit or layout
				'states': []
			},
			'preventSwitch': false,
			'preventSwitchMessage': 'Switching is disabled.',
			'clipboard': null,
			'sidebarDuration': 300,
			'sidebarWidth': 320,
			'messageDelay': 2000,
			'modalDuration': 300,
			'modalWidth': 800,
			'modalHeight': 400,
			'urls': {
				'settings': '', // url to save settings
				'css_modal': '/static/cms/css/plugins/cms.toolbar.dialog.css',
				'css_sideframe': '/static/cms/css/plugins/cms.toolbar.sideframe.css'
			},
			'lang': {
				'confirm': 'Yes',
				'cancel': 'Cancel'
			}
		},

		initialize: function (container, options) {
			this.container = $(container);
			this.options = $.extend(true, {}, this.options, options);
			this.settings = this.options.settings;

			// class variables
			this.toolbar = this.container.find('.cms_toolbar');
			this.toolbar.hide();
			this.toolbarTrigger = this.container.find('.cms_toolbar-trigger');

			this.navigations = this.container.find('.cms_toolbar-item-navigation');
			this.buttons = this.container.find('.cms_toolbar-item-buttons');
			this.modes = this.container.find('.cms_toolbar-item-buttons-group a');
			this.switcher = this.container.find('.cms_toolbar-item_switch');

			this.body = $('html');
			this.sideframe = this.container.find('.cms_sideframe');
			this.messages = this.container.find('.cms_messages');
			this.modal = this.container.find('.cms_modal');
			this.tooltip = this.container.find('.cms_placeholders-tooltip');
			this.menu = this.container.find('.cms_placeholders-menu');
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
			// set correct settings
			if(this.getSettings() === null) this.setSettings();
			this.settings = this.getSettings();

			// setup toolbar visibility, we need to reverse the options to set the correct state
			(this.settings.toolbar === 'expanded') ? this._showToolbar(0, true) : this._hideToolbar(0, true);
			// setup toolbar mode
			(this.settings.mode === 'drag') ? this._enableDragMode(300, true) : this._enableEditMode(300, true);
		},

		_events: function () {
			var that = this;

			// attach event to the trigger handler
			this.toolbarTrigger.bind('click', function (e) {
				e.preventDefault();
				that.toggleToolbar(200);
			});

			// attach event to the navigation elements
			this.navigations.each(function () {
				var item = $(this);
				// attach delegate event
				item.find('li ul a').bind('click', function (e) {
					e.preventDefault();
					if(!$(this).parent().hasClass('cms_toolbar-item-navigation-disabled')) that.delegate($(this));
				});
				// remove events from first level
				item.find('> li > a').bind('click', function (e) {
					e.preventDefault();
					if($(this).attr('href') !== ''
						&& $(this).attr('href') !== '#'
						&& !$(this).parent().hasClass('cms_toolbar-item-navigation-disabled')
						&& !$(this).parent().hasClass('cms_toolbar-item-navigation-disabled')) that.delegate($(this));
				});

				// handle states
				var states = $(['> li', '> li li', '> li li li']);
					states.each(function (index, list) {
						item.find(list).bind('mouseenter mouseleave', function (e) {
							item.find(list).removeClass('cms_toolbar-item-navigation-hover');
							if(e.type === 'mouseenter') $(this).addClass('cms_toolbar-item-navigation-hover');
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
			this._eventsSidebar();
			this._eventsModal();

			// stopper events
			$(document).bind('mouseup.cms', function (e) {
				that._stopSideframeResize();
				that._endModalMove(e);
				that._endModalResize(e);
			});

			// event for switching between edit and layout mode
			this.menu.bind('click', function () {
				($(this).hasClass('cms_placeholders-menu-alternate')) ? that._enableEditMode(300) : that._enableDragMode(300);

				// attach active class to current element
				var id = $(this).data('id');

				// set active state
				that.setActive(id);

				// set new position
				var pos = $('#cms_plugin-' + id).position('body').top;
				var bound = $(window).height();
				var offset = 200;
				if(bound - pos <= 0) $(window).scrollTop(pos - offset);
			});

			this.modes.eq(0).bind('click', function (e) {
				e.preventDefault();
				that._enableEditMode(300);
			});
			this.modes.eq(1).bind('click', function (e) {
				e.preventDefault();
				that._enableDragMode(300);
			});
		},

		_eventsSidebar: function () {
			var that = this;

			// attach event to the sidebar
			this.sideframe.find('.cms_sideframe-close').bind('click', function () {
				that.closeSideframe(true);
			});

			this.sideframe.find('.cms_sideframe-hide').bind('click', function () {
				if($(this).hasClass('cms_sideframe-hidden')) {
					$(this).removeClass('cms_sideframe-hidden');
					that._showSideframe(that.options.sidebarWidth);
				} else {
					$(this).addClass('cms_sideframe-hidden');
					that._hideSideframe();
				}
			});

			this.sideframe.find('.cms_sideframe-maximize').bind('click', function () {
				if($(this).hasClass('cms_sideframe-minimize')) {
					$(this).removeClass('cms_sideframe-minimize');
					that.sideframe.find('.cms_sideframe-hide').show();
					that._showSideframe(that.options.sidebarWidth);
				} else {
					$(this).addClass('cms_sideframe-minimize');
					that.sideframe.find('.cms_sideframe-hide').removeClass('cms_sideframe-hidden').hide();
					that._showSideframe(0, true);
				}
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
			this.modal.find('.cms_modal-save').bind('click', function (e) {
				e.preventDefault();
				that._saveModal();
			});
		},

		// public methods
		toggleToolbar: function (speed) {
			(this.settings.toolbar === 'collapsed') ? this._showToolbar(speed) : this._hideToolbar(speed);
		},

		setSettings: function (settings) {
			// cancel if local storage is not available
			if(!window.localStorage) return false;
			// set settings
			settings = $.extend({}, this.settings, settings);
			return localStorage.setItem('cms_cookie', JSON.stringify(settings));
		},

		getSettings: function () {
			// cancel if local storage is not available
			if(!window.localStorage) return false;
			// get settings
			return JSON.parse(localStorage.getItem('cms_cookie'));
		},

		delegate: function (el) {
			// save local vars
			var target = el.attr('data-rel');

			switch(target) {
				case 'modal':
					this.openModal(el.attr('href'), el.attr('data-name'), [{
						'title': el.attr('data-name'),
						'url': el.attr('href')
					}]);
					break;
				case 'message':
					this.openMessage(el.attr('data-text'));
					break;
				case 'sideframe':
					this.openSideframe(el.attr('href'));
					break;
				case 'ajax':
					this.openAjax(el.attr('href'), el.attr('data-post'));
					break;
				default:
					window.location.href = el.attr('href');
			}
		},

		openSideframe: function (url, maximized) {
			// prepare iframe
			var that = this;
			var holder = this.sideframe.find('.cms_sideframe-frame');
			var iframe = $('<iframe src="'+url+'" class="" frameborder="0" />');
				iframe.hide();
			var width = this.options.sidebarWidth;

			// attach load event to iframe
			iframe.bind('load', function () {
				iframe.show();
				that.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');
			});

			// cancel animation if sidebar is already shown
			if(this.sideframe.is(':visible')) {
				// sidebar is already open
				insertHolder(iframe);
				// reanimate the frame
				if(parseInt(this.sideframe.css('width')) <= width) this._showSideframe(width, maximized);
			} else {
				// load iframe after frame animation is done
				setTimeout(function () {
					insertHolder(iframe);
				}, this.options.sidebarDuration);
				// display the frame
				this._showSideframe(width, maximized);
			}

			function insertHolder(iframe) {
				// show iframe after animation
				that.sideframe.find('.cms_sideframe-frame').addClass('cms_loader');
				holder.html(iframe);
			}
		},

		closeSideframe: function () {
			this._hideSideframe(true);
		},

		openMessage: function (msg, dir, error, delay) {
			// set toolbar freeze
			this.lockToolbar = true;

			// add content to element
			this.messages.find('.cms_messages-inner').html(msg);

			// clear timeout
			clearTimeout(this.timer);

			// determine width
			var that = this;
			var width = this.messages.outerWidth(true);
			var height = this.messages.outerHeight(true);
			var top = this.toolbar.outerHeight(true);
			var close = this.messages.find('.cms_messages-close');
				close.hide();
				close.bind('click', function () {
					that.closeMessage();
				});

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
						'left': -width
					});
					this.messages.animate({ 'left': 0 });
					break;
				case 'right':
					this.messages.css({
						'top': top,
						'right': -width
					});
					this.messages.animate({ 'right': 0 });
					break;
				default:
					this.messages.css({
						'left': '50%',
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
			// prepare iframe
			var that = this;

			var iframe = $('<iframe src="'+url+'" frameborder="0" style="background:#fff;" />');
				iframe.hide();
			var holder = this.modal.find('.cms_modal-frame');
			var contents = this.modal.find('.cms_modal-body, .cms_modal-foot');
				contents.show();

			// insure previous iframe is hidden
			holder.find('iframe').hide();

			// attach load event for iframe to prevent flicker effects
			iframe.bind('load', function () {
				// after iframe is loaded append css
				iframe.contents().find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.options.urls.css_modal + '" />'));

				// set modal buttons
				that._setModalButtons($(this));

				// than show
				iframe.show();
			});

			// show iframe after animation
			setTimeout(function () {
				that.modal.find('.cms_modal-body').addClass('cms_loader');
				holder.html(iframe);
			}, this.options.modalDuration);

			// set correct title
			var title = this.modal.find('.cms_modal-title');
				title.html(name || '&nbsp;');

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

			// empty buttons
			this.modal.find('.cms_modal-buttons').html('');

			// display modal
			this._showModal(this.options.modalDuration);
		},

		closeModal: function () {
			this._hideModal(100);
		},

		openAjax: function (url, post) {
			var that = this;

			$.ajax({
				'type': 'POST',
				'url': url,
				'data': (post) ? JSON.parse(post) : {},
				'success': function () {
					window.location.reload();
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

			// attach active class to current element
			var dragitem = $('#cms_draggable-' + id);
			var plugin = $('#cms_plugin-' + id);

			// set new classes
			dragitem.addClass('cms_draggable-selected');
			plugin.addClass('cms_plugin-active');
		},

		// private methods
		_showToolbar: function (speed, init) {
			this.toolbarTrigger.addClass('cms_toolbar-trigger-expanded');
			this.toolbar.slideDown(speed);
			this.settings.toolbar = 'expanded';
			if(!init) this.setSettings();
		},

		_hideToolbar: function (speed, init) {
			// cancel if sidebar is active
			if(this.lockToolbar) return false;

			this.toolbarTrigger.removeClass('cms_toolbar-trigger-expanded');
			this.toolbar.slideUp(speed);
			this.settings.toolbar = 'collapsed';
			if(!init) this.setSettings();
		},

		_enableEditMode: function (speed, init) {
			this.bars.hide();
			this.plugins.fadeIn(speed);
			this.placeholders.hide();
			this.menu.hide().removeClass('cms_placeholders-menu-alternate');

			// set active item
			this.modes.removeClass('cms_btn-active').eq(0).addClass('cms_btn-active');
			this.settings.mode = 'edit';

			// hide clipboard if in edit mode
			this.container.find('.cms_clipboard').hide();

			if(!init) this.setSettings();
		},

		_enableDragMode: function (speed, init) {
			this.bars.fadeIn(speed);
			this.plugins.hide();
			this.placeholders.fadeIn(speed);
			this.menu.hide().removeClass('cms_placeholders-menu-alternate');

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

		_showSideframe: function (width, maximized) {
			if(maximized) {
				this.sideframe.animate({ 'width': $(window).width() }, 0);
				this.body.animate({ 'margin-left': 0 }, 0);
				// invert icon position
				this.sideframe.find('.cms_sideframe-btn').css('right', -2);
			} else {
				this.sideframe.animate({ 'width': width }, this.options.sidebarDuration);
				this.body.animate({ 'margin-left': width }, this.options.sidebarDuration);
				this.sideframe.find('.cms_sideframe-btn').css('right', -20);
			}
			this.lockToolbar = true;
		},

		_hideSideframe: function (close) {
			var duration = this.options.sidebarDuration;
			// remove the iframe
			if(close && this.sideframe.width() <= 0) duration = 0;
			if(close) this.sideframe.find('iframe').remove();
			this.sideframe.animate({ 'width': 0 }, duration, function () {
				if(close) $(this).hide();
			});
			this.body.animate({ 'margin-left': 0 }, duration);
			this.sideframe.find('.cms_sideframe-frame').removeClass('cms_loader');
			this.lockToolbar = false;
		},

		_startSideframeResize: function () {
			var that = this;
			// this prevents the iframe from being focusable
			this.sideframe.find('.cms_sideframe-shim').css('z-index', 20);

			$(document).bind('mousemove.cms', function (e) {
				if(e.clientX <= 3) e.clientX = 3;

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
					'top': 1,
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
					'top': 0,
					'margin': 0
				});
				// bind resize event
				$(window).bind('resize.cms.modal', function () {
					container.css({
						'width': $(window).width(),
						'height': $(window).height() - 60
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
				var max = that.modal.find('.cms_modal-breadcrumb').outerWidth(true) + that.modal.find('.cms_modal-buttons').outerWidth(true);

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
			var row = iframe.contents().find('.submit-row');
			var buttons = row.find('input, a');
			var render = $('<span />');

			// loop over input buttons
			buttons.each(function (index, item) {
				item = $(item);

				// cancel if item is a hidden input
				if(item.attr('type') === 'hidden') return false;

				// create helper variables
				var title = item.attr('value') || item.text();
				var cls = 'cms_btn';

				// set additional css classes
				if(item.hasClass('default')) cls = 'cms_btn cms_btn-action';
				if(item.hasClass('deletelink')) cls = 'cms_btn cms_btn-caution';

				// create the element
				var el = $('<div class="'+cls+'" data-name="'+item.attr('name')+'" data-url="'+item.attr('href')+'">'+title+'</div>');
					el.bind('click', function () {
						var input = row.find('input[name="'+$(this).attr('data-name')+'"]');
						if(input.length) input.click();

						var anchor = row.find('a[href="'+$(this).attr('data-url')+'"]');
						if(anchor.length) iframe.attr('src', iframe.attr('src') + anchor.attr('href'));
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

		_saveModal: function () {
			this.modal.find('iframe').contents().find('form').submit();
		},

		_changeModalContent: function (el) {
			var that = this;

			if(el.hasClass('cms_modal-breadcrumb-last')) return false;

			var parents = el.parent().find('a');
				parents.removeClass('cms_modal-breadcrumb-last');

			el.addClass('cms_modal-breadcrumb-last');

			// now refresh the content
			var iframe = $('<iframe src="'+el.attr('href')+'" class="" frameborder="0" />');
				iframe.hide();
			var holder = this.modal.find('.cms_modal-frame');

			// insure previous iframe is hidden
			holder.find('iframe').hide();

			// attach load event for iframe to prevent flicker effects
			iframe.bind('load', function () {
				// after iframe is loaded append css
				iframe.contents().find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.options.urls.css_modal + '" />'));

				// than show
				iframe.show();
			});

			// inject
			holder.html(iframe);

			// update title
			this.modal.find('.cms_modal-title').text(el.text());
		},

		showError: function (msg) {
			this.openMessage(msg, 'center', true);
		}

	});

});
})(CMS.$);
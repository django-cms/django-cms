/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Modal
	 * Controls a cms specific modal
	 */
	CMS.Modal = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'onClose': false,
			'minHeight': 400,
			'minWidth': 800,
			'modalDuration': 300,
			'newPlugin': false,
			'urls': {
				'css_modal': 'cms/css/cms.toolbar.modal.css'
			}
		},

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);
			this.config = CMS.config;

			// elements
			this.body = $('html');
			this.modal = $('.cms_modal');
			this.toolbar = $('.cms_toolbar');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms click.cms';
			this.maximized = false;
			this.minimized = false;
			this.triggerMaximized = false;
			this.saved = false;

			// if the modal is initialized the first time, set the events
			if(!this.modal.data('ready')) this._events();

			// ready modal
			this.modal.data('ready', true);
		},

		// initial methods
		_events: function () {
			var that = this;

			// attach events to window
			this.modal.find('.cms_modal-collapse').bind(this.click, function (e) {
				e.preventDefault();
				that._minimize();
			});
			this.modal.find('.cms_modal-title').bind('mousedown.cms', function (e) {
				e.preventDefault();
				that._startMove(e);
			});
			this.modal.find('.cms_modal-title').bind('dblclick.cms', function () {
				that._maximize();
			});
			this.modal.find('.cms_modal-resize').bind('mousedown.cms', function (e) {
				e.preventDefault();
				that._startResize(e);
			});
			this.modal.find('.cms_modal-maximize').bind(this.click, function (e) {
				e.preventDefault();
				that._maximize();
			});
			this.modal.find('.cms_modal-breadcrumb-items').on(this.click, 'a', function (e) {
				e.preventDefault();
				that._changeContent($(this));
			});
			this.modal.find('.cms_modal-close, .cms_modal-cancel').bind(this.click, function (e) {
				that.options.onClose = null;
				e.preventDefault();
				that.close();
			});

			// stopper events
			$(document).bind('mouseup.cms', function (e) {
				that._endMove(e);
				that._endResize(e);
			});
		},

		// public methods
		open: function (url, name, breadcrumb) {
			// cancel if another lightbox is already being opened
			if(CMS.API.locked) {
				CMS.API.locked = false;
				return false
			} else {
				CMS.API.locked = true;
			}

			// because a new instance is called, we have to ensure minimized state is removed #3620
			if(this.modal.is(':visible') && this.modal.find('.cms_modal-collapsed').length) {
				this.minimized = true;
				this._minimize();
			}

			// show loader
			CMS.API.Toolbar._loader(true);

			// hide tooltip
			this.hideTooltip();

			// reset breadcrumb
			this.modal.find('.cms_modal-breadcrumb').hide();
			this.modal.find('.cms_modal-breadcrumb-items').html('');

			// empty buttons
			this.modal.find('.cms_modal-buttons').html('');

			var contents = this.modal.find('.cms_modal-body, .cms_modal-foot');
				contents.show();

			this._loadContent(url, name);

			// insure modal is not maximized
			if(this.modal.find('.cms_modal-collapsed').length) this._minimize();

			// reset styles
			this.modal.css({
				'left': '50%',
				'top': '50%',
				'mergin-left': 0,
				'margin-right': 0
			});
			// lets set the modal width and height to the size of the browser
			var widthOffset = 300; // adds margin left and right
			var heightOffset = 350; // adds margin top and bottom;
			var screenWidth = $(window).width(); // it has to be the height of the window not computer screen
			var screenHeight = $(window).height(); // it has to be the height of the window and not computer screen

			var width = (screenWidth >= this.options.minWidth + widthOffset) ? screenWidth - widthOffset : this.options.minWidth;
			var height = (screenHeight >= this.options.minHeight + heightOffset) ? screenHeight - heightOffset : this.options.minHeight;
			this.modal.find('.cms_modal-body').css({
				'width': width,
				'height': height
			});
			this.modal.find('.cms_modal-body').removeClass('cms_loader');
			this.modal.find('.cms_modal-maximize').removeClass('cms_modal-maximize-active');
			this.maximized = false;
			// in case, the window is larger than the windows height, we trigger fullscreen mode
			if(height >= screenHeight) this.triggerMaximized = true;

			// we need to render the breadcrumb
			this._setBreadcrumb(breadcrumb);

			// display modal
			this._show(this.options.modalDuration);
		},

		close: function () {
			var that = this;
			// handle remove option when plugin is new
			if(this.options.newPlugin) {
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
			if(this.options.onClose) this.reloadBrowser(this.options.onClose, false, true);

			// reset maximize or minimize states for #3111
			setTimeout(function () {
				if(that.minimized) { that._minimize(); }
				if(that.maximized) { that._maximize(); }
			}, 300);
		},

		// private methods
		_show: function (speed) {
			// we need to position the modal in the center
			var that = this;
			var width = this.modal.width();
			var height = this.modal.height();

			// animates and sets the modal
			this.modal.show().css({
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

				// hide loader
				CMS.API.Toolbar._loader(false);

				// check if we should maximize
				if(that.triggerMaximized) that._maximize();

				// changed locked status to allow other modals again
				CMS.API.locked = false;
			});

			// prevent scrolling
			this.preventScroll(true);

			// add esc close event
			$(document).bind('keydown.cms', function (e) {
				if(e.keyCode === 27) that.close();
			});

			// set focus to modal
			this.modal.focus();
		},

		_hide: function (speed) {
			this.modal.fadeOut(speed);
			this.modal.find('.cms_modal-frame iframe').remove();
			this.modal.find('.cms_modal-body').removeClass('cms_loader');
			// prevent scrolling
			this.preventScroll(false);
		},

		_minimize: function () {
			var trigger = this.modal.find('.cms_modal-collapse');
			var maximize = this.modal.find('.cms_modal-maximize');
			var contents = this.modal.find('.cms_modal-body, .cms_modal-foot');
			var title = this.modal.find('.cms_modal-title');

			// cancel action if maximized
			if(this.maximized) return false;

			if(this.minimized === false) {
				// ensure toolbar is shown
				CMS.API.Toolbar.toggleToolbar(true);

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
					'top': (this.config.debug) ? 6 : 1,
					'margin': 0
				});

				// enable scrolling
				this.body.css('overflow', '');

				// ensure maximize element is hidden #3111
				maximize.hide();
				// set correct cursor when maximized #3111
				title.css('cursor', 'default');

				this.minimized = true;
			} else {
				// minimize
				trigger.removeClass('cms_modal-collapsed');
				contents.show();

				// reattach css
				this.modal.css(this.modal.data('css'));

				// disable scrolling
				this.body.css('overflow', 'hidden');

				// ensure maximize element is shown #3111
				maximize.show();
				// set correct cursor when maximized #3111
				title.css('cursor', 'move');

				this.minimized = false;
			}
		},

		_maximize: function () {
			var debug = (this.config.debug) ? 5 : 0;
			var container = this.modal.find('.cms_modal-body');
			var minimize = this.modal.find('.cms_modal-collapse');
			var trigger = this.modal.find('.cms_modal-maximize');
			var title = this.modal.find('.cms_modal-title');

			// cancel action when minimized
			if(this.minimized) return false;

			if(this.maximized === false) {
				// maximize
				this.maximized = true;
				trigger.addClass('cms_modal-maximize-active');

				this.modal.data('css', {
					'left': this.modal.css('left'),
					'top': this.modal.css('top'),
					'margin-left': this.modal.css('margin-left'),
					'margin-top': this.modal.css('margin-top')
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

				// ensure maximize element is hidden #3111
				minimize.hide();
				// set correct cursor when maximized #3111
				title.css('cursor', 'default');
			} else {
				// minimize
				this.maximized = false;
				trigger.removeClass('cms_modal-maximize-active');

				$(window).unbind('resize.cms.modal');

				// reattach css
				this.modal.css(this.modal.data('css'));
				container.css(container.data('css'));

				// ensure maximize element is shown #3111
				minimize.show();
				// set correct cursor when maximized #3111
				title.css('cursor', 'move');
			}
		},

		_startMove: function (initial) {
			// cancel if maximized
			if(this.maximized) return false;
			// cancel action when minimized
			if(this.minimized) return false;

			var that = this;
			var position = that.modal.position();

			this.modal.find('.cms_modal-shim').show();

			$(document).bind('mousemove.cms', function (e) {
				var left = position.left - (initial.pageX - e.pageX);
				var top = position.top - (initial.pageY - e.pageY);

				that.modal.css({
					'left': left,
					'top': top
				});
			});
		},

		_endMove: function () {
			this.modal.find('.cms_modal-shim').hide();

			$(document).unbind('mousemove.cms');
		},

		_startResize: function (initial) {
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

		_endResize: function () {
			this.modal.find('.cms_modal-shim').hide();

			$(document).unbind('mousemove.cms');
		},

		_setBreadcrumb: function (breadcrumb) {
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

		_setButtons: function (iframe) {
			var djangoSuit = iframe.contents().find('.suit-columns').length > 0;
			var that = this;
			var row;
			if (!djangoSuit) {
				row = iframe.contents().find('.submit-row:eq(0)');
			} else {
				row = iframe.contents().find('.save-box:eq(0)');
			}
			row.hide(); // hide submit-row
			var buttons = row.find('input, a, button');
			var render = $('<span />'); // seriously jquery...

			// if there are no given buttons within the submit-row area
			// scan deeper within the form itself
			if(!buttons.length) {
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
				if(item.attr('type') === 'hidden') return false;

				// create helper variables
				var title = item.attr('value') || item.text();
				var cls = 'cms_btn';

				// set additional special css classes
				if(item.hasClass('default')) cls = 'cms_btn cms_btn-action';
				if(item.hasClass('deletelink')) cls = 'cms_btn cms_btn-caution';

				// create the element and attach events
				var el = $('<div class="'+cls+' '+item.attr('class')+'">'+title+'</div>');
					el.bind(that.click, function () {
						if(item.is('input') || item.is('button')) item[0].click();
						if(item.is('a')) that._loadContent(item.prop('href'), title);

						// trigger only when blue action buttons are triggered
						if(item.hasClass('default') || item.hasClass('deletelink')) {
 							that.options.newPlugin = null;
 							// reset onClose when delete is triggered
							if(item.hasClass('deletelink')) that.options.onClose = null;
							// hide iframe
							that.modal.find('.cms_modal-frame iframe').hide();
							// page has been saved or deleted, run checkup
							that.saved = true;
						}
					});

				// append element
				render.append(el);
			});

			// manually add cancel button at the end
			var cancel = $('<div class="cms_btn">'+that.config.lang.cancel+'</div>');
				cancel.bind(that.click, function () {
					that.options.onClose = false;
					that.close();
				});
			render.append(cancel);

			// render buttons
			this.modal.find('.cms_modal-buttons').html(render);
		},

		_loadContent: function (url, name) {
			var that = this;

			// FIXME: A better fix is needed for '&' being interpreted as the
			// start of en entity by jQuery. See #3404
			url = url.replace('&', '&amp;');
			// now refresh the content
			var iframe = $('<iframe src="'+url+'" class="" frameborder="0" />');
				iframe.css('visibility', 'hidden');
			var holder = this.modal.find('.cms_modal-frame');

			// set correct title
			var title = this.modal.find('.cms_modal-title');
				title.html(name || '&nbsp;');

			// ensure previous iframe is hidden
			holder.find('iframe').css('visibility', 'hidden');

			// attach load event for iframe to prevent flicker effects
			iframe.bind('load', function () {
				// check if iframe can be accessed
				try {
					iframe.contents();
				} catch (error) {
					CMS.API.Toolbar.showError('<strong>' + error + '</strong>');
					that.close();
				}

				// show messages in toolbar if provided
				var messages = iframe.contents().find('.messagelist li');
					if(messages.length) CMS.API.Toolbar.openMessage(messages.eq(0).text());
					messages.remove();
				var contents = iframe.contents();

				// determine if we should close the modal or reload
				if(messages.length && that.enforceReload) that.reloadBrowser();
				if(messages.length && that.enforceClose) {
					that.close();
					return false;
				}

				// after iframe is loaded append css
				contents.find('head').append($('<link rel="stylesheet" type="text/css" href="' + that.config.urls.static + that.options.urls.css_modal + '" />'));

				// adding django hacks
				contents.find('.viewsitelink').attr('target', '_top');

				// set modal buttons
				that._setButtons($(this));

				// when an error occurs, reset the saved status so the form can be checked and validated again
				if(iframe.contents().find('.errornote').length || iframe.contents().find('.errorlist').length) {
					that.saved = false;
				}

				// when the window has been changed pressing the blue or red button, we need to run a reload check
				// also check that no delete-confirmation is required
				if(that.saved && !contents.find('.delete-confirmation').length) {
					that.reloadBrowser(window.location.href, false, true);
				} else {
					iframe.show();
					// set title of not provided
					var innerTitle = iframe.contents().find('#content h1:eq(0)');
					if(name === undefined) title.html(innerTitle.text());
					innerTitle.remove();

					// than show
					iframe.css('visibility', 'visible');

					// append ready state
					iframe.data('ready', true);

					// attach close event
					contents.find('body').bind('keydown.cms', function (e) {
						if(e.keyCode === 27) that.close();
					});
					contents.find('body').addClass('cms_modal-window');

					// figure out if .object-tools is available
					if(contents.find('.object-tools').length) {
						contents.find('#content').css('padding-top', 38);
					}
				}
			});

			// inject
			setTimeout(function () {
				that.modal.find('.cms_modal-body').addClass('cms_loader');
				holder.html(iframe);
			}, this.options.modalDuration);
		},

		_changeContent: function (el) {
			if(el.hasClass('cms_modal-breadcrumb-last')) return false;

			var parents = el.parent().find('a');
				parents.removeClass('cms_modal-breadcrumb-last');

			el.addClass('cms_modal-breadcrumb-last');

			this._loadContent(el.attr('href'));

			// update title
			this.modal.find('.cms_modal-title').text(el.text());
		}

	});

});
})(CMS.$);

/**
 * @author		Angelo Dini
 * @copyright	http://www.divio.ch under the BSD Licence
 * @requires	Classy, jQuery
 *
 * check if classy.js exists */
 if(window['Class'] === undefined) log('classy.js is required!');

/* needs to be rewritten */
function hide_iframe() { CMS.Placeholders.toggleFrame(); CMS.Placeholders.reloadBrowser(); }

/*##################################################|*/
/* #CUSTOM APP# */
(function ($, Class) {
	/**
	 * Toolbar
	 * @version: 0.0.1
	 * @description: Handles placeholders when in editmode
	 	and adds "lightbox" to toolbar
	 */
	CMS.Placeholders = Class.$extend({

		options: {
			'edit_mode': false,
			'page_is_defined': false
		},

		initialize: function (container, options) {
			// save reference to this class
			var classy = this;
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save toolbar elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.dim = this.wrapper.find('#cms_placeholder-dim');
			this.frame = this.wrapper.find('#cms_placeholder-content');
			this.timer = function () {};
			this.overlay = this.wrapper.find('#cms_placeholder-overlay');
			
			// save placeholder elements
			if(this.options.editmode) {
				this.bars = $('.cms_placeholder-bar');
				this.bars.each(function (index, item) {
					classy._bars.call(classy, item);
				});
				
				// enable dom traversal for cms_placeholder
				this.holders = $('.cms_placeholder');
				this.holders.bind('mouseenter', function (e) {
					classy._holder.call(classy, e.currentTarget);
				});
			}
			
			// setup everything
			this._setup();
		},
		
		_setup: function () {
			// save reference to this class
			var classy = this;
			
			// set default dimm value to false
			this.toolbar.data('dimmed', false)
			
			// set defailt frame value to true
			this.frame.data('collapsed', true);
			
			// bind overlay event
			this.overlay.bind('mouseleave', function () {
				classy._hideOverlay();
			});
			// this is for testing
			this.overlay.bind('click', function () {
				classy._hideOverlay();
				
				// when clicking the mouseenter event should be canceled until
				// you enter the event again (outbound)
			});
		},
		
		/* this private method controls the buttons on the bar (add plugins) */
		_bars: function (el) {
			// save reference to this class
			var classy = this;
			var bar = $(el);
			
			// attach button event
			var barButton = bar.find('.cms_toolbar-btn');
				barButton.data('collapsed', true).bind('click', function (e) {
					e.preventDefault();
					
					($(this).data('collapsed')) ? classy._showPluginList.call(classy, $(e.currentTarget)) : classy._hidePluginList.call(classy, $(e.currentTarget));
				});
			
			// read and save placeholder bar variables
			var values = bar.attr('class').split('::');
				values.shift(); // remove classes
				values = {
					'language': values[0],
					'placeholder_id': values[1],
					'placeholder': values[2]
				};
			
			// attach events to placeholder plugins
			bar.find('.cms_placeholder-subnav li a').bind('click', function (e) {
				e.preventDefault();
				// add type to values
				values.plugin_type = $(this).attr('rel').split('::')[1];
				// try to add a new plugin
				classy.addPlugin.call(classy, classy.options.urls.cms_page_add_plugin, values);
			});
		},
		
		/* this private method shows the overlay when hovering */
		_holder: function (el) {
			// save reference to this class
			var classy = this;
			var holder = $(el);
			
			// show overlay
			this._showOverlay.call(classy, holder);
			
			// get values
			var values = holder.attr('class').split('::');
				values.shift(); // remove classes
				values = {
					'plugin_id': values[0],
					'placeholder': values[1],
					'type': values[2],
					'slot': values[3]
				};
			
			var buttons = this.overlay.find('.cms_placeholder-options li');
				// unbind all button events
				buttons.find('a').unbind('click');
				
				// attach edit event
				buttons.find('a[rel^=edit]').bind('click', function (e) {
					e.preventDefault();
					classy.editPlugin.call(classy, values.placeholder, values.plugin_id);
				});
				
				// attach delete event
				buttons.find('a[rel^=settings]').bind('click', function (e) {
					e.preventDefault();
					classy.deletePlugin.call(classy, values.placeholder, values.plugin_id);
				});
				
				// attach move event
				buttons.find('a[rel^=moveup]').bind('click', function (e) {
					e.preventDefault();
					
					// wee need to somehow determine if we can move the selected plugin up
					// so how the fuck are we gonna do that...
					// so holder is the current holder. lets check if we find any other placeholders
					// now lets get the current id, if its 0 (means top) we do not need to do a shit
					var index = holder.parent().find('.cms_placeholder').index(holder);
					
					// if there is no other element on top cancel the move event
					if(index == 0) { alert(classy.options.lang.move_warning); return false; }
					
					// now we passed so lets get the data for the element next to it
					var target = $(holder.parent().find('.cms_placeholder')[index-1]).attr('class').split('::');
						target.shift();
					
					classy.movePlugin.call(classy, {
						'placeholder_id': values.placeholder,
						'plugin_id': values.plugin_id,
						'slot_id': values.slot
					}, {
						'placeholder_id': target[1],
						'plugin_id': target[0],
						'slot_id': target[3]
					});
				});
			},
		
		addPlugin: function (url, data) {
			var classy = this;
			// do ajax thingy
			$.ajax({
				'type': 'POST',
				'url': url,
				'data': data,
				'success': function (response) {
					// we get the id back
					classy.editPlugin.call(classy, data.placeholder_id, response);
				},
				'error': function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});
		},
		
		editPlugin: function (placeholder_id, plugin_id) {
			var classy = this;
			var frame = this.frame.find('.cms_placeholder-content_inner');
			
			// show framebox
			CMS.Placeholders.toggleFrame();
			
			// load the template through the data id
			// for that we create an iframe with the specific url
			var iframe = $('<iframe />', {
				'id': 'cms_placeholder-iframe',
				'src': classy.options.urls.cms_page_changelist + placeholder_id + '/edit-plugin/' + plugin_id + '?popup=true&no_preview',
				'style': 'width:100%; height:50px; border:none; overflow:hidden;', // 100px = displayed bigger butt positioning works, needs fix
				'allowtransparency': true,
				'scrollbars': 'no',
				'frameborder': 0
			});
			
			// inject to element
			frame.html(iframe);
			
			// bind load event to injected iframe
			// lets set the correct height for the frame
			$('#cms_placeholder-iframe').load(function () {
				//$(document.body).css('overflow', 'hidden');
				
				// set new height and animate
				var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true);
				$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				
				// resize window after animation
				setTimeout(function () {
					$(window).resize();
					//$(document.body).css('overflow', 'auto');
				}, 501);
				
				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		},
		
		deletePlugin: function (placeholder_id, plugin_id) {
			var classy = this;
			// lets ask if you are sure
			var message = this.options.lang.delete_request;
			var confirmed = confirm(message, true);
			
			// now do ajax
			if(confirmed) {
				$.ajax({
					'type': 'POST',
					'url': this.options.urls.cms_page_remove_plugin,
					'data': { 'plugin_id': plugin_id },
					'success': function (response) {
						// refresh
						classy.reloadBrowser();
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			}
		},
		
		movePlugin: function (plugin, target) {
			// move plugin to certain position - will also be used for dragNdrop
			
			// jonas should do some shit here cause the implementation works with arrays at the moment
			// so i have to check that with him
			
			log('old location');
			log(plugin);
			
			log('new location');
			log(target);
			
			// i need to say what plugin should be moved and where exactly
			// so there is a plugin object and a target object
		},
		
		_showOverlay: function (holder) {
			// lets place the overlay
			this.overlay.css({
				'width': holder.width()-2,
				'height': holder.height()-2,
				'left': holder.offset().left,
				'top': holder.offset().top
			});
			
			// and now show it
			this.overlay.show();
		},
		
		_hideOverlay: function () {
			// hide overlay again
			this.overlay.hide();
		},
		
		_showPluginList: function (el) {
			// save reference to this class
			var classy = this;
			var list = el.parent().find('.cms_placeholder-subnav');
				list.show();
			
			// add event to body to hide the list needs a timout for late trigger
			setTimeout(function () {
				$(window).bind('click', function () {
					classy._hidePluginList.call(classy, el);
				});
			}, 100);
			
			el.addClass('cms_toolbar-btn-active').data('collapsed', false);
		},
		
		_hidePluginList: function (el) {
			var list = el.parent().find('.cms_placeholder-subnav');
				list.hide();
			
			// remove the body event
			$(window).unbind('click');
			
			el.removeClass('cms_toolbar-btn-active').data('collapsed', true);
		},
		
		toggleFrame: function () {
			(this.frame.data('collapsed')) ? this._showFrame() : this._hideFrame();
			
			// show dimmer
			this.toggleDim();
			
			// we need to make sure that the toolbar is visible when showing the frame
		},
		
		_showFrame: function () {
			var classy = this;
			// show frame
			this.frame.fadeIn();
			// change data information
			this.frame.data('collapsed', false);
		},
		
		_hideFrame: function () {
			// hide frame
			this.frame.fadeOut();
			// change data information
			this.frame.data('collapsed', true);
			// there needs to be a function to unbind the loaded content and reset to loader
			this.frame.find('.cms_placeholder-content_inner')
				.addClass('cms_placeholder-content_loader')
				.html('');
		},

		toggleDim: function () {
			(this.toolbar.data('dimmed')) ? this._hideDim() : this._showDim();
		},
		
		_showDim: function () {
			var classy = this;
			clearTimeout(this.timer);
			// attach resize event to window
			$(window).bind('resize', function () {
				classy.dim.css({
					'width': $(window).width(),
					'height': $(window).height(),
				});
				classy.frame.css('width', $(window).width());
				// adjust after resizing
				classy.timer = setTimeout(function () {
					classy.dim.css({
						'width': $(window).width(),
						'height': $(document).height()
					});
					classy.frame.css('width', $(window).width());
				}, 100);
			});
			// init dim resize
			$(window).resize();
			// change data information
			this.toolbar.data('dimmed', true);
			// show dim
			this.dim.stop().fadeIn();
			// add event to dim to hide
			this.dim.bind('click', function (e) {
				classy.toggleFrame.call(classy);
			});
		},
		
		_hideDim: function () {
			// unbind resize event
			$(window).unbind('resize');
			// change data information
			this.toolbar.data('dimmed', false);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
			// remove dim event
			this.dim.unbind('click');
		},
		
		reloadBrowser: function () {
			window.location.reload();
		}
		
	});
})(jQuery, Class);
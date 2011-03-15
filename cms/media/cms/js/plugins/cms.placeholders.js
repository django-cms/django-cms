/**
 * @author		Angelo Dini
 * @copyright	http://www.divio.ch under the BSD Licence
 * @requires	Classy, jQuery
 *
 * check if classy.js exists */
 if(window['Class'] === undefined) log('classy.js is required!');

/*##################################################|*/
/* #CUSTOM APP# */
(function ($, Class) {
	/**
	 * Toolbar
	 * @version: 0.0.1
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
				this.holders.each(function (index, item) {
					classy._holder.call(classy, item);
				});
			}
			
			// setup everything
			this._setup();
		},
		
		_setup: function () {
			// set default dimm value to false
			this.toolbar.data('dimmed', false)
			
			// set defailt frame value to true
			this.frame.data('collapsed', true);
		},
		
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
			var values = bar.attr('class');
				values = values.split('::');
				values.shift(); // remove classes
				values = {
					language: values[0],
					page_id: values[1],
					placeholder: values[2]
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
		
		_holder: function (el) {
			// save reference to this class
			var classy = this;
			var holder = $(el);
				holder.bind('mouseenter mouseleave', function (e) {
					//(e.type == 'mouseenter') ? classy._showOverlay.call(classy, holder) : classy._hideOverlay.call(classy, holder);
					if(e.type == 'mouseenter') classy._showOverlay.call(classy, holder);
				});
		},
		
		_showOverlay: function (holder) {
			// get al the variables from holder
			var values = holder.attr('class');
				values = values.split('::');
				values.shift(); // remove classes
				values = {
					plugin_id: values[0],
					placeholder: values[1],
					type: values[2],
					slot: values[3]
				};
			
			log(this.overlay);
			// lets place the overlay
			this.overlay.css({
				width: holder.width(),
				height: holder.height()
			});
			
			// and now show it
			this.overlay.show();
		},
		
		_hideOverlay: function (holder) {
			//log('hide');
			
			// hide overlay again
			//this.overlay.hide();
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
						'width': $(document).width(),
						'height': $(document).height(),
					});
					classy.frame.css('width', $(document).width());
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
				classy.toggleDim.call(classy);
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
		
		toggleFrame: function () {
			(this.frame.data('collapsed')) ? this._showFrame() : this._hideFrame();
		},
		
		_showFrame: function () {
			var classy = this;
			// show frame
			this.frame.fadeIn();
			// change data information
			this.frame.data('collapsed', false);
			// show dimmer
			this._showDim();
		},
		
		_hideFrame: function () {
			// hide frame
			this.frame.fadeOut();
			// change data information
			this.frame.data('collapsed', true);
			// hide dimmer
			this._hideDim();
			// there needs to be a function to unbind the loaded content and reset to loader
			this.frame.find('.cms_placeholder-content_inner')
				.addClass('cms_placeholder-content_loader')
				.html('');
		},
		
		addPlugin: function (url, data) {
			var classy = this;
			// do ajax thingy
			$.ajax({
				'type': 'POST',
				'url': url,
				'data': data,
				success: function (response) {
					// we get the id back
					classy.editPlugin.call(classy, data.page_id, response);
				},
				error: function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});
		},
		
		editPlugin: function (page_id, plugin_id) {
			var classy = this;
			var frame = this.frame.find('.cms_placeholder-content_inner');
			// show framebox
			CMS.Placeholders.toggleFrame();
			
			// load the template through the data id
			// for that we create an iframe with the specific url
			var iframe = $('<iframe />', {
				id: 'cms_placeholder-iframe',
				src: classy.options.urls.cms_page_changelist + page_id + '/edit-plugin/' + plugin_id + '?popup=true&no_preview',
				style: 'width:100%; height:100px; border:none; overflow:hidden;',
				allowtransparency: true,
				scrollbars: 'no',
				frameborder: 0
			});
			
			// inject to element
			frame.html(iframe);
			
			// lets set the correct height for the frame
			$('#cms_placeholder-iframe').load(function () {
				$(document.body).css('overflow', 'hidden');
				
				// set new height and animate
				var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true);
				$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				
				// resize window after animation
				setTimeout(function () {
					$(window).resize();
					$(document.body).css('overflow', 'auto');
				}, 501);
				
				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		}

	});
})(jQuery, Class);
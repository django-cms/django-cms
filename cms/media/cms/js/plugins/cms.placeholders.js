/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery, jQuery.ui.core, jQuery.ui.draggable, jQuery.ui.droppable
 *
 * assign Class and CMS namespace */
 var Class = Class || {};
 var CMS = CMS || {};

/*##################################################|*/
/* #CUSTOM APP# */
jQuery(document).ready(function ($) {
	/**
	 * Placeholders
	 * @version: 0.1.0
	 * @description: Handles placeholders when in editmode and adds "lightbox" to toolbar
	 * @public_methods:
	 *	- CMS.Placeholder.addPlugin(url, obj);
	 *	- CMS.Placeholder.editPlugin(placeholder_id, plugin_id);
	 *	- CMS.Placeholder.deletePlugin(placeholder_id, plugin_id);
	 *	- CMS.Placeholder.movePlugin(plugin, target);
	 *	- CMS.Placeholder.toggleFrame();
	 *	- CMS.Placeholder.toggleDim();
	 */
	CMS.Placeholders = Class.$extend({

		options: {
			'edit_mode': false,
			'compact_mode': false,
			'page_is_defined': false, // TODO: figure out why thats needed
			'lang': {
				'move_slot': '',
				'move_warning': '',
				'delete_request': ''
			},
			'urls': {
				'cms_page_move_plugin': '',
				'cms_page_changelist': '',
				'cms_page_change_template': '',
				'cms_page_add_plugin': '',
				'cms_page_remove_plugin': ''
			}
		},

		initialize: function (container, options) {
			// save reference to this class
			var classy = this;
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save placeholder elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.dim = this.wrapper.find('#cms_placeholder-dim');
			this.frame = this.wrapper.find('#cms_placeholder-content');
			this.timer = function () {};
			this.overlay = this.wrapper.find('#cms_placeholder-overlay');
			this.overlayIsHidden = false;
			
			// attach event handling to placeholder buttons and overlay if editmode is active
			if(this.options.edit_mode) {
				this.bars = $('.cms_placeholder-bar');
				this.bars.each(function (index, item) {
					classy._bars.call(classy, item);
				});
				
				// enable dom traversal for cms_placeholder
				this.holders = $('.cms_placeholder');
				this.holders.bind('mouseenter', function (e) {
					classy._holder.call(classy, e.currentTarget);
				});
				
				this._initDrag();
			}
			
			// setup everything
			this._setup();
		},
		
		_setup: function () {
			// save reference to this class
			var classy = this;
			
			// set default dimm value to false
			this.dim.data('dimmed', false);
			
			// set defailt frame value to true
			this.frame.data('collapsed', true);
			
			// bind overlay event
			this.overlay.bind('mouseleave', function () {
				classy._hideOverlay();
			});
			// this is for testing
			this.overlay.bind('click', function () {
				classy._hideOverlay();
				
				// we need to hide the oberlay and stop the event for a while
				classy.overlay.css('visibility', 'hidden');
				
				// add timer to show element after second mouseenter
				setTimeout(function () {
					classy.overlayIsHidden = true;
				}, 100);
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
			var split = bar.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'language': split[0],
					'placeholder_id': split[1],
					'placeholder': split[2]
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
			
			// set overlay to visible
			if(this.overlayIsHidden === true) {
				this.overlay.css('visibility', 'visible');
				this.overlayIsHidden = false;
			}
			
			// get values
			var split = holder.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'plugin_id': split[0],
					'placeholder': split[1],
					'type': split[2],
					'slot': split[3]
				};

			// TODO: find better way to implement this
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

					// TODO: add less docs to this description
					// wee need to somehow determine if we can move the selected plugin up
					// so how the fuck are we gonna do that...
					// so holder is the current holder. lets check if we find any other placeholders
					// now lets get the current id, if its 0 (means top) we do not need to do a shit
					var index = holder.parent().find('.cms_placeholder').index(holder);
					
					// if there is no other element on top cancel the move event
					if(index === 0) { alert(classy.options.lang.move_warning); return false; }
					
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
		
		_initDrag: function () {
			// TODO: when dragging disable the overlay

			// we need to active the drag and drop somehwere using jquery ui
			// so lets get all the containers and containing elements
			
			
			// al the items should be draggable
			var items = $('.cms_placeholder');
			// the placeholders define the header (containing container)
			// we probably need to add a wrapping div there to define the boundary
			//var placeholders = $('.cms_placeholder-bar');

            //log(placeholder);
			
			// lets add the drag event
			items.draggable({
				
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
			CMS.Placeholders.toggleDim();
			
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
			$('#cms_placeholder-iframe').load(function () {
				// set new height and animate
				var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true);
				$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				
				// resize window after animation
				setTimeout(function () {
					$(window).resize();
				}, 501);
				
				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		},
		
		deletePlugin: function (placeholder_id, plugin_id) {
			// lets ask if you are sure
			var message = this.options.lang.delete_request;
			var confirmed = confirm(message, true);
			
			// now do ajax
			if(confirmed) {
				$.ajax({
					'type': 'POST',
					'url': this.options.urls.cms_page_remove_plugin,
					'data': { 'plugin_id': plugin_id },
					'success': function () {
						// refresh
						CMS.Helpers.reloadBrowser();
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			}
		},
		
		movePlugin: function (plugin, target) {
			// TODO: this method does not work yet
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
		},
		
		_showFrame: function () {
			var classy = this;
			// show frame
			this.frame.fadeIn();
			// change data information
			this.frame.data('collapsed', false);
			// frame should always have space on top
			this.frame.css('top', 43);
			// make sure that toolbar is visible
			if(this.toolbar.data('collapsed')) CMS.Toolbar._showToolbar();
			// listen to toolbar events
			this.toolbar.bind('cms.toolbar.show cms.toolbar.hide', function (e) {
				(e.handleObj.namespace === 'show.toolbar') ? classy.frame.css('top', 43) : classy.frame.css('top', 0);
			});
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
			// remove toolbar events
			this.toolbar.unbind('cms.toolbar.show cms.toolbar.hide');
		},

		toggleDim: function () {
			(this.dim.data('dimmed')) ? this._hideDim() : this._showDim();
		},
		
		_showDim: function () {
			var classy = this;
			clearTimeout(this.timer);
			// attach resize event to window
			$(window).bind('resize', function () {
				classy.dim.css({
					'width': $(window).width(),
					'height': $(window).height()
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
			this.dim.data('dimmed', true);
			// show dim
			this.dim.stop().fadeIn();
			// add event to dim to hide
			this.dim.bind('click', function () {
				classy.toggleFrame.call(classy);
				classy.toggleDim.call(classy);
			});
		},
		
		_hideDim: function () {
			// unbind resize event
			$(window).unbind('resize');
			// change data information
			this.dim.data('dimmed', false);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
			// remove dim event
			this.dim.unbind('click');
		}
		
	});
});

/* needs to be changed to CMS namespace */
function hide_iframe() {
	CMS.Placeholders.toggleFrame();
	CMS.Placeholders.toggleDim();
	CMS.Helpers.reloadBrowser();
}
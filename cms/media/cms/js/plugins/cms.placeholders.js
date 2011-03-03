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
			'page_is_defined': false,
			'edit_mode': false
		},

		initialize: function (container, options) {
			// save reference to this class
			var classy = this;
			// check if only one element is found
			if($(container).length > 2) { log('Toolbar Error: one element expected, multiple elements given.'); return false; }
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save toolbar elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.toolbar.left = this.toolbar.find('.cms_toolbar-left');
			this.toolbar.right = this.toolbar.find('.cms_toolbar-right');
			this.dim = this.wrapper.find('#cms_toolbar-dim');
			
			// bind event to toggle button
			this.toggle = this.wrapper.find('#cms_toolbar-toggle');
			this.toggle.bind('click', function (e) {
				e.preventDefault();
				classy.toggleToolbar();
			});
			
			// csrf security patch
			patchCsrf(jQuery);
			
			// initial setups
			this._setup();
		},
		
		_setup: function () {
			// set if toolbar is visible or not
			($.cookie('CMS_toolbar-collapsed') == 'false') ? this.toolbar.data('collapsed', true) : this.toolbar.data('collapsed', false);
			
			// init scripts
			this.toggleToolbar();
			
			// show toolbar
			this.wrapper.show();
		}

	});
})(jQuery, Class);
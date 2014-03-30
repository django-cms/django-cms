/*##################################################|*/
/* #CMS.API# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {

	var appHooks = $('#application_urls'),
		selected = appHooks.find('option:selected'),
		appNsRow = $('.form-row.application_namespace'),
		appNs = appNsRow.find('#id_application_namespace'),
		original_ns = appNs.val();

	// Hide the namespace widget if its not required.
	appNsRow.toggleClass('hidden', !selected.data('namespace'));

	// Show it if we change to an app_hook that requires a namespace
	appHooks.on('change', function(){
		var self = $(this),
			opt = self.find('option:selected');

		appNsRow.toggleClass('hidden', !opt.data('namespace'));

		// If we clear the app_hook, clear out the app_namespace too
		if (!self.val()) {
			appNs.val('');
			appNs.removeAttr('value');
		}

		// When we choose one that does NOT require a namespace, then make
		// sure we reset to the previously set value, if any.
		if (!opt.data('namespace')){
			appNs.val(original_ns);
		}

		// If nothing was previously there, suggest the default, if
		// applicable.
		if (!original_ns && opt.data('namespace')) {
			appNs.val(opt.data('namespace'));
		}
	});
});
})(CMS.$);
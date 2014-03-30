/*##################################################|*/
/* #CMS# */

// ensuring django namespace is set correctly
window.django = window.django || undefined;

// ensuring jQuery namespace is set correctly
window.jQuery = (django) ? django.jQuery : window.jQuery || undefined;

// ensuring Class namespace is set correctly
window.Class = window.Class || undefined;

// ensuring CMS namespace is set correctly
var CMS = {
	'$': (jQuery) ? jQuery.noConflict() : undefined,
	'Class': (Class) ? Class.noConflict() : undefined,
	'API': {}
};

/*##################################################|*/
/* #CMS.API# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {

	var $app_hooks = $('#application_urls'),
		$selected = $app_hooks.find('option:selected'),
		$app_ns_row = $('.form-row.application_namespace'),
		$app_ns = $app_ns_row.find('#id_application_namespace'),
		original_ns = $app_ns.val();

	// Hide the namespace widget if its not required.
	$app_ns_row.toggleClass('hidden', !$selected.data('namespace'));

	// Show it if we change to an app_hook that requires a namespace
	$app_hooks.on('change', function(){
		var $this = $(this),
			$opt = $this.find('option:selected');

		$app_ns_row.toggleClass('hidden', !$opt.data('namespace'));

		// When we choose one that does NOT require a namespace, then make
		// sure we reset to the previously set value, if any.
		if (!$opt.data('namespace')){
			$app_ns.val(original_ns);
		}

		// If nothing was previously there, suggest the default, if
		// applicable.
		if (!original_ns && $opt.data('namespace')) {
			$app_ns.val($opt.data('namespace'));
		}
	});
});
})(CMS.$);
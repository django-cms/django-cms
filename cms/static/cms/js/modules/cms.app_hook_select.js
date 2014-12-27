/*##################################################|*/
/* #CMS.API# */
/* global apphooks_configuration */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {

	var appHooks = $('#application_urls'),
		selected = appHooks.find('option:selected'),
		appNsRow = $('.form-row.application_namespace'),
		appNs = appNsRow.find('#id_application_namespace'),
		appCfgsRow = $('.form-row.application_configs'),
		appCfgs = appCfgsRow.find('#application_configs'),
		appCfgsAdd = appCfgsRow.find('#add_application_configs'),
		original_ns = appNs.val();

	// Shows / hides namespace / config selection widgets depending on the user input
	appHooks.setupNamespaces = function() {
		var opt = $(this).find('option:selected');

		if(apphooks_configuration[opt.val()]){
			for(var i=0; i < apphooks_configuration[opt.val()].length; i++) {
				appCfgs.append('<option value="' + apphooks_configuration[opt.val()][i][0] + '">' + apphooks_configuration[opt.val()][i][1] + '</option>')
			}
			appCfgsAdd.attr('href', apphooks_configuration_url[opt.val()]);
			appCfgsRow.removeClass('hidden');
			appNsRow.addClass('hidden');
		}
		else {
			appCfgsRow.addClass('hidden');
			if(opt.data('namespace')) {
				appNsRow.removeClass('hidden');
			}
			else {
				appNsRow.addClass('hidden');
			}
		}
	};

	// Hide the namespace widgets if its not required.
	appHooks.setupNamespaces();

	// Show it if we change to an app_hook that requires a namespace
	appHooks.on('change', function(){
		var self = $(this);

		appHooks.setupNamespaces();

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
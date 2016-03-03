/*##################################################|*/
/* #CMS.SETUP# */
(function namespacing() {
	// insuring django namespace is available when using on admin
	django = window.django || undefined;

	// assigning correct jquery instance to jQuery variable
	var jQuery = (django) ? django.jQuery : window.jQuery || undefined;

	// assign global namespaces
	window.CMS = {
		'$': jQuery.noConflict(),
		'Class': Class.$noConflict(),
		'API': {}
	};
})();
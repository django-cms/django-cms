/*##################################################|*/
/* #CMS.SETUP# */

// insuring django namespace is available when using on admin
var django = django || undefined;

// assigning correct jquery instance to jQuery variable
var jQuery = (django) ? django.jQuery : window.jQuery || undefined;

// assign global namespaces
var CMS = {
	'$': jQuery.noConflict(),
	'Class': Class.$noConflict(),
	'API': {}
};
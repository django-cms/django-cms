/*##################################################|*/
/* #CMS.SETUP# */

// insuring django namespace is available when using on admin
var django = django || undefined;

// assigning correct jquery instance to our jQuery variable
var cmsQuery = (django) ? django.jQuery : window.jQuery || undefined;

// assign global namespaces
var CMS = {
	'$': cmsQuery.noConflict(),
	'Class': Class.$noConflict(),
	'API': {}
};
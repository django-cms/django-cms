/*##################################################|*/
/* #CMS.SETUP# */

// insuring django namespace is available when using on admin
var django = django || undefined;

// assign global namespaces
var CMS = {
	'$': (django ? django.jQuery : window.jQuery || undefined).noConflict(),
	'Class': Class.$noConflict(),
	'API': {}
};
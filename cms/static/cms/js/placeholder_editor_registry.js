/*
 * Some text editors allow plugin objects to be inserted in them.
 * The controls for this might not be part of the editor itself.
 * For these controls to be able to interact with the various editors
 * that can be used for editing text, it needs a specific javascript
 * interface (see wymeditor.placeholder.js for an example), and it
 * needs to be able to find the javascript object.  This file creates
 * a global object that is used to registor editors against the
 * fieldname that they are for.
 *
 * This registry allows multiple editors to exist in the same page.
 * If iframes are used, then there will be multiple instances of
 * PlaceholderEditorRegistry (one in each iframe), and each instance
 * will contain only object.
 */

var PlaceholderEditorRegistry = {};

jQuery.extend(PlaceholderEditorRegistry, {
	registerEditor : function(fieldname, editor) {
		PlaceholderEditorRegistry.STORE[fieldname] = editor;
	},
	retrieveEditor : function(fieldname) {
		return PlaceholderEditorRegistry.STORE[fieldname];
	},
	STORE : {}
});
/* For the django-cms PlaceholderEditor to be able to interact with
 * the various editors that can be used for editing text, it needs
 * a specific javascript interface (see wymeditor.placeholder.js for
 * an example), and it needs to be able to find the javascript object.
 * This file creates a global object that is used to registor editors
 * against the fieldname that they are for.
 */

var PlaceholderEditorRegistry = {};

jQuery.extend(PlaceholderEditorRegistry,
              {
                  registerEditor : function(fieldname, editor) {
                      PlaceholderEditorRegistry.STORE[fieldname] = editor;
                  },
                  retrieveEditor : function(fieldname) {
                      return PlaceholderEditorRegistry.STORE[fieldname];
                  },
                  STORE : {}
              });

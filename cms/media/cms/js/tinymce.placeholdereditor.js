/* Provides javascript bridge between WYMEditor and the django-cms PlaceholderEditor widget */

/*
 * The PlaceholderEditor widget allows different text editors to be used and
 * provides a javascript UI for inserting objects into the text editor.  For this
 * to work, the text editor needs to provide a javascript interface to talk to.
 * This is provided by PlaceholderBridge in this instance, but for different editors
 * a different bridge would be needed, with the same public interface.
 *
 * The PlaceholderEditor javascript needs to be able to find the javascript object
 * that provides this interface.  This is done by making a call to
 * PlaceholderEditorRegistry.registerEditor - see placeholder_editor_registry
 *
 * We also want to be able to re-use this bridge for different versions of
 * the WYMEditor, simply enabling it when the editor is created.
 */

function TinyMCEPlaceholderBridge(wym) {
    this.wym = wym;
}

TinyMCEPlaceholderBridge.prototype.insertText = function(text) {
    /* Inserts the text given at the current insertion point
     * in the text editor
     */
	tinyMCE.activeEditor.selection.setContent(text);

};

TinyMCEPlaceholderBridge.prototype.replaceContent = function(old, rep) {
    /* Replaces occurence of `old` with `new` in the editor. 
     */
	
	// todo: implement
	throw new Error("NotImplemented");
};


TinyMCEPlaceholderBridge.prototype.selectedObject = function() {
    /* If an image/object is selected, returns the HTMLImageObject for that image,
     * otherwise undefined/null.
     */

    // We rely on a private attribute that is set in 'mousedown' event
    // if the user clicks on an image. This could be fragile :-)
    return tinyMCE.activeEditor.selection.getContent();
};


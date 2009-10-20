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

function WymPlaceholderBridge(wym, opts) {
    this.wym = wym;
}

WymPlaceholderBridge.prototype.insertText = function(text) {
    /* Inserts the text given at the current insertion point
     * in the text editor
     */
    this.wym.insert(text);
};

WymPlaceholderBridge.prototype.replaceContent = function(old, rep) {
    /* Replaces occurence of `old` with `new` in the editor. 
     */
	var html = this.wym.html()
	this.wym.html(html.replace(old, rep));
};

WymPlaceholderBridge.prototype.selectedObject = function() {
    /* If an image/object is selected, returns the HTMLImageObject for that image,
     * otherwise undefined/null.
     */

    // We rely on a private attribute that is set in 'mousedown' event
    // if the user clicks on an image. This could be fragile :-)
    return this.wym._selected_image; // Returns null if no image selected.
};


/* Create plugin for the WYMEditor -- this function is called
 * when the editor is set up.
 */
WYMeditor.editor.prototype.placeholderbridge = function(options) {
    /* options must include 'name', the name of the textarea
     * that is being edited.
     */
    var wym = this;
    var c = new WymPlaceholderBridge(wym, options);
    PlaceholderEditorRegistry.registerEditor(options['name'], c);
};


/* This initialises the PlaceholderEditor controls
 */

// Global var, for storing callbacks, see below.
var editPluginPopupCallbacks = {};

// Global function, needed for popup window to call the parent via opener.dismissEditPluginPopup
function dismissEditPluginPopup(win, plugin_id, icon_src, icon_alt) {
    // This is called after user presses 'Save' in popup.
    win.close();
    var callback = editPluginPopupCallbacks[plugin_id];
    if (callback != null) {
        callback(plugin_id, icon_src, icon_alt);
    }
}

// TODO - move this html escape function somewhere nicer

function escapeHtml(html) {
    return html.replace(/&/g,"&amp;")
        .replace(/\"/g,"&quot;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;");
}


$(document).ready(function() {
    // Wire up the add/edit buttons.

    /* General functions */
    function get_editor(placeholder) {
        // Find the placeholder text editor widget
        if (typeof(PlaceholderEditorRegistry) == "undefined") {
            // This could occur if javascript defining PlaceholderEditorRegistry
            // has not been loaded for some reason.
            alert("A programming error occurred - cannot find text editor widgets.");
            return null;
        }
        return PlaceholderEditorRegistry.retrieveEditor(placeholder);
    }

    function edit_object(obj_id) {
        // Pop up window for editing object.
        window.open("edit-plugin/" + obj_id + "/?_popup=1",
                    "Edit plugin object",
                    "menubar=no,titlebar=no,toolbar=no,resizable=yes"
                      + ",width=800,height=300,top=0,left=0,scrollbars=yes"
                      + ",location=no"
                   );
    }

    function plugin_admin_html(plugin_id, icon_src, icon_alt) {
        return '<img src="' + escapeHtml(icon_src) + '" ' +
            'alt="'+ escapeHtml(icon_alt) + '" ' +
            'id="plugin_obj_' + plugin_id + '"/>';
    }

    /* onclick for 'Insert object' */
    $('span.insert-object').click(function() {
        var select = $(this).parent().children("select");
        var pluginvalue = select.attr('value');
        var placeholder = $(this).parent().parent().children("input[name=_placeholder]").attr('value');
        var page_id = window.location.href.split("/")[6]; // TODO - this seems a bit fragile...
        var language = $('#id_language').attr('value');

        if (pluginvalue == "") {
            alert(gettext("Please select a plugin type."));
            return;
        }

        var texteditor = get_editor(placeholder);
        if (texteditor == null || texteditor.insertText == null) {
            alert(gettext("Text editor does not support inserting objects."));
            return;
        }
        // First create db instance using AJAX post back
        $.post("add-plugin/",
               { page_id: page_id,
                 placeholder: placeholder,
                 plugin_type: pluginvalue,
                 language: language
               }, function(data) {
                   if ('error' != data) {
                       // Successfully created, data is pk of object, but object
                       // is 'blank'. We now want to show the edit popup.

                       // We only want to insert the text if the user actually
                       // *saved* the object.  We don't have modal dialogs, so we
                       // register a callback against the id number.  This callback
                       // is called by dismissEditPluginPopup().
                       var plugin_id = data;
                       editPluginPopupCallbacks[data] = function(plugin_id, icon_src, icon_alt) {
                           texteditor.insertText(plugin_admin_html(plugin_id, icon_src, icon_alt));
                           editPluginPopupCallbacks[data] = null; // Unbind callback
                       };

                       // Show popup for editing
                       edit_object(plugin_id);
                   }
               }, "html");

    });

    /* onclick for 'Edit selected object' */
    $('span.edit-object').click(function() {
        var placeholder = $(this).parent().parent().children("input[type=hidden]").attr('value');
        var texteditor = get_editor(placeholder);
        if (texteditor == null || texteditor.selectedObject == null) {
            alert(gettext("Text editor does not support editing objects."));
            return;
        }
        var imgobj = texteditor.selectedObject();
        if (imgobj == null) {
            alert(gettext("No object selected."));
            return;
        }
        if (imgobj.id == null || imgobj.id.indexOf("plugin_obj_") != 0) {
            alert(gettext("Not a plugin object"));
            return;
        }
        var plugin_id = imgobj.id.substr("plugin_obj_".length);
        edit_object(plugin_id);
    });
});

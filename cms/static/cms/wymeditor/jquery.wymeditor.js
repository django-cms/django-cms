/*jslint evil: true, indent: 4 */
/**
    WYMeditor
    =========

    version 1.0.0a4

    WYMeditor : what you see is What You Mean web-based editor

    Main JS file with core classes and functions.

    Copyright
    ---------

    Copyright (c) 2005 - 2010 Jean-Francois Hovinne, http://www.wymeditor.org/
    Dual licensed under the MIT (MIT-license.txt)
    and GPL (GPL-license.txt) licenses.

    Website
    -------

    For further information visit:
    http://www.wymeditor.org/


    Authors
    -------

    See AUTHORS file
*/

// Global WYMeditor namespace.
if (typeof (WYMeditor) === 'undefined') {
    WYMeditor = {};
}

// Wrap the Firebug console in WYMeditor.console
(function () {
    if (!window.console || !window.console.firebug) {
        var names = [
                "log", "debug", "info", "warn", "error", "assert", "dir", "dirxml",
                "group", "groupEnd", "time", "timeEnd", "count", "trace", "profile",
                "profileEnd"
            ],
            noOp = function () {},
            i;

        WYMeditor.console = {};
        for (i = 0; i < names.length; i += 1) {
            WYMeditor.console[names[i]] = noOp;
        }

    } else {
        WYMeditor.console = window.console;
    }
}());

jQuery.extend(WYMeditor, {

/**
    Constants
    =========

    Global WYMeditor constants.

    VERSION             - Defines WYMeditor version.
    INSTANCES           - An array of loaded WYMeditor.editor instances.
    STRINGS             - An array of loaded WYMeditor language pairs/values.
    SKINS               - An array of loaded WYMeditor skins.
    NAME                - The "name" attribute.
    INDEX               - A string replaced by the instance index.
    WYM_INDEX           - A string used to get/set the instance index.
    BASE_PATH           - A string replaced by WYMeditor's base path.
    SKIN_PATH           - A string replaced by WYMeditor's skin path.
    WYM_PATH            - A string replaced by WYMeditor's main JS file path.
    SKINS_DEFAULT_PATH  - The skins default base path.
    SKINS_DEFAULT_CSS   - The skins default CSS file.
    LANG_DEFAULT_PATH   - The language files default path.
    IFRAME_BASE_PATH    - A string replaced by the designmode iframe's base path.
    IFRAME_DEFAULT      - The iframe's default base path.
    JQUERY_PATH         - A string replaced by the computed jQuery path.
    DIRECTION           - A string replaced by the text direction (rtl or ltr).
    LOGO                - A string replaced by WYMeditor logo.
    TOOLS               - A string replaced by the toolbar's HTML.
    TOOLS_ITEMS         - A string replaced by the toolbar items.
    TOOL_NAME           - A string replaced by a toolbar item's name.
    TOOL_TITLE          - A string replaced by a toolbar item's title.
    TOOL_CLASS          - A string replaced by a toolbar item's class.
    CLASSES             - A string replaced by the classes panel's HTML.
    CLASSES_ITEMS       - A string replaced by the classes items.
    CLASS_NAME          - A string replaced by a class item's name.
    CLASS_TITLE         - A string replaced by a class item's title.
    CONTAINERS          - A string replaced by the containers panel's HTML.
    CONTAINERS_ITEMS    - A string replaced by the containers items.
    CONTAINER_NAME      - A string replaced by a container item's name.
    CONTAINER_TITLE     - A string replaced by a container item's title.
    CONTAINER_CLASS     - A string replaced by a container item's class.
    HTML                - A string replaced by the HTML view panel's HTML.
    IFRAME              - A string replaced by the designmode iframe.
    STATUS              - A string replaced by the status panel's HTML.
    DIALOG_TITLE        - A string replaced by a dialog's title.
    DIALOG_BODY         - A string replaced by a dialog's HTML body.
    BODY                - The BODY element.
    STRING              - The "string" type.
    BODY,DIV,P,
    H1,H2,H3,H4,H5,H6,
    PRE,BLOCKQUOTE,
    A,BR,IMG,
    TABLE,TD,TH,
    UL,OL,LI            - HTML elements string representation.
    CLASS,HREF,SRC,
    TITLE,REL,ALT       - HTML attributes string representation.
    DIALOG_LINK         - A link dialog type.
    DIALOG_IMAGE        - An image dialog type.
    DIALOG_TABLE        - A table dialog type.
    DIALOG_PASTE        - A 'Paste from Word' dialog type.
    BOLD                - Command: (un)set selection to <strong>.
    ITALIC              - Command: (un)set selection to <em>.
    CREATE_LINK         - Command: open the link dialog or (un)set link.
    INSERT_IMAGE        - Command: open the image dialog or insert an image.
    INSERT_TABLE        - Command: open the table dialog.
    PASTE               - Command: open the paste dialog.
    INDENT              - Command: nest a list item.
    OUTDENT             - Command: unnest a list item.
    TOGGLE_HTML         - Command: display/hide the HTML view.
    FORMAT_BLOCK        - Command: set a block element to another type.
    PREVIEW             - Command: open the preview dialog.
    UNLINK              - Command: unset a link.
    INSERT_UNORDEREDLIST- Command: insert an unordered list.
    INSERT_ORDEREDLIST  - Command: insert an ordered list.
    MAIN_CONTAINERS     - An array of the main HTML containers used in WYMeditor.
    BLOCKS              - An array of the HTML block elements.
    KEY                 - Standard key codes.
    NODE                - Node types.

*/

    VERSION             : "1.0.0a4",
    INSTANCES           : [],
    STRINGS             : [],
    SKINS               : [],
    NAME                : "name",
    INDEX               : "{Wym_Index}",
    WYM_INDEX           : "wym_index",
    BASE_PATH           : "{Wym_Base_Path}",
    CSS_PATH            : "{Wym_Css_Path}",
    WYM_PATH            : "{Wym_Wym_Path}",
    SKINS_DEFAULT_PATH  : "skins/",
    SKINS_DEFAULT_CSS   : "skin.css",
    SKINS_DEFAULT_JS    : "skin.js",
    LANG_DEFAULT_PATH   : "lang/",
    IFRAME_BASE_PATH    : "{Wym_Iframe_Base_Path}",
    IFRAME_DEFAULT      : "iframe/default/",
    JQUERY_PATH         : "{Wym_Jquery_Path}",
    DIRECTION           : "{Wym_Direction}",
    LOGO                : "{Wym_Logo}",
    TOOLS               : "{Wym_Tools}",
    TOOLS_ITEMS         : "{Wym_Tools_Items}",
    TOOL_NAME           : "{Wym_Tool_Name}",
    TOOL_TITLE          : "{Wym_Tool_Title}",
    TOOL_CLASS          : "{Wym_Tool_Class}",
    CLASSES             : "{Wym_Classes}",
    CLASSES_ITEMS       : "{Wym_Classes_Items}",
    CLASS_NAME          : "{Wym_Class_Name}",
    CLASS_TITLE         : "{Wym_Class_Title}",
    CONTAINERS          : "{Wym_Containers}",
    CONTAINERS_ITEMS    : "{Wym_Containers_Items}",
    CONTAINER_NAME      : "{Wym_Container_Name}",
    CONTAINER_TITLE     : "{Wym_Containers_Title}",
    CONTAINER_CLASS     : "{Wym_Container_Class}",
    HTML                : "{Wym_Html}",
    IFRAME              : "{Wym_Iframe}",
    STATUS              : "{Wym_Status}",
    DIALOG_TITLE        : "{Wym_Dialog_Title}",
    DIALOG_BODY         : "{Wym_Dialog_Body}",
    NEWLINE             : "\n",
    STRING              : "string",
    BODY                : "body",
    DIV                 : "div",
    P                   : "p",
    H1                  : "h1",
    H2                  : "h2",
    H3                  : "h3",
    H4                  : "h4",
    H5                  : "h5",
    H6                  : "h6",
    PRE                 : "pre",
    BLOCKQUOTE          : "blockquote",
    A                   : "a",
    BR                  : "br",
    IMG                 : "img",
    TABLE               : "table",
    TR                  : "tr",
    TD                  : "td",
    TH                  : "th",
    UL                  : "ul",
    OL                  : "ol",
    LI                  : "li",
    CLASS               : "class",
    HREF                : "href",
    SRC                 : "src",
    TITLE               : "title",
    REL                 : "rel",
    ALT                 : "alt",
    DIALOG_LINK         : "Link",
    DIALOG_IMAGE        : "Image",
    DIALOG_TABLE        : "Table",
    DIALOG_PASTE        : "Paste_From_Word",
    BOLD                : "Bold",
    ITALIC              : "Italic",
    CREATE_LINK         : "CreateLink",
    INSERT_IMAGE        : "InsertImage",
    INSERT_TABLE        : "InsertTable",
    INSERT_HTML         : "InsertHTML",
    PASTE               : "Paste",
    INDENT              : "Indent",
    OUTDENT             : "Outdent",
    TOGGLE_HTML         : "ToggleHtml",
    FORMAT_BLOCK        : "FormatBlock",
    PREVIEW             : "Preview",
    UNLINK              : "Unlink",
    INSERT_UNORDEREDLIST: "InsertUnorderedList",
    INSERT_ORDEREDLIST  : "InsertOrderedList",

    MAIN_CONTAINERS : ["p",  "h1",  "h2",  "h3", "h4", "h5", "h6", "pre", "blockquote"],

    BLOCKS : ["address", "blockquote", "div", "dl",
        "fieldset", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
        "noscript", "ol", "p", "pre", "table", "ul", "dd", "dt",
        "li", "tbody", "td", "tfoot", "th", "thead", "tr"],

    BLOCKING_ELEMENTS : ["table", "blockquote", "pre"],

    NON_BLOCKING_ELEMENTS : ["p", "h1", "h2", "h3", "h4", "h5", "h6"],

    KEY : {
        BACKSPACE: 8,
        TAB: 9,
        ENTER: 13,
        CTRL: 17,
        END: 35,
        HOME: 36,
        CURSOR: [37, 38, 39, 40],
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40,
        DELETE: 46,
        B: 66,
        I: 73,
        R: 82,
        COMMAND: 224
    },

    NODE : {
        ELEMENT: 1,
        ATTRIBUTE: 2,
        TEXT: 3
    },

    /**
        WYMeditor.editor
        ================

        WYMeditor editor main class, instantiated for each editor occurrence.

        See also: WYMeditor.editor.init

        Use
        ---

        Initializes main values (index, elements, paths, ...)
        and calls WYMeditor.editor.init which initializes the editor.

        ### Parameters

        elem - The HTML element to be replaced by the editor.

        options - The hash of options.

        ### Returns

        Nothing.

    */
    editor : function (elem, options) {
        // Store the instance in the INSTANCES array and store the index
        this._index = WYMeditor.INSTANCES.push(this) - 1;
        // The element replaced by the editor
        this._element = elem;
        this._options = options;
        // Store the element's inner value
        this._html = jQuery(elem).val();

        if (this._options.html) {
            this._html = this._options.html;
        }
        // Path to the WYMeditor core
        this._options.wymPath = this._options.wymPath ||
            WYMeditor.computeWymPath();
        // Path to the main JS files
        this._options.basePath = this._options.basePath ||
            WYMeditor.computeBasePath(this._options.wymPath);
        // Path to jQuery (for loading in pop-up dialogs)
        this._options.jQueryPath = this._options.jQueryPath ||
            WYMeditor.computeJqueryPath();
        // Path to skin files
        this._options.skinPath = this._options.skinPath ||
            this._options.basePath + WYMeditor.SKINS_DEFAULT_PATH + this._options.skin + '/';
        // Path to the language files
        this._options.langPath = this._options.langPath ||
            this._options.basePath + WYMeditor.LANG_DEFAULT_PATH;
        // The designmode iframe's base path
        this._options.iframeBasePath = this._options.iframeBasePath ||
            this._options.basePath + WYMeditor.IFRAME_DEFAULT;

        // Initialize the editor instance
        this.init();
    }
});


/********** jQuery Plugin Definition **********/

/**
    wymeditor
    =========

    jQuery plugin function for replacing an HTML element with a WYMeditor
    instance.

    Example
    -------

    `jQuery(".wymeditor").wymeditor({});`
*/
jQuery.fn.wymeditor = function (options) {

    options = jQuery.extend({

        html:       "",
        basePath:   false,
        skinPath:    false,
        wymPath:    false,
        iframeBasePath: false,
        jQueryPath: false,
        styles: false,
        stylesheet: false,
        skin:       "default",
        initSkin:   true,
        loadSkin:   true,
        lang:       "en",
        direction:  "ltr",
        customCommands: [],
        boxHtml: String() +
            "<div class='wym_box'>" +
                "<div class='wym_area_top'>" +
                    WYMeditor.TOOLS +
                "</div>" +
                "<div class='wym_area_left'></div>" +
                "<div class='wym_area_right'>" +
                    WYMeditor.CONTAINERS +
                    WYMeditor.CLASSES +
                "</div>" +
                "<div class='wym_area_main'>" +
                    WYMeditor.HTML +
                    WYMeditor.IFRAME +
                    WYMeditor.STATUS +
                "</div>" +
                "<div class='wym_area_bottom'>" +
                    WYMeditor.LOGO +
                "</div>" +
            "</div>",

        logoHtml: String() +
            '<a class="wym_wymeditor_link" ' +
                'href="http://www.wymeditor.org/">WYMeditor</a>',

        iframeHtml: String() +
            '<div class="wym_iframe wym_section">' +
                '<iframe src="' + WYMeditor.IFRAME_BASE_PATH + 'wymiframe.html" ' +
                    'onload="this.contentWindow.parent.WYMeditor.INSTANCES[' +
                        WYMeditor.INDEX + '].initIframe(this)">' +
                '</iframe>' +
            "</div>",

        editorStyles: [],
        toolsHtml: String() +
            '<div class="wym_tools wym_section">' +
                '<h2>{Tools}</h2>' +
                '<ul>' +
                    WYMeditor.TOOLS_ITEMS +
                '</ul>' +
            '</div>',

        toolsItemHtml: String() +
            '<li class="' + WYMeditor.TOOL_CLASS + '">' +
                '<a href="#" name="' + WYMeditor.TOOL_NAME + '"' +
                        'title="' + WYMeditor.TOOL_TITLE + '">' +
                    WYMeditor.TOOL_TITLE +
                '</a>' +
            '</li>',

        toolsItems: [
            {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'},
            {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
            {'name': 'Superscript', 'title': 'Superscript',
                'css': 'wym_tools_superscript'},
            {'name': 'Subscript', 'title': 'Subscript',
                'css': 'wym_tools_subscript'},
            {'name': 'InsertOrderedList', 'title': 'Ordered_List',
                'css': 'wym_tools_ordered_list'},
            {'name': 'InsertUnorderedList', 'title': 'Unordered_List',
                'css': 'wym_tools_unordered_list'},
            {'name': 'Indent', 'title': 'Indent', 'css': 'wym_tools_indent'},
            {'name': 'Outdent', 'title': 'Outdent', 'css': 'wym_tools_outdent'},
            {'name': 'Undo', 'title': 'Undo', 'css': 'wym_tools_undo'},
            {'name': 'Redo', 'title': 'Redo', 'css': 'wym_tools_redo'},
            {'name': 'CreateLink', 'title': 'Link', 'css': 'wym_tools_link'},
            {'name': 'Unlink', 'title': 'Unlink', 'css': 'wym_tools_unlink'},
            {'name': 'InsertImage', 'title': 'Image', 'css': 'wym_tools_image'},
            {'name': 'InsertTable', 'title': 'Table', 'css': 'wym_tools_table'},
            {'name': 'Paste', 'title': 'Paste_From_Word',
                'css': 'wym_tools_paste'},
            {'name': 'ToggleHtml', 'title': 'HTML', 'css': 'wym_tools_html'},
            {'name': 'Preview', 'title': 'Preview', 'css': 'wym_tools_preview'}
        ],

        containersHtml: String() +
            '<div class="wym_containers wym_section">' +
                '<h2>{Containers}</h2>' +
                '<ul>' +
                    WYMeditor.CONTAINERS_ITEMS +
                '</ul>' +
            '</div>',

        containersItemHtml: String() +
            '<li class="' + WYMeditor.CONTAINER_CLASS + '">' +
                '<a href="#" name="' + WYMeditor.CONTAINER_NAME + '">' +
                    WYMeditor.CONTAINER_TITLE +
                '</a>' +
            '</li>',

        containersItems: [
            {'name': 'P', 'title': 'Paragraph', 'css': 'wym_containers_p'},
            {'name': 'H1', 'title': 'Heading_1', 'css': 'wym_containers_h1'},
            {'name': 'H2', 'title': 'Heading_2', 'css': 'wym_containers_h2'},
            {'name': 'H3', 'title': 'Heading_3', 'css': 'wym_containers_h3'},
            {'name': 'H4', 'title': 'Heading_4', 'css': 'wym_containers_h4'},
            {'name': 'H5', 'title': 'Heading_5', 'css': 'wym_containers_h5'},
            {'name': 'H6', 'title': 'Heading_6', 'css': 'wym_containers_h6'},
            {'name': 'PRE', 'title': 'Preformatted', 'css': 'wym_containers_pre'},
            {'name': 'BLOCKQUOTE', 'title': 'Blockquote',
                'css': 'wym_containers_blockquote'},
            {'name': 'TH', 'title': 'Table_Header', 'css': 'wym_containers_th'}
        ],

        classesHtml: String() +
            '<div class="wym_classes wym_section">' +
                '<h2>{Classes}</h2>' +
                '<ul>' +
                    WYMeditor.CLASSES_ITEMS +
                '</ul>' +
            '</div>',

        classesItemHtml: String() +
            '<li class="wym_classes_' + WYMeditor.CLASS_NAME + '">' +
                '<a href="#" name="' + WYMeditor.CLASS_NAME + '">' +
                    WYMeditor.CLASS_TITLE +
                '</a>' +
            '</li>',

        classesItems:      [],
        statusHtml: String() +
            '<div class="wym_status wym_section">' +
                '<h2>{Status}</h2>' +
            '</div>',

        htmlHtml: String() +
            '<div class="wym_html wym_section">' +
                '<h2>{Source_Code}</h2>' +
                '<textarea class="wym_html_val"></textarea>' +
            '</div>',

        boxSelector:        ".wym_box",
        toolsSelector:      ".wym_tools",
        toolsListSelector:  " ul",
        containersSelector: ".wym_containers",
        classesSelector:    ".wym_classes",
        htmlSelector:       ".wym_html",
        iframeSelector:     ".wym_iframe iframe",
        iframeBodySelector: ".wym_iframe",
        statusSelector:     ".wym_status",
        toolSelector:       ".wym_tools a",
        containerSelector:  ".wym_containers a",
        classSelector:      ".wym_classes a",
        htmlValSelector:    ".wym_html_val",

        hrefSelector:       ".wym_href",
        srcSelector:        ".wym_src",
        titleSelector:      ".wym_title",
        relSelector:        ".wym_rel",
        altSelector:        ".wym_alt",
        textSelector:       ".wym_text",

        rowsSelector:       ".wym_rows",
        colsSelector:       ".wym_cols",
        captionSelector:    ".wym_caption",
        summarySelector:    ".wym_summary",

        submitSelector:     "form",
        cancelSelector:     ".wym_cancel",
        previewSelector:    "",

        dialogTypeSelector:    ".wym_dialog_type",
        dialogLinkSelector:    ".wym_dialog_link",
        dialogImageSelector:   ".wym_dialog_image",
        dialogTableSelector:   ".wym_dialog_table",
        dialogPasteSelector:   ".wym_dialog_paste",
        dialogPreviewSelector: ".wym_dialog_preview",

        updateSelector:    ".wymupdate",
        updateEvent:       "click",

        dialogFeatures:    "menubar=no,titlebar=no,toolbar=no,resizable=no" +
            ",width=560,height=300,top=0,left=0",
        dialogFeaturesPreview: "menubar=no,titlebar=no,toolbar=no,resizable=no" +
            ",scrollbars=yes,width=560,height=300,top=0,left=0",

        dialogHtml: String() +
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" ' +
                    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">' +
            '<html dir="' + WYMeditor.DIRECTION + '">' +
                '<head>' +
                    '<link rel="stylesheet" type="text/css" media="screen" ' +
                        'href="' + WYMeditor.CSS_PATH + '" />' +
                    '<title>' + WYMeditor.DIALOG_TITLE + '</title>' +
                    '<script type="text/javascript" ' +
                        'src="' + WYMeditor.JQUERY_PATH + '"></script>' +
                    '<script type="text/javascript" ' +
                        'src="' + WYMeditor.WYM_PATH + '"></script>' +
                '</head>' +
                WYMeditor.DIALOG_BODY +
            '</html>',

        dialogLinkHtml: String() +
            '<body class="wym_dialog wym_dialog_link" ' +
                    ' onload="WYMeditor.INIT_DIALOG(' + WYMeditor.INDEX + ')">' +
                '<form>' +
                    '<fieldset>' +
                        '<input type="hidden" class="wym_dialog_type" ' +
                            'value="' + WYMeditor.DIALOG_LINK + '" />' +
                        '<legend>{Link}</legend>' +
                        '<div class="row">' +
                            '<label>{URL}</label>' +
                            '<input type="text" class="wym_href" value="" ' +
                                'size="40" autofocus="autofocus" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Title}</label>' +
                            '<input type="text" class="wym_title" value="" ' +
                                'size="40" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Relationship}</label>' +
                            '<input type="text" class="wym_rel" value="" ' +
                                'size="40" />' +
                        '</div>' +
                        '<div class="row row-indent">' +
                            '<input class="wym_submit" type="submit" ' +
                                'value="{Submit}" />' +
                            '<input class="wym_cancel" type="button" ' +
                                'value="{Cancel}" />' +
                        '</div>' +
                    '</fieldset>' +
                '</form>' +
            '</body>',

        dialogImageHtml: String() +
            '<body class="wym_dialog wym_dialog_image" ' +
                    'onload="WYMeditor.INIT_DIALOG(' + WYMeditor.INDEX + ')">' +
                '<form>' +
                    '<fieldset>' +
                        '<input type="hidden" class="wym_dialog_type" ' +
                            'value="' + WYMeditor.DIALOG_IMAGE + '" />' +
                        '<legend>{Image}</legend>' +
                        '<div class="row">' +
                            '<label>{URL}</label>' +
                            '<input type="text" class="wym_src" value="" ' +
                                'size="40" autofocus="autofocus" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Alternative_Text}</label>' +
                            '<input type="text" class="wym_alt" value="" size="40" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Title}</label>' +
                            '<input type="text" class="wym_title" value="" size="40" />' +
                        '</div>' +
                        '<div class="row row-indent">' +
                            '<input class="wym_submit" type="submit" ' +
                                'value="{Submit}" />' +
                            '<input class="wym_cancel" type="button" ' +
                                'value="{Cancel}" />' +
                        '</div>' +
                    '</fieldset>' +
                '</form>' +
            '</body>',

        dialogTableHtml: String() +
            '<body class="wym_dialog wym_dialog_table" ' +
                    'onload="WYMeditor.INIT_DIALOG(' + WYMeditor.INDEX + ')">' +
                '<form>' +
                    '<fieldset>' +
                        '<input type="hidden" class="wym_dialog_type" ' +
                            'value="' + WYMeditor.DIALOG_TABLE + '" />' +
                        '<legend>{Table}</legend>' +
                        '<div class="row">' +
                            '<label>{Caption}</label>' +
                            '<input type="text" class="wym_caption" value="" ' +
                                'size="40" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Summary}</label>' +
                            '<input type="text" class="wym_summary" value="" ' +
                                'size="40" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Number_Of_Rows}</label>' +
                            '<input type="text" class="wym_rows" value="3" size="3" />' +
                        '</div>' +
                        '<div class="row">' +
                            '<label>{Number_Of_Cols}</label>' +
                            '<input type="text" class="wym_cols" value="2" size="3" />' +
                        '</div>' +
                        '<div class="row row-indent">' +
                            '<input class="wym_submit" type="submit" ' +
                                'value="{Submit}" />' +
                            '<input class="wym_cancel" type="button" ' +
                                'value="{Cancel}" />' +
                        '</div>' +
                    '</fieldset>' +
                '</form>' +
            '</body>',

        dialogPasteHtml: String() +
            '<body class="wym_dialog wym_dialog_paste" ' +
                    'onload="WYMeditor.INIT_DIALOG(' + WYMeditor.INDEX + ')">' +
                '<form>' +
                    '<input type="hidden" class="wym_dialog_type" ' +
                        'value="' + WYMeditor.DIALOG_PASTE + '" />' +
                    '<fieldset>' +
                        '<legend>{Paste_From_Word}</legend>' +
                        '<div class="row">' +
                            '<textarea class="wym_text" rows="10" cols="50" ' +
                                'autofocus="autofocus"></textarea>' +
                        '</div>' +
                        '<div class="row">' +
                            '<input class="wym_submit" type="submit" ' +
                                'value="{Submit}" />' +
                            '<input class="wym_cancel" type="button" ' +
                                'value="{Cancel}" />' +
                        '</div>' +
                    '</fieldset>' +
                '</form>' +
            '</body>',

        dialogPreviewHtml: String() +
            '<body class="wym_dialog wym_dialog_preview" ' +
                'onload="WYMeditor.INIT_DIALOG(' + WYMeditor.INDEX + ')"></body>',

        dialogStyles: [],

        stringDelimiterLeft:  "{",
        stringDelimiterRight: "}",

        preInit: null,
        preBind: null,
        postInit: null,

        preInitDialog: null,
        postInitDialog: null

    }, options);

    return this.each(function () {
        // Assigning to _editor because the return value from new isn't
        // actually used, but we need to use new to properly change the
        // prototype
        var _editor = new WYMeditor.editor(jQuery(this), options);
    });
};

// Enable accessing of wymeditor instances via $.wymeditors
jQuery.extend({
    wymeditors: function (i) {
        return WYMeditor.INSTANCES[i];
    }
});

/**
    WYMeditor.computeWymPath
    ========================

    Get the relative path to the WYMeditor core js file for usage as
    a src attribute for script inclusion.

    Looks for script tags on the current page and finds the first matching
    src attribute matching any of these values:
    * jquery.wymeditor.pack.js
    * jquery.wymeditor.min.js
    * jquery.wymeditor.packed.js
    * jquery.wymeditor.js
    * /core.js
*/
WYMeditor.computeWymPath = function () {
    var script = jQuery(
        jQuery.grep(
            jQuery('script'),
            function (s) {
                if (!s.src) {
                    return null;
                }
                return (
                    s.src.match(
                        /jquery\.wymeditor(\.pack|\.min|\.packed)?\.js(\?.*)?$/
                    )
                );
            }
        )
    );
    if (script.length > 0) {
        return script.attr('src');
    }
    // We couldn't locate the base path. This will break language loading,
    // dialog boxes and other features.
    WYMeditor.console.warn(
        "Error determining wymPath. No base WYMeditor file located."
    );
    WYMeditor.console.warn("Assuming wymPath to be the current URL");
    WYMeditor.console.warn("Please pass a correct wymPath option");

    // Guess that the wymPath is the current directory
    return '';
};

/**
    WYMeditor.computeBasePath
    =========================

    Get the relative path to the WYMeditor directory root based on the path to
    the wymeditor base file. This path is used as the basis for loading:
    * Language files
    * Skins
    *
*/
WYMeditor.computeBasePath = function (wymPath) {
    // Strip everything after the last slash to get the base path
    var lastSlashIndex = wymPath.lastIndexOf('/');
    return wymPath.substr(0, lastSlashIndex + 1);
};

/**
    WYMeditor.computeJqueryPath
    ===========================

    Get the relative path to the currently-included jquery javascript file.

    Returns the first script src attribute that matches one of the following
    patterns:

    * jquery.pack.js
    * jquery.min.js
    * jquery.packed.js
    * Plus the jquery-<version> variants
*/
WYMeditor.computeJqueryPath = function () {
    return jQuery(
        jQuery.grep(
            jQuery('script'),
            function (s) {
                return (
                    s.src &&
                    s.src.match(
                            /jquery(-(.*)){0,1}(\.pack|\.min|\.packed)?\.js(\?.*)?$/
                        )
                );
            }
        )
    ).attr('src');
};

/********** DIALOGS **********/

WYMeditor.INIT_DIALOG = function (index) {

    var wym = window.opener.WYMeditor.INSTANCES[index],
        doc = window.document,
        selected = wym.selected(),
        dialogType = jQuery(wym._options.dialogTypeSelector).val(),
        sStamp = wym.uniqueStamp(),
        styles,
        aCss,
        tableOnClick;

    if (dialogType === WYMeditor.DIALOG_LINK) {
        // ensure that we select the link to populate the fields
        if (selected && selected.tagName &&
                selected.tagName.toLowerCase !== WYMeditor.A) {
            selected = jQuery(selected).parentsOrSelf(WYMeditor.A);
        }

        // fix MSIE selection if link image has been clicked
        if (!selected && wym._selected_image) {
            selected = jQuery(wym._selected_image).parentsOrSelf(WYMeditor.A);
        }
    }

    // pre-init functions
    if (jQuery.isFunction(wym._options.preInitDialog)) {
        wym._options.preInitDialog(wym, window);
    }

    // add css rules from options
    styles = doc.styleSheets[0];
    aCss = eval(wym._options.dialogStyles);

    wym.addCssRules(doc, aCss);

    // auto populate fields if selected container (e.g. A)
    if (selected) {
        jQuery(wym._options.hrefSelector).val(jQuery(selected).attr(WYMeditor.HREF));
        jQuery(wym._options.srcSelector).val(jQuery(selected).attr(WYMeditor.SRC));
        jQuery(wym._options.titleSelector).val(jQuery(selected).attr(WYMeditor.TITLE));
        jQuery(wym._options.relSelector).val(jQuery(selected).attr(WYMeditor.REL));
        jQuery(wym._options.altSelector).val(jQuery(selected).attr(WYMeditor.ALT));
    }

    // auto populate image fields if selected image
    if (wym._selected_image) {
        jQuery(wym._options.dialogImageSelector + " " + wym._options.srcSelector).val(jQuery(wym._selected_image).attr(WYMeditor.SRC));
        jQuery(wym._options.dialogImageSelector + " " + wym._options.titleSelector).val(jQuery(wym._selected_image).attr(WYMeditor.TITLE));
        jQuery(wym._options.dialogImageSelector + " " + wym._options.altSelector).val(jQuery(wym._selected_image).attr(WYMeditor.ALT));
    }

    jQuery(wym._options.dialogLinkSelector + " " +
            wym._options.submitSelector).submit(function () {

        var sUrl = jQuery(wym._options.hrefSelector).val(),
            link;
        if (sUrl.length > 0) {

            if (selected[0] && selected[0].tagName.toLowerCase() === WYMeditor.A) {
                link = selected;
            } else {
                wym._exec(WYMeditor.CREATE_LINK, sStamp);
                link = jQuery("a[href=" + sStamp + "]", wym._doc.body);
            }

            link.attr(WYMeditor.HREF, sUrl);
            link.attr(WYMeditor.TITLE, jQuery(wym._options.titleSelector).val());
            link.attr(WYMeditor.REL, jQuery(wym._options.relSelector).val());
        }
        window.close();
    });

    jQuery(wym._options.dialogImageSelector + " " +
            wym._options.submitSelector).submit(function () {

        var sUrl = jQuery(wym._options.srcSelector).val(),
            $img;
        if (sUrl.length > 0) {

            wym._exec(WYMeditor.INSERT_IMAGE, sStamp);

            $img = jQuery("img[src$=" + sStamp + "]", wym._doc.body);
            $img.attr(WYMeditor.SRC, sUrl);
            $img.attr(WYMeditor.TITLE, jQuery(wym._options.titleSelector).val());
            $img.attr(WYMeditor.ALT, jQuery(wym._options.altSelector).val());
        }
        window.close();
    });

    tableOnClick = WYMeditor.MAKE_TABLE_ONCLICK(wym);
    jQuery(wym._options.dialogTableSelector + " " + wym._options.submitSelector)
        .submit(tableOnClick);

    jQuery(wym._options.dialogPasteSelector + " " +
            wym._options.submitSelector).submit(function () {

        var sText = jQuery(wym._options.textSelector).val();
        wym.paste(sText);
        window.close();
    });

    jQuery(wym._options.dialogPreviewSelector + " " +
        wym._options.previewSelector).html(wym.xhtml());

    //cancel button
    jQuery(wym._options.cancelSelector).mousedown(function () {
        window.close();
    });

    //pre-init functions
    if (jQuery.isFunction(wym._options.postInitDialog)) {
        wym._options.postInitDialog(wym, window);
    }

};

/********** TABLE DIALOG ONCLICK **********/

WYMeditor.MAKE_TABLE_ONCLICK = function (wym) {
    var tableOnClick = function () {
        var numRows = jQuery(wym._options.rowsSelector).val(),
            numColumns = jQuery(wym._options.colsSelector).val(),
            caption = jQuery(wym._options.captionSelector).val(),
            summary = jQuery(wym._options.summarySelector).val(),

            table = wym.insertTable(numRows, numColumns, caption, summary);

        window.close();
    };

    return tableOnClick;
};


/********** HELPERS **********/

// Returns true if it is a text node with whitespaces only
jQuery.fn.isPhantomNode = function () {
    if (this[0].nodeType === 3) {
        return !(/[^\t\n\r ]/.test(this[0].data));
    }

    return false;
};

WYMeditor.isPhantomNode = function (n) {
    if (n.nodeType === 3) {
        return !(/[^\t\n\r ]/.test(n.data));
    }

    return false;
};

WYMeditor.isPhantomString = function (str) {
    return !(/[^\t\n\r ]/.test(str));
};

// Returns the Parents or the node itself
// jqexpr = a jQuery expression
jQuery.fn.parentsOrSelf = function (jqexpr) {
    var n = this;

    if (n[0].nodeType === 3) {
        n = n.parents().slice(0, 1);
    }

//  if (n.is(jqexpr)) // XXX should work, but doesn't (probably a jQuery bug)
    if (n.filter(jqexpr).size() === 1) {
        return n;
    } else {
        return n.parents(jqexpr).slice(0, 1);
    }
};

// String & array helpers

WYMeditor.Helper = {

    //replace all instances of 'old' by 'rep' in 'str' string
    replaceAll: function (str, old, rep) {
        var rExp = new RegExp(old, "g");
        return str.replace(rExp, rep);
    },

    //insert 'inserted' at position 'pos' in 'str' string
    insertAt: function (str, inserted, pos) {
        return str.substr(0, pos) + inserted + str.substring(pos);
    },

    //trim 'str' string
    trim: function (str) {
        return str.replace(/^(\s*)|(\s*)$/gm, '');
    },

    //return true if 'arr' array contains 'elem', or false
    contains: function (arr, elem) {
        var i;
        for (i = 0; i < arr.length; i += 1) {
            if (arr[i] === elem) {
                return true;
            }
        }
        return false;
    },

    //return 'item' position in 'arr' array, or -1
    indexOf: function (arr, item) {
        var ret = -1, i;
        for (i = 0; i < arr.length; i += 1) {
            if (arr[i] === item) {
                ret = i;
                break;
            }
        }
        return ret;
    },

    //return 'item' object in 'arr' array, checking its 'name' property, or null
    findByName: function (arr, name) {
        var i, item;
        for (i = 0; i < arr.length; i += 1) {
            item = arr[i];
            if (item.name === name) {
                return item;
            }
        }
        return null;
    }
};


/**
 * @license Rangy, a cross-browser JavaScript range and selection library
 * http://code.google.com/p/rangy/
 *
 * Copyright 2011, Tim Down
 * Licensed under the MIT license.
 * Version: 1.2.2
 * Build date: 13 November 2011
 */
window['rangy'] = (function() {


    var OBJECT = "object", FUNCTION = "function", UNDEFINED = "undefined";

    var domRangeProperties = ["startContainer", "startOffset", "endContainer", "endOffset", "collapsed",
        "commonAncestorContainer", "START_TO_START", "START_TO_END", "END_TO_START", "END_TO_END"];

    var domRangeMethods = ["setStart", "setStartBefore", "setStartAfter", "setEnd", "setEndBefore",
        "setEndAfter", "collapse", "selectNode", "selectNodeContents", "compareBoundaryPoints", "deleteContents",
        "extractContents", "cloneContents", "insertNode", "surroundContents", "cloneRange", "toString", "detach"];

    var textRangeProperties = ["boundingHeight", "boundingLeft", "boundingTop", "boundingWidth", "htmlText", "text"];

    // Subset of TextRange's full set of methods that we're interested in
    var textRangeMethods = ["collapse", "compareEndPoints", "duplicate", "getBookmark", "moveToBookmark",
        "moveToElementText", "parentElement", "pasteHTML", "select", "setEndPoint", "getBoundingClientRect"];

    /*----------------------------------------------------------------------------------------------------------------*/

    // Trio of functions taken from Peter Michaux's article:
    // http://peter.michaux.ca/articles/feature-detection-state-of-the-art-browser-scripting
    function isHostMethod(o, p) {
        var t = typeof o[p];
        return t == FUNCTION || (!!(t == OBJECT && o[p])) || t == "unknown";
    }

    function isHostObject(o, p) {
        return !!(typeof o[p] == OBJECT && o[p]);
    }

    function isHostProperty(o, p) {
        return typeof o[p] != UNDEFINED;
    }

    // Creates a convenience function to save verbose repeated calls to tests functions
    function createMultiplePropertyTest(testFunc) {
        return function(o, props) {
            var i = props.length;
            while (i--) {
                if (!testFunc(o, props[i])) {
                    return false;
                }
            }
            return true;
        };
    }

    // Next trio of functions are a convenience to save verbose repeated calls to previous two functions
    var areHostMethods = createMultiplePropertyTest(isHostMethod);
    var areHostObjects = createMultiplePropertyTest(isHostObject);
    var areHostProperties = createMultiplePropertyTest(isHostProperty);

    function isTextRange(range) {
        return range && areHostMethods(range, textRangeMethods) && areHostProperties(range, textRangeProperties);
    }

    var api = {
        version: "1.2.2",
        initialized: false,
        supported: true,

        util: {
            isHostMethod: isHostMethod,
            isHostObject: isHostObject,
            isHostProperty: isHostProperty,
            areHostMethods: areHostMethods,
            areHostObjects: areHostObjects,
            areHostProperties: areHostProperties,
            isTextRange: isTextRange
        },

        features: {},

        modules: {},
        config: {
            alertOnWarn: false,
            preferTextRange: false
        }
    };

    function fail(reason) {
        window.alert("Rangy not supported in your browser. Reason: " + reason);
        api.initialized = true;
        api.supported = false;
    }

    api.fail = fail;

    function warn(msg) {
        var warningMessage = "Rangy warning: " + msg;
        if (api.config.alertOnWarn) {
            window.alert(warningMessage);
        } else if (typeof window.console != UNDEFINED && typeof window.console.log != UNDEFINED) {
            window.console.log(warningMessage);
        }
    }

    api.warn = warn;

    if ({}.hasOwnProperty) {
        api.util.extend = function(o, props) {
            for (var i in props) {
                if (props.hasOwnProperty(i)) {
                    o[i] = props[i];
                }
            }
        };
    } else {
        fail("hasOwnProperty not supported");
    }

    var initListeners = [];
    var moduleInitializers = [];

    // Initialization
    function init() {
        if (api.initialized) {
            return;
        }
        var testRange;
        var implementsDomRange = false, implementsTextRange = false;

        // First, perform basic feature tests

        if (isHostMethod(document, "createRange")) {
            testRange = document.createRange();
            if (areHostMethods(testRange, domRangeMethods) && areHostProperties(testRange, domRangeProperties)) {
                implementsDomRange = true;
            }
            testRange.detach();
        }

        var body = isHostObject(document, "body") ? document.body : document.getElementsByTagName("body")[0];

        if (body && isHostMethod(body, "createTextRange")) {
            testRange = body.createTextRange();
            if (isTextRange(testRange)) {
                implementsTextRange = true;
            }
        }

        if (!implementsDomRange && !implementsTextRange) {
            fail("Neither Range nor TextRange are implemented");
        }

        api.initialized = true;
        api.features = {
            implementsDomRange: implementsDomRange,
            implementsTextRange: implementsTextRange
        };

        // Initialize modules and call init listeners
        var allListeners = moduleInitializers.concat(initListeners);
        for (var i = 0, len = allListeners.length; i < len; ++i) {
            try {
                allListeners[i](api);
            } catch (ex) {
                if (isHostObject(window, "console") && isHostMethod(window.console, "log")) {
                    window.console.log("Init listener threw an exception. Continuing.", ex);
                }

            }
        }
    }

    // Allow external scripts to initialize this library in case it's loaded after the document has loaded
    api.init = init;

    // Execute listener immediately if already initialized
    api.addInitListener = function(listener) {
        if (api.initialized) {
            listener(api);
        } else {
            initListeners.push(listener);
        }
    };

    var createMissingNativeApiListeners = [];

    api.addCreateMissingNativeApiListener = function(listener) {
        createMissingNativeApiListeners.push(listener);
    };

    function createMissingNativeApi(win) {
        win = win || window;
        init();

        // Notify listeners
        for (var i = 0, len = createMissingNativeApiListeners.length; i < len; ++i) {
            createMissingNativeApiListeners[i](win);
        }
    }

    api.createMissingNativeApi = createMissingNativeApi;

    /**
     * @constructor
     */
    function Module(name) {
        this.name = name;
        this.initialized = false;
        this.supported = false;
    }

    Module.prototype.fail = function(reason) {
        this.initialized = true;
        this.supported = false;

        throw new Error("Module '" + this.name + "' failed to load: " + reason);
    };

    Module.prototype.warn = function(msg) {
        api.warn("Module " + this.name + ": " + msg);
    };

    Module.prototype.createError = function(msg) {
        return new Error("Error in Rangy " + this.name + " module: " + msg);
    };

    api.createModule = function(name, initFunc) {
        var module = new Module(name);
        api.modules[name] = module;

        moduleInitializers.push(function(api) {
            initFunc(api, module);
            module.initialized = true;
            module.supported = true;
        });
    };

    api.requireModules = function(modules) {
        for (var i = 0, len = modules.length, module, moduleName; i < len; ++i) {
            moduleName = modules[i];
            module = api.modules[moduleName];
            if (!module || !(module instanceof Module)) {
                throw new Error("Module '" + moduleName + "' not found");
            }
            if (!module.supported) {
                throw new Error("Module '" + moduleName + "' not supported");
            }
        }
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    // Wait for document to load before running tests

    var docReady = false;

    var loadHandler = function(e) {

        if (!docReady) {
            docReady = true;
            if (!api.initialized) {
                init();
            }
        }
    };

    // Test whether we have window and document objects that we will need
    if (typeof window == UNDEFINED) {
        fail("No window found");
        return;
    }
    if (typeof document == UNDEFINED) {
        fail("No document found");
        return;
    }

    if (isHostMethod(document, "addEventListener")) {
        document.addEventListener("DOMContentLoaded", loadHandler, false);
    }

    // Add a fallback in case the DOMContentLoaded event isn't supported
    if (isHostMethod(window, "addEventListener")) {
        window.addEventListener("load", loadHandler, false);
    } else if (isHostMethod(window, "attachEvent")) {
        window.attachEvent("onload", loadHandler);
    } else {
        fail("Window does not have required addEventListener or attachEvent method");
    }

    return api;
})();
rangy.createModule("DomUtil", function(api, module) {

    var UNDEF = "undefined";
    var util = api.util;

    // Perform feature tests
    if (!util.areHostMethods(document, ["createDocumentFragment", "createElement", "createTextNode"])) {
        module.fail("document missing a Node creation method");
    }

    if (!util.isHostMethod(document, "getElementsByTagName")) {
        module.fail("document missing getElementsByTagName method");
    }

    var el = document.createElement("div");
    if (!util.areHostMethods(el, ["insertBefore", "appendChild", "cloneNode"] ||
            !util.areHostObjects(el, ["previousSibling", "nextSibling", "childNodes", "parentNode"]))) {
        module.fail("Incomplete Element implementation");
    }

    // innerHTML is required for Range's createContextualFragment method
    if (!util.isHostProperty(el, "innerHTML")) {
        module.fail("Element is missing innerHTML property");
    }

    var textNode = document.createTextNode("test");
    if (!util.areHostMethods(textNode, ["splitText", "deleteData", "insertData", "appendData", "cloneNode"] ||
            !util.areHostObjects(el, ["previousSibling", "nextSibling", "childNodes", "parentNode"]) ||
            !util.areHostProperties(textNode, ["data"]))) {
        module.fail("Incomplete Text Node implementation");
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Removed use of indexOf because of a bizarre bug in Opera that is thrown in one of the Acid3 tests. I haven't been
    // able to replicate it outside of the test. The bug is that indexOf returns -1 when called on an Array that
    // contains just the document as a single element and the value searched for is the document.
    var arrayContains = /*Array.prototype.indexOf ?
        function(arr, val) {
            return arr.indexOf(val) > -1;
        }:*/

        function(arr, val) {
            var i = arr.length;
            while (i--) {
                if (arr[i] === val) {
                    return true;
                }
            }
            return false;
        };

    // Opera 11 puts HTML elements in the null namespace, it seems, and IE 7 has undefined namespaceURI
    function isHtmlNamespace(node) {
        var ns;
        return typeof node.namespaceURI == UNDEF || ((ns = node.namespaceURI) === null || ns == "http://www.w3.org/1999/xhtml");
    }

    function parentElement(node) {
        var parent = node.parentNode;
        return (parent.nodeType == 1) ? parent : null;
    }

    function getNodeIndex(node) {
        var i = 0;
        while( (node = node.previousSibling) ) {
            i++;
        }
        return i;
    }

    function getNodeLength(node) {
        var childNodes;
        return isCharacterDataNode(node) ? node.length : ((childNodes = node.childNodes) ? childNodes.length : 0);
    }

    function getCommonAncestor(node1, node2) {
        var ancestors = [], n;
        for (n = node1; n; n = n.parentNode) {
            ancestors.push(n);
        }

        for (n = node2; n; n = n.parentNode) {
            if (arrayContains(ancestors, n)) {
                return n;
            }
        }

        return null;
    }

    function isAncestorOf(ancestor, descendant, selfIsAncestor) {
        var n = selfIsAncestor ? descendant : descendant.parentNode;
        while (n) {
            if (n === ancestor) {
                return true;
            } else {
                n = n.parentNode;
            }
        }
        return false;
    }

    function getClosestAncestorIn(node, ancestor, selfIsAncestor) {
        var p, n = selfIsAncestor ? node : node.parentNode;
        while (n) {
            p = n.parentNode;
            if (p === ancestor) {
                return n;
            }
            n = p;
        }
        return null;
    }

    function isCharacterDataNode(node) {
        var t = node.nodeType;
        return t == 3 || t == 4 || t == 8 ; // Text, CDataSection or Comment
    }

    function insertAfter(node, precedingNode) {
        var nextNode = precedingNode.nextSibling, parent = precedingNode.parentNode;
        if (nextNode) {
            parent.insertBefore(node, nextNode);
        } else {
            parent.appendChild(node);
        }
        return node;
    }

    // Note that we cannot use splitText() because it is bugridden in IE 9.
    function splitDataNode(node, index) {
        var newNode = node.cloneNode(false);
        newNode.deleteData(0, index);
        node.deleteData(index, node.length - index);
        insertAfter(newNode, node);
        return newNode;
    }

    function getDocument(node) {
        if (node.nodeType == 9) {
            return node;
        } else if (typeof node.ownerDocument != UNDEF) {
            return node.ownerDocument;
        } else if (typeof node.document != UNDEF) {
            return node.document;
        } else if (node.parentNode) {
            return getDocument(node.parentNode);
        } else {
            throw new Error("getDocument: no document found for node");
        }
    }

    function getWindow(node) {
        var doc = getDocument(node);
        if (typeof doc.defaultView != UNDEF) {
            return doc.defaultView;
        } else if (typeof doc.parentWindow != UNDEF) {
            return doc.parentWindow;
        } else {
            throw new Error("Cannot get a window object for node");
        }
    }

    function getIframeDocument(iframeEl) {
        if (typeof iframeEl.contentDocument != UNDEF) {
            return iframeEl.contentDocument;
        } else if (typeof iframeEl.contentWindow != UNDEF) {
            return iframeEl.contentWindow.document;
        } else {
            throw new Error("getIframeWindow: No Document object found for iframe element");
        }
    }

    function getIframeWindow(iframeEl) {
        if (typeof iframeEl.contentWindow != UNDEF) {
            return iframeEl.contentWindow;
        } else if (typeof iframeEl.contentDocument != UNDEF) {
            return iframeEl.contentDocument.defaultView;
        } else {
            throw new Error("getIframeWindow: No Window object found for iframe element");
        }
    }

    function getBody(doc) {
        return util.isHostObject(doc, "body") ? doc.body : doc.getElementsByTagName("body")[0];
    }

    function getRootContainer(node) {
        var parent;
        while ( (parent = node.parentNode) ) {
            node = parent;
        }
        return node;
    }

    function comparePoints(nodeA, offsetA, nodeB, offsetB) {
        // See http://www.w3.org/TR/DOM-Level-2-Traversal-Range/ranges.html#Level-2-Range-Comparing
        var nodeC, root, childA, childB, n;
        if (nodeA == nodeB) {

            // Case 1: nodes are the same
            return offsetA === offsetB ? 0 : (offsetA < offsetB) ? -1 : 1;
        } else if ( (nodeC = getClosestAncestorIn(nodeB, nodeA, true)) ) {

            // Case 2: node C (container B or an ancestor) is a child node of A
            return offsetA <= getNodeIndex(nodeC) ? -1 : 1;
        } else if ( (nodeC = getClosestAncestorIn(nodeA, nodeB, true)) ) {

            // Case 3: node C (container A or an ancestor) is a child node of B
            return getNodeIndex(nodeC) < offsetB  ? -1 : 1;
        } else {

            // Case 4: containers are siblings or descendants of siblings
            root = getCommonAncestor(nodeA, nodeB);
            childA = (nodeA === root) ? root : getClosestAncestorIn(nodeA, root, true);
            childB = (nodeB === root) ? root : getClosestAncestorIn(nodeB, root, true);

            if (childA === childB) {
                // This shouldn't be possible

                throw new Error("comparePoints got to case 4 and childA and childB are the same!");
            } else {
                n = root.firstChild;
                while (n) {
                    if (n === childA) {
                        return -1;
                    } else if (n === childB) {
                        return 1;
                    }
                    n = n.nextSibling;
                }
                throw new Error("Should not be here!");
            }
        }
    }

    function fragmentFromNodeChildren(node) {
        var fragment = getDocument(node).createDocumentFragment(), child;
        while ( (child = node.firstChild) ) {
            fragment.appendChild(child);
        }
        return fragment;
    }

    function inspectNode(node) {
        if (!node) {
            return "[No node]";
        }
        if (isCharacterDataNode(node)) {
            return '"' + node.data + '"';
        } else if (node.nodeType == 1) {
            var idAttr = node.id ? ' id="' + node.id + '"' : "";
            return "<" + node.nodeName + idAttr + ">[" + node.childNodes.length + "]";
        } else {
            return node.nodeName;
        }
    }

    /**
     * @constructor
     */
    function NodeIterator(root) {
        this.root = root;
        this._next = root;
    }

    NodeIterator.prototype = {
        _current: null,

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            var n = this._current = this._next;
            var child, next;
            if (this._current) {
                child = n.firstChild;
                if (child) {
                    this._next = child;
                } else {
                    next = null;
                    while ((n !== this.root) && !(next = n.nextSibling)) {
                        n = n.parentNode;
                    }
                    this._next = next;
                }
            }
            return this._current;
        },

        detach: function() {
            this._current = this._next = this.root = null;
        }
    };

    function createIterator(root) {
        return new NodeIterator(root);
    }

    /**
     * @constructor
     */
    function DomPosition(node, offset) {
        this.node = node;
        this.offset = offset;
    }

    DomPosition.prototype = {
        equals: function(pos) {
            return this.node === pos.node & this.offset == pos.offset;
        },

        inspect: function() {
            return "[DomPosition(" + inspectNode(this.node) + ":" + this.offset + ")]";
        }
    };

    /**
     * @constructor
     */
    function DOMException(codeName) {
        this.code = this[codeName];
        this.codeName = codeName;
        this.message = "DOMException: " + this.codeName;
    }

    DOMException.prototype = {
        INDEX_SIZE_ERR: 1,
        HIERARCHY_REQUEST_ERR: 3,
        WRONG_DOCUMENT_ERR: 4,
        NO_MODIFICATION_ALLOWED_ERR: 7,
        NOT_FOUND_ERR: 8,
        NOT_SUPPORTED_ERR: 9,
        INVALID_STATE_ERR: 11
    };

    DOMException.prototype.toString = function() {
        return this.message;
    };

    api.dom = {
        arrayContains: arrayContains,
        isHtmlNamespace: isHtmlNamespace,
        parentElement: parentElement,
        getNodeIndex: getNodeIndex,
        getNodeLength: getNodeLength,
        getCommonAncestor: getCommonAncestor,
        isAncestorOf: isAncestorOf,
        getClosestAncestorIn: getClosestAncestorIn,
        isCharacterDataNode: isCharacterDataNode,
        insertAfter: insertAfter,
        splitDataNode: splitDataNode,
        getDocument: getDocument,
        getWindow: getWindow,
        getIframeWindow: getIframeWindow,
        getIframeDocument: getIframeDocument,
        getBody: getBody,
        getRootContainer: getRootContainer,
        comparePoints: comparePoints,
        inspectNode: inspectNode,
        fragmentFromNodeChildren: fragmentFromNodeChildren,
        createIterator: createIterator,
        DomPosition: DomPosition
    };

    api.DOMException = DOMException;
});rangy.createModule("DomRange", function(api, module) {
    api.requireModules( ["DomUtil"] );


    var dom = api.dom;
    var DomPosition = dom.DomPosition;
    var DOMException = api.DOMException;

    /*----------------------------------------------------------------------------------------------------------------*/

    // Utility functions

    function isNonTextPartiallySelected(node, range) {
        return (node.nodeType != 3) &&
               (dom.isAncestorOf(node, range.startContainer, true) || dom.isAncestorOf(node, range.endContainer, true));
    }

    function getRangeDocument(range) {
        return dom.getDocument(range.startContainer);
    }

    function dispatchEvent(range, type, args) {
        var listeners = range._listeners[type];
        if (listeners) {
            for (var i = 0, len = listeners.length; i < len; ++i) {
                listeners[i].call(range, {target: range, args: args});
            }
        }
    }

    function getBoundaryBeforeNode(node) {
        return new DomPosition(node.parentNode, dom.getNodeIndex(node));
    }

    function getBoundaryAfterNode(node) {
        return new DomPosition(node.parentNode, dom.getNodeIndex(node) + 1);
    }

    function insertNodeAtPosition(node, n, o) {
        var firstNodeInserted = node.nodeType == 11 ? node.firstChild : node;
        if (dom.isCharacterDataNode(n)) {
            if (o == n.length) {
                dom.insertAfter(node, n);
            } else {
                n.parentNode.insertBefore(node, o == 0 ? n : dom.splitDataNode(n, o));
            }
        } else if (o >= n.childNodes.length) {
            n.appendChild(node);
        } else {
            n.insertBefore(node, n.childNodes[o]);
        }
        return firstNodeInserted;
    }

    function cloneSubtree(iterator) {
        var partiallySelected;
        for (var node, frag = getRangeDocument(iterator.range).createDocumentFragment(), subIterator; node = iterator.next(); ) {
            partiallySelected = iterator.isPartiallySelectedSubtree();

            node = node.cloneNode(!partiallySelected);
            if (partiallySelected) {
                subIterator = iterator.getSubtreeIterator();
                node.appendChild(cloneSubtree(subIterator));
                subIterator.detach(true);
            }

            if (node.nodeType == 10) { // DocumentType
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }
            frag.appendChild(node);
        }
        return frag;
    }

    function iterateSubtree(rangeIterator, func, iteratorState) {
        var it, n;
        iteratorState = iteratorState || { stop: false };
        for (var node, subRangeIterator; node = rangeIterator.next(); ) {
            //log.debug("iterateSubtree, partially selected: " + rangeIterator.isPartiallySelectedSubtree(), nodeToString(node));
            if (rangeIterator.isPartiallySelectedSubtree()) {
                // The node is partially selected by the Range, so we can use a new RangeIterator on the portion of the
                // node selected by the Range.
                if (func(node) === false) {
                    iteratorState.stop = true;
                    return;
                } else {
                    subRangeIterator = rangeIterator.getSubtreeIterator();
                    iterateSubtree(subRangeIterator, func, iteratorState);
                    subRangeIterator.detach(true);
                    if (iteratorState.stop) {
                        return;
                    }
                }
            } else {
                // The whole node is selected, so we can use efficient DOM iteration to iterate over the node and its
                // descendant
                it = dom.createIterator(node);
                while ( (n = it.next()) ) {
                    if (func(n) === false) {
                        iteratorState.stop = true;
                        return;
                    }
                }
            }
        }
    }

    function deleteSubtree(iterator) {
        var subIterator;
        while (iterator.next()) {
            if (iterator.isPartiallySelectedSubtree()) {
                subIterator = iterator.getSubtreeIterator();
                deleteSubtree(subIterator);
                subIterator.detach(true);
            } else {
                iterator.remove();
            }
        }
    }

    function extractSubtree(iterator) {

        for (var node, frag = getRangeDocument(iterator.range).createDocumentFragment(), subIterator; node = iterator.next(); ) {


            if (iterator.isPartiallySelectedSubtree()) {
                node = node.cloneNode(false);
                subIterator = iterator.getSubtreeIterator();
                node.appendChild(extractSubtree(subIterator));
                subIterator.detach(true);
            } else {
                iterator.remove();
            }
            if (node.nodeType == 10) { // DocumentType
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }
            frag.appendChild(node);
        }
        return frag;
    }

    function getNodesInRange(range, nodeTypes, filter) {
        //log.info("getNodesInRange, " + nodeTypes.join(","));
        var filterNodeTypes = !!(nodeTypes && nodeTypes.length), regex;
        var filterExists = !!filter;
        if (filterNodeTypes) {
            regex = new RegExp("^(" + nodeTypes.join("|") + ")$");
        }

        var nodes = [];
        iterateSubtree(new RangeIterator(range, false), function(node) {
            if ((!filterNodeTypes || regex.test(node.nodeType)) && (!filterExists || filter(node))) {
                nodes.push(node);
            }
        });
        return nodes;
    }

    function inspect(range) {
        var name = (typeof range.getName == "undefined") ? "Range" : range.getName();
        return "[" + name + "(" + dom.inspectNode(range.startContainer) + ":" + range.startOffset + ", " +
                dom.inspectNode(range.endContainer) + ":" + range.endOffset + ")]";
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // RangeIterator code partially borrows from IERange by Tim Ryan (http://github.com/timcameronryan/IERange)

    /**
     * @constructor
     */
    function RangeIterator(range, clonePartiallySelectedTextNodes) {
        this.range = range;
        this.clonePartiallySelectedTextNodes = clonePartiallySelectedTextNodes;



        if (!range.collapsed) {
            this.sc = range.startContainer;
            this.so = range.startOffset;
            this.ec = range.endContainer;
            this.eo = range.endOffset;
            var root = range.commonAncestorContainer;

            if (this.sc === this.ec && dom.isCharacterDataNode(this.sc)) {
                this.isSingleCharacterDataNode = true;
                this._first = this._last = this._next = this.sc;
            } else {
                this._first = this._next = (this.sc === root && !dom.isCharacterDataNode(this.sc)) ?
                    this.sc.childNodes[this.so] : dom.getClosestAncestorIn(this.sc, root, true);
                this._last = (this.ec === root && !dom.isCharacterDataNode(this.ec)) ?
                    this.ec.childNodes[this.eo - 1] : dom.getClosestAncestorIn(this.ec, root, true);
            }

        }
    }

    RangeIterator.prototype = {
        _current: null,
        _next: null,
        _first: null,
        _last: null,
        isSingleCharacterDataNode: false,

        reset: function() {
            this._current = null;
            this._next = this._first;
        },

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            // Move to next node
            var current = this._current = this._next;
            if (current) {
                this._next = (current !== this._last) ? current.nextSibling : null;

                // Check for partially selected text nodes
                if (dom.isCharacterDataNode(current) && this.clonePartiallySelectedTextNodes) {
                    if (current === this.ec) {

                        (current = current.cloneNode(true)).deleteData(this.eo, current.length - this.eo);
                    }
                    if (this._current === this.sc) {

                        (current = current.cloneNode(true)).deleteData(0, this.so);
                    }
                }
            }

            return current;
        },

        remove: function() {
            var current = this._current, start, end;

            if (dom.isCharacterDataNode(current) && (current === this.sc || current === this.ec)) {
                start = (current === this.sc) ? this.so : 0;
                end = (current === this.ec) ? this.eo : current.length;
                if (start != end) {
                    current.deleteData(start, end - start);
                }
            } else {
                if (current.parentNode) {
                    current.parentNode.removeChild(current);
                } else {

                }
            }
        },

        // Checks if the current node is partially selected
        isPartiallySelectedSubtree: function() {
            var current = this._current;
            return isNonTextPartiallySelected(current, this.range);
        },

        getSubtreeIterator: function() {
            var subRange;
            if (this.isSingleCharacterDataNode) {
                subRange = this.range.cloneRange();
                subRange.collapse();
            } else {
                subRange = new Range(getRangeDocument(this.range));
                var current = this._current;
                var startContainer = current, startOffset = 0, endContainer = current, endOffset = dom.getNodeLength(current);

                if (dom.isAncestorOf(current, this.sc, true)) {
                    startContainer = this.sc;
                    startOffset = this.so;
                }
                if (dom.isAncestorOf(current, this.ec, true)) {
                    endContainer = this.ec;
                    endOffset = this.eo;
                }

                updateBoundaries(subRange, startContainer, startOffset, endContainer, endOffset);
            }
            return new RangeIterator(subRange, this.clonePartiallySelectedTextNodes);
        },

        detach: function(detachRange) {
            if (detachRange) {
                this.range.detach();
            }
            this.range = this._current = this._next = this._first = this._last = this.sc = this.so = this.ec = this.eo = null;
        }
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    // Exceptions

    /**
     * @constructor
     */
    function RangeException(codeName) {
        this.code = this[codeName];
        this.codeName = codeName;
        this.message = "RangeException: " + this.codeName;
    }

    RangeException.prototype = {
        BAD_BOUNDARYPOINTS_ERR: 1,
        INVALID_NODE_TYPE_ERR: 2
    };

    RangeException.prototype.toString = function() {
        return this.message;
    };

    /*----------------------------------------------------------------------------------------------------------------*/

    /**
     * Currently iterates through all nodes in the range on creation until I think of a decent way to do it
     * TODO: Look into making this a proper iterator, not requiring preloading everything first
     * @constructor
     */
    function RangeNodeIterator(range, nodeTypes, filter) {
        this.nodes = getNodesInRange(range, nodeTypes, filter);
        this._next = this.nodes[0];
        this._position = 0;
    }

    RangeNodeIterator.prototype = {
        _current: null,

        hasNext: function() {
            return !!this._next;
        },

        next: function() {
            this._current = this._next;
            this._next = this.nodes[ ++this._position ];
            return this._current;
        },

        detach: function() {
            this._current = this._next = this.nodes = null;
        }
    };

    var beforeAfterNodeTypes = [1, 3, 4, 5, 7, 8, 10];
    var rootContainerNodeTypes = [2, 9, 11];
    var readonlyNodeTypes = [5, 6, 10, 12];
    var insertableNodeTypes = [1, 3, 4, 5, 7, 8, 10, 11];
    var surroundNodeTypes = [1, 3, 4, 5, 7, 8];

    function createAncestorFinder(nodeTypes) {
        return function(node, selfIsAncestor) {
            var t, n = selfIsAncestor ? node : node.parentNode;
            while (n) {
                t = n.nodeType;
                if (dom.arrayContains(nodeTypes, t)) {
                    return n;
                }
                n = n.parentNode;
            }
            return null;
        };
    }

    var getRootContainer = dom.getRootContainer;
    var getDocumentOrFragmentContainer = createAncestorFinder( [9, 11] );
    var getReadonlyAncestor = createAncestorFinder(readonlyNodeTypes);
    var getDocTypeNotationEntityAncestor = createAncestorFinder( [6, 10, 12] );

    function assertNoDocTypeNotationEntityAncestor(node, allowSelf) {
        if (getDocTypeNotationEntityAncestor(node, allowSelf)) {
            throw new RangeException("INVALID_NODE_TYPE_ERR");
        }
    }

    function assertNotDetached(range) {
        if (!range.startContainer) {
            throw new DOMException("INVALID_STATE_ERR");
        }
    }

    function assertValidNodeType(node, invalidTypes) {
        if (!dom.arrayContains(invalidTypes, node.nodeType)) {
            throw new RangeException("INVALID_NODE_TYPE_ERR");
        }
    }

    function assertValidOffset(node, offset) {
        if (offset < 0 || offset > (dom.isCharacterDataNode(node) ? node.length : node.childNodes.length)) {
            throw new DOMException("INDEX_SIZE_ERR");
        }
    }

    function assertSameDocumentOrFragment(node1, node2) {
        if (getDocumentOrFragmentContainer(node1, true) !== getDocumentOrFragmentContainer(node2, true)) {
            throw new DOMException("WRONG_DOCUMENT_ERR");
        }
    }

    function assertNodeNotReadOnly(node) {
        if (getReadonlyAncestor(node, true)) {
            throw new DOMException("NO_MODIFICATION_ALLOWED_ERR");
        }
    }

    function assertNode(node, codeName) {
        if (!node) {
            throw new DOMException(codeName);
        }
    }

    function isOrphan(node) {
        return !dom.arrayContains(rootContainerNodeTypes, node.nodeType) && !getDocumentOrFragmentContainer(node, true);
    }

    function isValidOffset(node, offset) {
        return offset <= (dom.isCharacterDataNode(node) ? node.length : node.childNodes.length);
    }

    function assertRangeValid(range) {
        assertNotDetached(range);
        if (isOrphan(range.startContainer) || isOrphan(range.endContainer) ||
                !isValidOffset(range.startContainer, range.startOffset) ||
                !isValidOffset(range.endContainer, range.endOffset)) {
            throw new Error("Range error: Range is no longer valid after DOM mutation (" + range.inspect() + ")");
        }
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Test the browser's innerHTML support to decide how to implement createContextualFragment
    var styleEl = document.createElement("style");
    var htmlParsingConforms = false;
    try {
        styleEl.innerHTML = "<b>x</b>";
        htmlParsingConforms = (styleEl.firstChild.nodeType == 3); // Opera incorrectly creates an element node
    } catch (e) {
        // IE 6 and 7 throw
    }

    api.features.htmlParsingConforms = htmlParsingConforms;

    var createContextualFragment = htmlParsingConforms ?

        // Implementation as per HTML parsing spec, trusting in the browser's implementation of innerHTML. See
        // discussion and base code for this implementation at issue 67.
        // Spec: http://html5.org/specs/dom-parsing.html#extensions-to-the-range-interface
        // Thanks to Aleks Williams.
        function(fragmentStr) {
            // "Let node the context object's start's node."
            var node = this.startContainer;
            var doc = dom.getDocument(node);

            // "If the context object's start's node is null, raise an INVALID_STATE_ERR
            // exception and abort these steps."
            if (!node) {
                throw new DOMException("INVALID_STATE_ERR");
            }

            // "Let element be as follows, depending on node's interface:"
            // Document, Document Fragment: null
            var el = null;

            // "Element: node"
            if (node.nodeType == 1) {
                el = node;

            // "Text, Comment: node's parentElement"
            } else if (dom.isCharacterDataNode(node)) {
                el = dom.parentElement(node);
            }

            // "If either element is null or element's ownerDocument is an HTML document
            // and element's local name is "html" and element's namespace is the HTML
            // namespace"
            if (el === null || (
                el.nodeName == "HTML"
                && dom.isHtmlNamespace(dom.getDocument(el).documentElement)
                && dom.isHtmlNamespace(el)
            )) {

            // "let element be a new Element with "body" as its local name and the HTML
            // namespace as its namespace.""
                el = doc.createElement("body");
            } else {
                el = el.cloneNode(false);
            }

            // "If the node's document is an HTML document: Invoke the HTML fragment parsing algorithm."
            // "If the node's document is an XML document: Invoke the XML fragment parsing algorithm."
            // "In either case, the algorithm must be invoked with fragment as the input
            // and element as the context element."
            el.innerHTML = fragmentStr;

            // "If this raises an exception, then abort these steps. Otherwise, let new
            // children be the nodes returned."

            // "Let fragment be a new DocumentFragment."
            // "Append all new children to fragment."
            // "Return fragment."
            return dom.fragmentFromNodeChildren(el);
        } :

        // In this case, innerHTML cannot be trusted, so fall back to a simpler, non-conformant implementation that
        // previous versions of Rangy used (with the exception of using a body element rather than a div)
        function(fragmentStr) {
            assertNotDetached(this);
            var doc = getRangeDocument(this);
            var el = doc.createElement("body");
            el.innerHTML = fragmentStr;

            return dom.fragmentFromNodeChildren(el);
        };

    /*----------------------------------------------------------------------------------------------------------------*/

    var rangeProperties = ["startContainer", "startOffset", "endContainer", "endOffset", "collapsed",
        "commonAncestorContainer"];

    var s2s = 0, s2e = 1, e2e = 2, e2s = 3;
    var n_b = 0, n_a = 1, n_b_a = 2, n_i = 3;

    function RangePrototype() {}

    RangePrototype.prototype = {
        attachListener: function(type, listener) {
            this._listeners[type].push(listener);
        },

        compareBoundaryPoints: function(how, range) {
            assertRangeValid(this);
            assertSameDocumentOrFragment(this.startContainer, range.startContainer);

            var nodeA, offsetA, nodeB, offsetB;
            var prefixA = (how == e2s || how == s2s) ? "start" : "end";
            var prefixB = (how == s2e || how == s2s) ? "start" : "end";
            nodeA = this[prefixA + "Container"];
            offsetA = this[prefixA + "Offset"];
            nodeB = range[prefixB + "Container"];
            offsetB = range[prefixB + "Offset"];
            return dom.comparePoints(nodeA, offsetA, nodeB, offsetB);
        },

        insertNode: function(node) {
            assertRangeValid(this);
            assertValidNodeType(node, insertableNodeTypes);
            assertNodeNotReadOnly(this.startContainer);

            if (dom.isAncestorOf(node, this.startContainer, true)) {
                throw new DOMException("HIERARCHY_REQUEST_ERR");
            }

            // No check for whether the container of the start of the Range is of a type that does not allow
            // children of the type of node: the browser's DOM implementation should do this for us when we attempt
            // to add the node

            var firstNodeInserted = insertNodeAtPosition(node, this.startContainer, this.startOffset);
            this.setStartBefore(firstNodeInserted);
        },

        cloneContents: function() {
            assertRangeValid(this);

            var clone, frag;
            if (this.collapsed) {
                return getRangeDocument(this).createDocumentFragment();
            } else {
                if (this.startContainer === this.endContainer && dom.isCharacterDataNode(this.startContainer)) {
                    clone = this.startContainer.cloneNode(true);
                    clone.data = clone.data.slice(this.startOffset, this.endOffset);
                    frag = getRangeDocument(this).createDocumentFragment();
                    frag.appendChild(clone);
                    return frag;
                } else {
                    var iterator = new RangeIterator(this, true);
                    clone = cloneSubtree(iterator);
                    iterator.detach();
                }
                return clone;
            }
        },

        canSurroundContents: function() {
            assertRangeValid(this);
            assertNodeNotReadOnly(this.startContainer);
            assertNodeNotReadOnly(this.endContainer);

            // Check if the contents can be surrounded. Specifically, this means whether the range partially selects
            // no non-text nodes.
            var iterator = new RangeIterator(this, true);
            var boundariesInvalid = (iterator._first && (isNonTextPartiallySelected(iterator._first, this)) ||
                    (iterator._last && isNonTextPartiallySelected(iterator._last, this)));
            iterator.detach();
            return !boundariesInvalid;
        },

        surroundContents: function(node) {
            assertValidNodeType(node, surroundNodeTypes);

            if (!this.canSurroundContents()) {
                throw new RangeException("BAD_BOUNDARYPOINTS_ERR");
            }

            // Extract the contents
            var content = this.extractContents();

            // Clear the children of the node
            if (node.hasChildNodes()) {
                while (node.lastChild) {
                    node.removeChild(node.lastChild);
                }
            }

            // Insert the new node and add the extracted contents
            insertNodeAtPosition(node, this.startContainer, this.startOffset);
            node.appendChild(content);

            this.selectNode(node);
        },

        cloneRange: function() {
            assertRangeValid(this);
            var range = new Range(getRangeDocument(this));
            var i = rangeProperties.length, prop;
            while (i--) {
                prop = rangeProperties[i];
                range[prop] = this[prop];
            }
            return range;
        },

        toString: function() {
            assertRangeValid(this);
            var sc = this.startContainer;
            if (sc === this.endContainer && dom.isCharacterDataNode(sc)) {
                return (sc.nodeType == 3 || sc.nodeType == 4) ? sc.data.slice(this.startOffset, this.endOffset) : "";
            } else {
                var textBits = [], iterator = new RangeIterator(this, true);

                iterateSubtree(iterator, function(node) {
                    // Accept only text or CDATA nodes, not comments

                    if (node.nodeType == 3 || node.nodeType == 4) {
                        textBits.push(node.data);
                    }
                });
                iterator.detach();
                return textBits.join("");
            }
        },

        // The methods below are all non-standard. The following batch were introduced by Mozilla but have since
        // been removed from Mozilla.

        compareNode: function(node) {
            assertRangeValid(this);

            var parent = node.parentNode;
            var nodeIndex = dom.getNodeIndex(node);

            if (!parent) {
                throw new DOMException("NOT_FOUND_ERR");
            }

            var startComparison = this.comparePoint(parent, nodeIndex),
                endComparison = this.comparePoint(parent, nodeIndex + 1);

            if (startComparison < 0) { // Node starts before
                return (endComparison > 0) ? n_b_a : n_b;
            } else {
                return (endComparison > 0) ? n_a : n_i;
            }
        },

        comparePoint: function(node, offset) {
            assertRangeValid(this);
            assertNode(node, "HIERARCHY_REQUEST_ERR");
            assertSameDocumentOrFragment(node, this.startContainer);

            if (dom.comparePoints(node, offset, this.startContainer, this.startOffset) < 0) {
                return -1;
            } else if (dom.comparePoints(node, offset, this.endContainer, this.endOffset) > 0) {
                return 1;
            }
            return 0;
        },

        createContextualFragment: createContextualFragment,

        toHtml: function() {
            assertRangeValid(this);
            var container = getRangeDocument(this).createElement("div");
            container.appendChild(this.cloneContents());
            return container.innerHTML;
        },

        // touchingIsIntersecting determines whether this method considers a node that borders a range intersects
        // with it (as in WebKit) or not (as in Gecko pre-1.9, and the default)
        intersectsNode: function(node, touchingIsIntersecting) {
            assertRangeValid(this);
            assertNode(node, "NOT_FOUND_ERR");
            if (dom.getDocument(node) !== getRangeDocument(this)) {
                return false;
            }

            var parent = node.parentNode, offset = dom.getNodeIndex(node);
            assertNode(parent, "NOT_FOUND_ERR");

            var startComparison = dom.comparePoints(parent, offset, this.endContainer, this.endOffset),
                endComparison = dom.comparePoints(parent, offset + 1, this.startContainer, this.startOffset);

            return touchingIsIntersecting ? startComparison <= 0 && endComparison >= 0 : startComparison < 0 && endComparison > 0;
        },


        isPointInRange: function(node, offset) {
            assertRangeValid(this);
            assertNode(node, "HIERARCHY_REQUEST_ERR");
            assertSameDocumentOrFragment(node, this.startContainer);

            return (dom.comparePoints(node, offset, this.startContainer, this.startOffset) >= 0) &&
                   (dom.comparePoints(node, offset, this.endContainer, this.endOffset) <= 0);
        },

        // The methods below are non-standard and invented by me.

        // Sharing a boundary start-to-end or end-to-start does not count as intersection.
        intersectsRange: function(range, touchingIsIntersecting) {
            assertRangeValid(this);

            if (getRangeDocument(range) != getRangeDocument(this)) {
                throw new DOMException("WRONG_DOCUMENT_ERR");
            }

            var startComparison = dom.comparePoints(this.startContainer, this.startOffset, range.endContainer, range.endOffset),
                endComparison = dom.comparePoints(this.endContainer, this.endOffset, range.startContainer, range.startOffset);

            return touchingIsIntersecting ? startComparison <= 0 && endComparison >= 0 : startComparison < 0 && endComparison > 0;
        },

        intersection: function(range) {
            if (this.intersectsRange(range)) {
                var startComparison = dom.comparePoints(this.startContainer, this.startOffset, range.startContainer, range.startOffset),
                    endComparison = dom.comparePoints(this.endContainer, this.endOffset, range.endContainer, range.endOffset);

                var intersectionRange = this.cloneRange();

                if (startComparison == -1) {
                    intersectionRange.setStart(range.startContainer, range.startOffset);
                }
                if (endComparison == 1) {
                    intersectionRange.setEnd(range.endContainer, range.endOffset);
                }
                return intersectionRange;
            }
            return null;
        },

        union: function(range) {
            if (this.intersectsRange(range, true)) {
                var unionRange = this.cloneRange();
                if (dom.comparePoints(range.startContainer, range.startOffset, this.startContainer, this.startOffset) == -1) {
                    unionRange.setStart(range.startContainer, range.startOffset);
                }
                if (dom.comparePoints(range.endContainer, range.endOffset, this.endContainer, this.endOffset) == 1) {
                    unionRange.setEnd(range.endContainer, range.endOffset);
                }
                return unionRange;
            } else {
                throw new RangeException("Ranges do not intersect");
            }
        },

        containsNode: function(node, allowPartial) {
            if (allowPartial) {
                return this.intersectsNode(node, false);
            } else {
                return this.compareNode(node) == n_i;
            }
        },

        containsNodeContents: function(node) {
            return this.comparePoint(node, 0) >= 0 && this.comparePoint(node, dom.getNodeLength(node)) <= 0;
        },

        containsRange: function(range) {
            return this.intersection(range).equals(range);
        },

        containsNodeText: function(node) {
            var nodeRange = this.cloneRange();
            nodeRange.selectNode(node);
            var textNodes = nodeRange.getNodes([3]);
            if (textNodes.length > 0) {
                nodeRange.setStart(textNodes[0], 0);
                var lastTextNode = textNodes.pop();
                nodeRange.setEnd(lastTextNode, lastTextNode.length);
                var contains = this.containsRange(nodeRange);
                nodeRange.detach();
                return contains;
            } else {
                return this.containsNodeContents(node);
            }
        },

        createNodeIterator: function(nodeTypes, filter) {
            assertRangeValid(this);
            return new RangeNodeIterator(this, nodeTypes, filter);
        },

        getNodes: function(nodeTypes, filter) {
            assertRangeValid(this);
            return getNodesInRange(this, nodeTypes, filter);
        },

        getDocument: function() {
            return getRangeDocument(this);
        },

        collapseBefore: function(node) {
            assertNotDetached(this);

            this.setEndBefore(node);
            this.collapse(false);
        },

        collapseAfter: function(node) {
            assertNotDetached(this);

            this.setStartAfter(node);
            this.collapse(true);
        },

        getName: function() {
            return "DomRange";
        },

        equals: function(range) {
            return Range.rangesEqual(this, range);
        },

        inspect: function() {
            return inspect(this);
        }
    };

    function copyComparisonConstantsToObject(obj) {
        obj.START_TO_START = s2s;
        obj.START_TO_END = s2e;
        obj.END_TO_END = e2e;
        obj.END_TO_START = e2s;

        obj.NODE_BEFORE = n_b;
        obj.NODE_AFTER = n_a;
        obj.NODE_BEFORE_AND_AFTER = n_b_a;
        obj.NODE_INSIDE = n_i;
    }

    function copyComparisonConstants(constructor) {
        copyComparisonConstantsToObject(constructor);
        copyComparisonConstantsToObject(constructor.prototype);
    }

    function createRangeContentRemover(remover, boundaryUpdater) {
        return function() {
            assertRangeValid(this);

            var sc = this.startContainer, so = this.startOffset, root = this.commonAncestorContainer;

            var iterator = new RangeIterator(this, true);

            // Work out where to position the range after content removal
            var node, boundary;
            if (sc !== root) {
                node = dom.getClosestAncestorIn(sc, root, true);
                boundary = getBoundaryAfterNode(node);
                sc = boundary.node;
                so = boundary.offset;
            }

            // Check none of the range is read-only
            iterateSubtree(iterator, assertNodeNotReadOnly);

            iterator.reset();

            // Remove the content
            var returnValue = remover(iterator);
            iterator.detach();

            // Move to the new position
            boundaryUpdater(this, sc, so, sc, so);

            return returnValue;
        };
    }

    function createPrototypeRange(constructor, boundaryUpdater, detacher) {
        function createBeforeAfterNodeSetter(isBefore, isStart) {
            return function(node) {
                assertNotDetached(this);
                assertValidNodeType(node, beforeAfterNodeTypes);
                assertValidNodeType(getRootContainer(node), rootContainerNodeTypes);

                var boundary = (isBefore ? getBoundaryBeforeNode : getBoundaryAfterNode)(node);
                (isStart ? setRangeStart : setRangeEnd)(this, boundary.node, boundary.offset);
            };
        }

        function setRangeStart(range, node, offset) {
            var ec = range.endContainer, eo = range.endOffset;
            if (node !== range.startContainer || offset !== range.startOffset) {
                // Check the root containers of the range and the new boundary, and also check whether the new boundary
                // is after the current end. In either case, collapse the range to the new position
                if (getRootContainer(node) != getRootContainer(ec) || dom.comparePoints(node, offset, ec, eo) == 1) {
                    ec = node;
                    eo = offset;
                }
                boundaryUpdater(range, node, offset, ec, eo);
            }
        }

        function setRangeEnd(range, node, offset) {
            var sc = range.startContainer, so = range.startOffset;
            if (node !== range.endContainer || offset !== range.endOffset) {
                // Check the root containers of the range and the new boundary, and also check whether the new boundary
                // is after the current end. In either case, collapse the range to the new position
                if (getRootContainer(node) != getRootContainer(sc) || dom.comparePoints(node, offset, sc, so) == -1) {
                    sc = node;
                    so = offset;
                }
                boundaryUpdater(range, sc, so, node, offset);
            }
        }

        function setRangeStartAndEnd(range, node, offset) {
            if (node !== range.startContainer || offset !== range.startOffset || node !== range.endContainer || offset !== range.endOffset) {
                boundaryUpdater(range, node, offset, node, offset);
            }
        }

        constructor.prototype = new RangePrototype();

        api.util.extend(constructor.prototype, {
            setStart: function(node, offset) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeStart(this, node, offset);
            },

            setEnd: function(node, offset) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeEnd(this, node, offset);
            },

            setStartBefore: createBeforeAfterNodeSetter(true, true),
            setStartAfter: createBeforeAfterNodeSetter(false, true),
            setEndBefore: createBeforeAfterNodeSetter(true, false),
            setEndAfter: createBeforeAfterNodeSetter(false, false),

            collapse: function(isStart) {
                assertRangeValid(this);
                if (isStart) {
                    boundaryUpdater(this, this.startContainer, this.startOffset, this.startContainer, this.startOffset);
                } else {
                    boundaryUpdater(this, this.endContainer, this.endOffset, this.endContainer, this.endOffset);
                }
            },

            selectNodeContents: function(node) {
                // This doesn't seem well specified: the spec talks only about selecting the node's contents, which
                // could be taken to mean only its children. However, browsers implement this the same as selectNode for
                // text nodes, so I shall do likewise
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, true);

                boundaryUpdater(this, node, 0, node, dom.getNodeLength(node));
            },

            selectNode: function(node) {
                assertNotDetached(this);
                assertNoDocTypeNotationEntityAncestor(node, false);
                assertValidNodeType(node, beforeAfterNodeTypes);

                var start = getBoundaryBeforeNode(node), end = getBoundaryAfterNode(node);
                boundaryUpdater(this, start.node, start.offset, end.node, end.offset);
            },

            extractContents: createRangeContentRemover(extractSubtree, boundaryUpdater),

            deleteContents: createRangeContentRemover(deleteSubtree, boundaryUpdater),

            canSurroundContents: function() {
                assertRangeValid(this);
                assertNodeNotReadOnly(this.startContainer);
                assertNodeNotReadOnly(this.endContainer);

                // Check if the contents can be surrounded. Specifically, this means whether the range partially selects
                // no non-text nodes.
                var iterator = new RangeIterator(this, true);
                var boundariesInvalid = (iterator._first && (isNonTextPartiallySelected(iterator._first, this)) ||
                        (iterator._last && isNonTextPartiallySelected(iterator._last, this)));
                iterator.detach();
                return !boundariesInvalid;
            },

            detach: function() {
                detacher(this);
            },

            splitBoundaries: function() {
                assertRangeValid(this);


                var sc = this.startContainer, so = this.startOffset, ec = this.endContainer, eo = this.endOffset;
                var startEndSame = (sc === ec);

                if (dom.isCharacterDataNode(ec) && eo > 0 && eo < ec.length) {
                    dom.splitDataNode(ec, eo);

                }

                if (dom.isCharacterDataNode(sc) && so > 0 && so < sc.length) {

                    sc = dom.splitDataNode(sc, so);
                    if (startEndSame) {
                        eo -= so;
                        ec = sc;
                    } else if (ec == sc.parentNode && eo >= dom.getNodeIndex(sc)) {
                        eo++;
                    }
                    so = 0;

                }
                boundaryUpdater(this, sc, so, ec, eo);
            },

            normalizeBoundaries: function() {
                assertRangeValid(this);

                var sc = this.startContainer, so = this.startOffset, ec = this.endContainer, eo = this.endOffset;

                var mergeForward = function(node) {
                    var sibling = node.nextSibling;
                    if (sibling && sibling.nodeType == node.nodeType) {
                        ec = node;
                        eo = node.length;
                        node.appendData(sibling.data);
                        sibling.parentNode.removeChild(sibling);
                    }
                };

                var mergeBackward = function(node) {
                    var sibling = node.previousSibling;
                    if (sibling && sibling.nodeType == node.nodeType) {
                        sc = node;
                        var nodeLength = node.length;
                        so = sibling.length;
                        node.insertData(0, sibling.data);
                        sibling.parentNode.removeChild(sibling);
                        if (sc == ec) {
                            eo += so;
                            ec = sc;
                        } else if (ec == node.parentNode) {
                            var nodeIndex = dom.getNodeIndex(node);
                            if (eo == nodeIndex) {
                                ec = node;
                                eo = nodeLength;
                            } else if (eo > nodeIndex) {
                                eo--;
                            }
                        }
                    }
                };

                var normalizeStart = true;

                if (dom.isCharacterDataNode(ec)) {
                    if (ec.length == eo) {
                        mergeForward(ec);
                    }
                } else {
                    if (eo > 0) {
                        var endNode = ec.childNodes[eo - 1];
                        if (endNode && dom.isCharacterDataNode(endNode)) {
                            mergeForward(endNode);
                        }
                    }
                    normalizeStart = !this.collapsed;
                }

                if (normalizeStart) {
                    if (dom.isCharacterDataNode(sc)) {
                        if (so == 0) {
                            mergeBackward(sc);
                        }
                    } else {
                        if (so < sc.childNodes.length) {
                            var startNode = sc.childNodes[so];
                            if (startNode && dom.isCharacterDataNode(startNode)) {
                                mergeBackward(startNode);
                            }
                        }
                    }
                } else {
                    sc = ec;
                    so = eo;
                }

                boundaryUpdater(this, sc, so, ec, eo);
            },

            collapseToPoint: function(node, offset) {
                assertNotDetached(this);

                assertNoDocTypeNotationEntityAncestor(node, true);
                assertValidOffset(node, offset);

                setRangeStartAndEnd(this, node, offset);
            }
        });

        copyComparisonConstants(constructor);
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    // Updates commonAncestorContainer and collapsed after boundary change
    function updateCollapsedAndCommonAncestor(range) {
        range.collapsed = (range.startContainer === range.endContainer && range.startOffset === range.endOffset);
        range.commonAncestorContainer = range.collapsed ?
            range.startContainer : dom.getCommonAncestor(range.startContainer, range.endContainer);
    }

    function updateBoundaries(range, startContainer, startOffset, endContainer, endOffset) {
        var startMoved = (range.startContainer !== startContainer || range.startOffset !== startOffset);
        var endMoved = (range.endContainer !== endContainer || range.endOffset !== endOffset);

        range.startContainer = startContainer;
        range.startOffset = startOffset;
        range.endContainer = endContainer;
        range.endOffset = endOffset;

        updateCollapsedAndCommonAncestor(range);
        dispatchEvent(range, "boundarychange", {startMoved: startMoved, endMoved: endMoved});
    }

    function detach(range) {
        assertNotDetached(range);
        range.startContainer = range.startOffset = range.endContainer = range.endOffset = null;
        range.collapsed = range.commonAncestorContainer = null;
        dispatchEvent(range, "detach", null);
        range._listeners = null;
    }

    /**
     * @constructor
     */
    function Range(doc) {
        this.startContainer = doc;
        this.startOffset = 0;
        this.endContainer = doc;
        this.endOffset = 0;
        this._listeners = {
            boundarychange: [],
            detach: []
        };
        updateCollapsedAndCommonAncestor(this);
    }

    createPrototypeRange(Range, updateBoundaries, detach);

    api.rangePrototype = RangePrototype.prototype;

    Range.rangeProperties = rangeProperties;
    Range.RangeIterator = RangeIterator;
    Range.copyComparisonConstants = copyComparisonConstants;
    Range.createPrototypeRange = createPrototypeRange;
    Range.inspect = inspect;
    Range.getRangeDocument = getRangeDocument;
    Range.rangesEqual = function(r1, r2) {
        return r1.startContainer === r2.startContainer &&
               r1.startOffset === r2.startOffset &&
               r1.endContainer === r2.endContainer &&
               r1.endOffset === r2.endOffset;
    };

    api.DomRange = Range;
    api.RangeException = RangeException;
});rangy.createModule("WrappedRange", function(api, module) {
    api.requireModules( ["DomUtil", "DomRange"] );

    /**
     * @constructor
     */
    var WrappedRange;
    var dom = api.dom;
    var DomPosition = dom.DomPosition;
    var DomRange = api.DomRange;



    /*----------------------------------------------------------------------------------------------------------------*/

    /*
    This is a workaround for a bug where IE returns the wrong container element from the TextRange's parentElement()
    method. For example, in the following (where pipes denote the selection boundaries):

    <ul id="ul"><li id="a">| a </li><li id="b"> b |</li></ul>

    var range = document.selection.createRange();
    alert(range.parentElement().id); // Should alert "ul" but alerts "b"

    This method returns the common ancestor node of the following:
    - the parentElement() of the textRange
    - the parentElement() of the textRange after calling collapse(true)
    - the parentElement() of the textRange after calling collapse(false)
     */
    function getTextRangeContainerElement(textRange) {
        var parentEl = textRange.parentElement();

        var range = textRange.duplicate();
        range.collapse(true);
        var startEl = range.parentElement();
        range = textRange.duplicate();
        range.collapse(false);
        var endEl = range.parentElement();
        var startEndContainer = (startEl == endEl) ? startEl : dom.getCommonAncestor(startEl, endEl);

        return startEndContainer == parentEl ? startEndContainer : dom.getCommonAncestor(parentEl, startEndContainer);
    }

    function textRangeIsCollapsed(textRange) {
        return textRange.compareEndPoints("StartToEnd", textRange) == 0;
    }

    // Gets the boundary of a TextRange expressed as a node and an offset within that node. This function started out as
    // an improved version of code found in Tim Cameron Ryan's IERange (http://code.google.com/p/ierange/) but has
    // grown, fixing problems with line breaks in preformatted text, adding workaround for IE TextRange bugs, handling
    // for inputs and images, plus optimizations.
    function getTextRangeBoundaryPosition(textRange, wholeRangeContainerElement, isStart, isCollapsed) {
        var workingRange = textRange.duplicate();

        workingRange.collapse(isStart);
        var containerElement = workingRange.parentElement();

        // Sometimes collapsing a TextRange that's at the start of a text node can move it into the previous node, so
        // check for that
        // TODO: Find out when. Workaround for wholeRangeContainerElement may break this
        if (!dom.isAncestorOf(wholeRangeContainerElement, containerElement, true)) {
            containerElement = wholeRangeContainerElement;

        }



        // Deal with nodes that cannot "contain rich HTML markup". In practice, this means form inputs, images and
        // similar. See http://msdn.microsoft.com/en-us/library/aa703950%28VS.85%29.aspx
        if (!containerElement.canHaveHTML) {
            return new DomPosition(containerElement.parentNode, dom.getNodeIndex(containerElement));
        }

        var workingNode = dom.getDocument(containerElement).createElement("span");
        var comparison, workingComparisonType = isStart ? "StartToStart" : "StartToEnd";
        var previousNode, nextNode, boundaryPosition, boundaryNode;

        // Move the working range through the container's children, starting at the end and working backwards, until the
        // working range reaches or goes past the boundary we're interested in
        do {
            containerElement.insertBefore(workingNode, workingNode.previousSibling);
            workingRange.moveToElementText(workingNode);
        } while ( (comparison = workingRange.compareEndPoints(workingComparisonType, textRange)) > 0 &&
                workingNode.previousSibling);

        // We've now reached or gone past the boundary of the text range we're interested in
        // so have identified the node we want
        boundaryNode = workingNode.nextSibling;

        if (comparison == -1 && boundaryNode && dom.isCharacterDataNode(boundaryNode)) {
            // This is a character data node (text, comment, cdata). The working range is collapsed at the start of the
            // node containing the text range's boundary, so we move the end of the working range to the boundary point
            // and measure the length of its text to get the boundary's offset within the node.
            workingRange.setEndPoint(isStart ? "EndToStart" : "EndToEnd", textRange);


            var offset;

            if (/[\r\n]/.test(boundaryNode.data)) {
                /*
                For the particular case of a boundary within a text node containing line breaks (within a <pre> element,
                for example), we need a slightly complicated approach to get the boundary's offset in IE. The facts:

                - Each line break is represented as \r in the text node's data/nodeValue properties
                - Each line break is represented as \r\n in the TextRange's 'text' property
                - The 'text' property of the TextRange does not contain trailing line breaks

                To get round the problem presented by the final fact above, we can use the fact that TextRange's
                moveStart() and moveEnd() methods return the actual number of characters moved, which is not necessarily
                the same as the number of characters it was instructed to move. The simplest approach is to use this to
                store the characters moved when moving both the start and end of the range to the start of the document
                body and subtracting the start offset from the end offset (the "move-negative-gazillion" method).
                However, this is extremely slow when the document is large and the range is near the end of it. Clearly
                doing the mirror image (i.e. moving the range boundaries to the end of the document) has the same
                problem.

                Another approach that works is to use moveStart() to move the start boundary of the range up to the end
                boundary one character at a time and incrementing a counter with the value returned by the moveStart()
                call. However, the check for whether the start boundary has reached the end boundary is expensive, so
                this method is slow (although unlike "move-negative-gazillion" is largely unaffected by the location of
                the range within the document).

                The method below is a hybrid of the two methods above. It uses the fact that a string containing the
                TextRange's 'text' property with each \r\n converted to a single \r character cannot be longer than the
                text of the TextRange, so the start of the range is moved that length initially and then a character at
                a time to make up for any trailing line breaks not contained in the 'text' property. This has good
                performance in most situations compared to the previous two methods.
                */
                var tempRange = workingRange.duplicate();
                var rangeLength = tempRange.text.replace(/\r\n/g, "\r").length;

                offset = tempRange.moveStart("character", rangeLength);
                while ( (comparison = tempRange.compareEndPoints("StartToEnd", tempRange)) == -1) {
                    offset++;
                    tempRange.moveStart("character", 1);
                }
            } else {
                offset = workingRange.text.length;
            }
            boundaryPosition = new DomPosition(boundaryNode, offset);
        } else {


            // If the boundary immediately follows a character data node and this is the end boundary, we should favour
            // a position within that, and likewise for a start boundary preceding a character data node
            previousNode = (isCollapsed || !isStart) && workingNode.previousSibling;
            nextNode = (isCollapsed || isStart) && workingNode.nextSibling;



            if (nextNode && dom.isCharacterDataNode(nextNode)) {
                boundaryPosition = new DomPosition(nextNode, 0);
            } else if (previousNode && dom.isCharacterDataNode(previousNode)) {
                boundaryPosition = new DomPosition(previousNode, previousNode.length);
            } else {
                boundaryPosition = new DomPosition(containerElement, dom.getNodeIndex(workingNode));
            }
        }

        // Clean up
        workingNode.parentNode.removeChild(workingNode);

        return boundaryPosition;
    }

    // Returns a TextRange representing the boundary of a TextRange expressed as a node and an offset within that node.
    // This function started out as an optimized version of code found in Tim Cameron Ryan's IERange
    // (http://code.google.com/p/ierange/)
    function createBoundaryTextRange(boundaryPosition, isStart) {
        var boundaryNode, boundaryParent, boundaryOffset = boundaryPosition.offset;
        var doc = dom.getDocument(boundaryPosition.node);
        var workingNode, childNodes, workingRange = doc.body.createTextRange();
        var nodeIsDataNode = dom.isCharacterDataNode(boundaryPosition.node);

        if (nodeIsDataNode) {
            boundaryNode = boundaryPosition.node;
            boundaryParent = boundaryNode.parentNode;
        } else {
            childNodes = boundaryPosition.node.childNodes;
            boundaryNode = (boundaryOffset < childNodes.length) ? childNodes[boundaryOffset] : null;
            boundaryParent = boundaryPosition.node;
        }

        // Position the range immediately before the node containing the boundary
        workingNode = doc.createElement("span");

        // Making the working element non-empty element persuades IE to consider the TextRange boundary to be within the
        // element rather than immediately before or after it, which is what we want
        workingNode.innerHTML = "&#feff;";

        // insertBefore is supposed to work like appendChild if the second parameter is null. However, a bug report
        // for IERange suggests that it can crash the browser: http://code.google.com/p/ierange/issues/detail?id=12
        if (boundaryNode) {
            boundaryParent.insertBefore(workingNode, boundaryNode);
        } else {
            boundaryParent.appendChild(workingNode);
        }

        workingRange.moveToElementText(workingNode);
        workingRange.collapse(!isStart);

        // Clean up
        boundaryParent.removeChild(workingNode);

        // Move the working range to the text offset, if required
        if (nodeIsDataNode) {
            workingRange[isStart ? "moveStart" : "moveEnd"]("character", boundaryOffset);
        }

        return workingRange;
    }

    /*----------------------------------------------------------------------------------------------------------------*/

    if (api.features.implementsDomRange && (!api.features.implementsTextRange || !api.config.preferTextRange)) {
        // This is a wrapper around the browser's native DOM Range. It has two aims:
        // - Provide workarounds for specific browser bugs
        // - provide convenient extensions, which are inherited from Rangy's DomRange

        (function() {
            var rangeProto;
            var rangeProperties = DomRange.rangeProperties;
            var canSetRangeStartAfterEnd;

            function updateRangeProperties(range) {
                var i = rangeProperties.length, prop;
                while (i--) {
                    prop = rangeProperties[i];
                    range[prop] = range.nativeRange[prop];
                }
            }

            function updateNativeRange(range, startContainer, startOffset, endContainer,endOffset) {
                var startMoved = (range.startContainer !== startContainer || range.startOffset != startOffset);
                var endMoved = (range.endContainer !== endContainer || range.endOffset != endOffset);

                // Always set both boundaries for the benefit of IE9 (see issue 35)
                if (startMoved || endMoved) {
                    range.setEnd(endContainer, endOffset);
                    range.setStart(startContainer, startOffset);
                }
            }

            function detach(range) {
                range.nativeRange.detach();
                range.detached = true;
                var i = rangeProperties.length, prop;
                while (i--) {
                    prop = rangeProperties[i];
                    range[prop] = null;
                }
            }

            var createBeforeAfterNodeSetter;

            WrappedRange = function(range) {
                if (!range) {
                    throw new Error("Range must be specified");
                }
                this.nativeRange = range;
                updateRangeProperties(this);
            };

            DomRange.createPrototypeRange(WrappedRange, updateNativeRange, detach);

            rangeProto = WrappedRange.prototype;

            rangeProto.selectNode = function(node) {
                this.nativeRange.selectNode(node);
                updateRangeProperties(this);
            };

            rangeProto.deleteContents = function() {
                this.nativeRange.deleteContents();
                updateRangeProperties(this);
            };

            rangeProto.extractContents = function() {
                var frag = this.nativeRange.extractContents();
                updateRangeProperties(this);
                return frag;
            };

            rangeProto.cloneContents = function() {
                return this.nativeRange.cloneContents();
            };

            // TODO: Until I can find a way to programmatically trigger the Firefox bug (apparently long-standing, still
            // present in 3.6.8) that throws "Index or size is negative or greater than the allowed amount" for
            // insertNode in some circumstances, all browsers will have to use the Rangy's own implementation of
            // insertNode, which works but is almost certainly slower than the native implementation.
/*
            rangeProto.insertNode = function(node) {
                this.nativeRange.insertNode(node);
                updateRangeProperties(this);
            };
*/

            rangeProto.surroundContents = function(node) {
                this.nativeRange.surroundContents(node);
                updateRangeProperties(this);
            };

            rangeProto.collapse = function(isStart) {
                this.nativeRange.collapse(isStart);
                updateRangeProperties(this);
            };

            rangeProto.cloneRange = function() {
                return new WrappedRange(this.nativeRange.cloneRange());
            };

            rangeProto.refresh = function() {
                updateRangeProperties(this);
            };

            rangeProto.toString = function() {
                return this.nativeRange.toString();
            };

            // Create test range and node for feature detection

            var testTextNode = document.createTextNode("test");
            dom.getBody(document).appendChild(testTextNode);
            var range = document.createRange();

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for Firefox 2 bug that prevents moving the start of a Range to a point after its current end and
            // correct for it

            range.setStart(testTextNode, 0);
            range.setEnd(testTextNode, 0);

            try {
                range.setStart(testTextNode, 1);
                canSetRangeStartAfterEnd = true;

                rangeProto.setStart = function(node, offset) {
                    this.nativeRange.setStart(node, offset);
                    updateRangeProperties(this);
                };

                rangeProto.setEnd = function(node, offset) {
                    this.nativeRange.setEnd(node, offset);
                    updateRangeProperties(this);
                };

                createBeforeAfterNodeSetter = function(name) {
                    return function(node) {
                        this.nativeRange[name](node);
                        updateRangeProperties(this);
                    };
                };

            } catch(ex) {


                canSetRangeStartAfterEnd = false;

                rangeProto.setStart = function(node, offset) {
                    try {
                        this.nativeRange.setStart(node, offset);
                    } catch (ex) {
                        this.nativeRange.setEnd(node, offset);
                        this.nativeRange.setStart(node, offset);
                    }
                    updateRangeProperties(this);
                };

                rangeProto.setEnd = function(node, offset) {
                    try {
                        this.nativeRange.setEnd(node, offset);
                    } catch (ex) {
                        this.nativeRange.setStart(node, offset);
                        this.nativeRange.setEnd(node, offset);
                    }
                    updateRangeProperties(this);
                };

                createBeforeAfterNodeSetter = function(name, oppositeName) {
                    return function(node) {
                        try {
                            this.nativeRange[name](node);
                        } catch (ex) {
                            this.nativeRange[oppositeName](node);
                            this.nativeRange[name](node);
                        }
                        updateRangeProperties(this);
                    };
                };
            }

            rangeProto.setStartBefore = createBeforeAfterNodeSetter("setStartBefore", "setEndBefore");
            rangeProto.setStartAfter = createBeforeAfterNodeSetter("setStartAfter", "setEndAfter");
            rangeProto.setEndBefore = createBeforeAfterNodeSetter("setEndBefore", "setStartBefore");
            rangeProto.setEndAfter = createBeforeAfterNodeSetter("setEndAfter", "setStartAfter");

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for and correct Firefox 2 behaviour with selectNodeContents on text nodes: it collapses the range to
            // the 0th character of the text node
            range.selectNodeContents(testTextNode);
            if (range.startContainer == testTextNode && range.endContainer == testTextNode &&
                    range.startOffset == 0 && range.endOffset == testTextNode.length) {
                rangeProto.selectNodeContents = function(node) {
                    this.nativeRange.selectNodeContents(node);
                    updateRangeProperties(this);
                };
            } else {
                rangeProto.selectNodeContents = function(node) {
                    this.setStart(node, 0);
                    this.setEnd(node, DomRange.getEndOffset(node));
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for WebKit bug that has the beahviour of compareBoundaryPoints round the wrong way for constants
            // START_TO_END and END_TO_START: https://bugs.webkit.org/show_bug.cgi?id=20738

            range.selectNodeContents(testTextNode);
            range.setEnd(testTextNode, 3);

            var range2 = document.createRange();
            range2.selectNodeContents(testTextNode);
            range2.setEnd(testTextNode, 4);
            range2.setStart(testTextNode, 2);

            if (range.compareBoundaryPoints(range.START_TO_END, range2) == -1 &
                    range.compareBoundaryPoints(range.END_TO_START, range2) == 1) {
                // This is the wrong way round, so correct for it


                rangeProto.compareBoundaryPoints = function(type, range) {
                    range = range.nativeRange || range;
                    if (type == range.START_TO_END) {
                        type = range.END_TO_START;
                    } else if (type == range.END_TO_START) {
                        type = range.START_TO_END;
                    }
                    return this.nativeRange.compareBoundaryPoints(type, range);
                };
            } else {
                rangeProto.compareBoundaryPoints = function(type, range) {
                    return this.nativeRange.compareBoundaryPoints(type, range.nativeRange || range);
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Test for existence of createContextualFragment and delegate to it if it exists
            if (api.util.isHostMethod(range, "createContextualFragment")) {
                rangeProto.createContextualFragment = function(fragmentStr) {
                    return this.nativeRange.createContextualFragment(fragmentStr);
                };
            }

            /*--------------------------------------------------------------------------------------------------------*/

            // Clean up
            dom.getBody(document).removeChild(testTextNode);
            range.detach();
            range2.detach();
        })();

        api.createNativeRange = function(doc) {
            doc = doc || document;
            return doc.createRange();
        };
    } else if (api.features.implementsTextRange) {
        // This is a wrapper around a TextRange, providing full DOM Range functionality using rangy's DomRange as a
        // prototype

        WrappedRange = function(textRange) {
            this.textRange = textRange;
            this.refresh();
        };

        WrappedRange.prototype = new DomRange(document);

        WrappedRange.prototype.refresh = function() {
            var start, end;

            // TextRange's parentElement() method cannot be trusted. getTextRangeContainerElement() works around that.
            var rangeContainerElement = getTextRangeContainerElement(this.textRange);

            if (textRangeIsCollapsed(this.textRange)) {
                end = start = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, true, true);
            } else {

                start = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, true, false);
                end = getTextRangeBoundaryPosition(this.textRange, rangeContainerElement, false, false);
            }

            this.setStart(start.node, start.offset);
            this.setEnd(end.node, end.offset);
        };

        DomRange.copyComparisonConstants(WrappedRange);

        // Add WrappedRange as the Range property of the global object to allow expression like Range.END_TO_END to work
        var globalObj = (function() { return this; })();
        if (typeof globalObj.Range == "undefined") {
            globalObj.Range = WrappedRange;
        }

        api.createNativeRange = function(doc) {
            doc = doc || document;
            return doc.body.createTextRange();
        };
    }

    if (api.features.implementsTextRange) {
        WrappedRange.rangeToTextRange = function(range) {
            if (range.collapsed) {
                var tr = createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);



                return tr;

                //return createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);
            } else {
                var startRange = createBoundaryTextRange(new DomPosition(range.startContainer, range.startOffset), true);
                var endRange = createBoundaryTextRange(new DomPosition(range.endContainer, range.endOffset), false);
                var textRange = dom.getDocument(range.startContainer).body.createTextRange();
                textRange.setEndPoint("StartToStart", startRange);
                textRange.setEndPoint("EndToEnd", endRange);
                return textRange;
            }
        };
    }

    WrappedRange.prototype.getName = function() {
        return "WrappedRange";
    };

    api.WrappedRange = WrappedRange;

    api.createRange = function(doc) {
        doc = doc || document;
        return new WrappedRange(api.createNativeRange(doc));
    };

    api.createRangyRange = function(doc) {
        doc = doc || document;
        return new DomRange(doc);
    };

    api.createIframeRange = function(iframeEl) {
        return api.createRange(dom.getIframeDocument(iframeEl));
    };

    api.createIframeRangyRange = function(iframeEl) {
        return api.createRangyRange(dom.getIframeDocument(iframeEl));
    };

    api.addCreateMissingNativeApiListener(function(win) {
        var doc = win.document;
        if (typeof doc.createRange == "undefined") {
            doc.createRange = function() {
                return api.createRange(this);
            };
        }
        doc = win = null;
    });
});rangy.createModule("WrappedSelection", function(api, module) {
    // This will create a selection object wrapper that follows the Selection object found in the WHATWG draft DOM Range
    // spec (http://html5.org/specs/dom-range.html)

    api.requireModules( ["DomUtil", "DomRange", "WrappedRange"] );

    api.config.checkSelectionRanges = true;

    var BOOLEAN = "boolean",
        windowPropertyName = "_rangySelection",
        dom = api.dom,
        util = api.util,
        DomRange = api.DomRange,
        WrappedRange = api.WrappedRange,
        DOMException = api.DOMException,
        DomPosition = dom.DomPosition,
        getSelection,
        selectionIsCollapsed,
        CONTROL = "Control";



    function getWinSelection(winParam) {
        return (winParam || window).getSelection();
    }

    function getDocSelection(winParam) {
        return (winParam || window).document.selection;
    }

    // Test for the Range/TextRange and Selection features required
    // Test for ability to retrieve selection
    var implementsWinGetSelection = api.util.isHostMethod(window, "getSelection"),
        implementsDocSelection = api.util.isHostObject(document, "selection");

    var useDocumentSelection = implementsDocSelection && (!implementsWinGetSelection || api.config.preferTextRange);

    if (useDocumentSelection) {
        getSelection = getDocSelection;
        api.isSelectionValid = function(winParam) {
            var doc = (winParam || window).document, nativeSel = doc.selection;

            // Check whether the selection TextRange is actually contained within the correct document
            return (nativeSel.type != "None" || dom.getDocument(nativeSel.createRange().parentElement()) == doc);
        };
    } else if (implementsWinGetSelection) {
        getSelection = getWinSelection;
        api.isSelectionValid = function() {
            return true;
        };
    } else {
        module.fail("Neither document.selection or window.getSelection() detected.");
    }

    api.getNativeSelection = getSelection;

    var testSelection = getSelection();
    var testRange = api.createNativeRange(document);
    var body = dom.getBody(document);

    // Obtaining a range from a selection
    var selectionHasAnchorAndFocus = util.areHostObjects(testSelection, ["anchorNode", "focusNode"] &&
                                     util.areHostProperties(testSelection, ["anchorOffset", "focusOffset"]));
    api.features.selectionHasAnchorAndFocus = selectionHasAnchorAndFocus;

    // Test for existence of native selection extend() method
    var selectionHasExtend = util.isHostMethod(testSelection, "extend");
    api.features.selectionHasExtend = selectionHasExtend;

    // Test if rangeCount exists
    var selectionHasRangeCount = (typeof testSelection.rangeCount == "number");
    api.features.selectionHasRangeCount = selectionHasRangeCount;

    var selectionSupportsMultipleRanges = false;
    var collapsedNonEditableSelectionsSupported = true;

    if (util.areHostMethods(testSelection, ["addRange", "getRangeAt", "removeAllRanges"]) &&
            typeof testSelection.rangeCount == "number" && api.features.implementsDomRange) {

        (function() {
            var iframe = document.createElement("iframe");
            body.appendChild(iframe);

            var iframeDoc = dom.getIframeDocument(iframe);
            iframeDoc.open();
            iframeDoc.write("<html><head></head><body>12</body></html>");
            iframeDoc.close();

            var sel = dom.getIframeWindow(iframe).getSelection();
            var docEl = iframeDoc.documentElement;
            var iframeBody = docEl.lastChild, textNode = iframeBody.firstChild;

            // Test whether the native selection will allow a collapsed selection within a non-editable element
            var r1 = iframeDoc.createRange();
            r1.setStart(textNode, 1);
            r1.collapse(true);
            sel.addRange(r1);
            collapsedNonEditableSelectionsSupported = (sel.rangeCount == 1);
            sel.removeAllRanges();

            // Test whether the native selection is capable of supporting multiple ranges
            var r2 = r1.cloneRange();
            r1.setStart(textNode, 0);
            r2.setEnd(textNode, 2);
            sel.addRange(r1);
            sel.addRange(r2);

            selectionSupportsMultipleRanges = (sel.rangeCount == 2);

            // Clean up
            r1.detach();
            r2.detach();

            body.removeChild(iframe);
        })();
    }

    api.features.selectionSupportsMultipleRanges = selectionSupportsMultipleRanges;
    api.features.collapsedNonEditableSelectionsSupported = collapsedNonEditableSelectionsSupported;

    // ControlRanges
    var implementsControlRange = false, testControlRange;

    if (body && util.isHostMethod(body, "createControlRange")) {
        testControlRange = body.createControlRange();
        if (util.areHostProperties(testControlRange, ["item", "add"])) {
            implementsControlRange = true;
        }
    }
    api.features.implementsControlRange = implementsControlRange;

    // Selection collapsedness
    if (selectionHasAnchorAndFocus) {
        selectionIsCollapsed = function(sel) {
            return sel.anchorNode === sel.focusNode && sel.anchorOffset === sel.focusOffset;
        };
    } else {
        selectionIsCollapsed = function(sel) {
            return sel.rangeCount ? sel.getRangeAt(sel.rangeCount - 1).collapsed : false;
        };
    }

    function updateAnchorAndFocusFromRange(sel, range, backwards) {
        var anchorPrefix = backwards ? "end" : "start", focusPrefix = backwards ? "start" : "end";
        sel.anchorNode = range[anchorPrefix + "Container"];
        sel.anchorOffset = range[anchorPrefix + "Offset"];
        sel.focusNode = range[focusPrefix + "Container"];
        sel.focusOffset = range[focusPrefix + "Offset"];
    }

    function updateAnchorAndFocusFromNativeSelection(sel) {
        var nativeSel = sel.nativeSelection;
        sel.anchorNode = nativeSel.anchorNode;
        sel.anchorOffset = nativeSel.anchorOffset;
        sel.focusNode = nativeSel.focusNode;
        sel.focusOffset = nativeSel.focusOffset;
    }

    function updateEmptySelection(sel) {
        sel.anchorNode = sel.focusNode = null;
        sel.anchorOffset = sel.focusOffset = 0;
        sel.rangeCount = 0;
        sel.isCollapsed = true;
        sel._ranges.length = 0;
    }

    function getNativeRange(range) {
        var nativeRange;
        if (range instanceof DomRange) {
            nativeRange = range._selectionNativeRange;
            if (!nativeRange) {
                nativeRange = api.createNativeRange(dom.getDocument(range.startContainer));
                nativeRange.setEnd(range.endContainer, range.endOffset);
                nativeRange.setStart(range.startContainer, range.startOffset);
                range._selectionNativeRange = nativeRange;
                range.attachListener("detach", function() {

                    this._selectionNativeRange = null;
                });
            }
        } else if (range instanceof WrappedRange) {
            nativeRange = range.nativeRange;
        } else if (api.features.implementsDomRange && (range instanceof dom.getWindow(range.startContainer).Range)) {
            nativeRange = range;
        }
        return nativeRange;
    }

    function rangeContainsSingleElement(rangeNodes) {
        if (!rangeNodes.length || rangeNodes[0].nodeType != 1) {
            return false;
        }
        for (var i = 1, len = rangeNodes.length; i < len; ++i) {
            if (!dom.isAncestorOf(rangeNodes[0], rangeNodes[i])) {
                return false;
            }
        }
        return true;
    }

    function getSingleElementFromRange(range) {
        var nodes = range.getNodes();
        if (!rangeContainsSingleElement(nodes)) {
            throw new Error("getSingleElementFromRange: range " + range.inspect() + " did not consist of a single element");
        }
        return nodes[0];
    }

    function isTextRange(range) {
        return !!range && typeof range.text != "undefined";
    }

    function updateFromTextRange(sel, range) {
        // Create a Range from the selected TextRange
        var wrappedRange = new WrappedRange(range);
        sel._ranges = [wrappedRange];

        updateAnchorAndFocusFromRange(sel, wrappedRange, false);
        sel.rangeCount = 1;
        sel.isCollapsed = wrappedRange.collapsed;
    }

    function updateControlSelection(sel) {
        // Update the wrapped selection based on what's now in the native selection
        sel._ranges.length = 0;
        if (sel.docSelection.type == "None") {
            updateEmptySelection(sel);
        } else {
            var controlRange = sel.docSelection.createRange();
            if (isTextRange(controlRange)) {
                // This case (where the selection type is "Control" and calling createRange() on the selection returns
                // a TextRange) can happen in IE 9. It happens, for example, when all elements in the selected
                // ControlRange have been removed from the ControlRange and removed from the document.
                updateFromTextRange(sel, controlRange);
            } else {
                sel.rangeCount = controlRange.length;
                var range, doc = dom.getDocument(controlRange.item(0));
                for (var i = 0; i < sel.rangeCount; ++i) {
                    range = api.createRange(doc);
                    range.selectNode(controlRange.item(i));
                    sel._ranges.push(range);
                }
                sel.isCollapsed = sel.rangeCount == 1 && sel._ranges[0].collapsed;
                updateAnchorAndFocusFromRange(sel, sel._ranges[sel.rangeCount - 1], false);
            }
        }
    }

    function addRangeToControlSelection(sel, range) {
        var controlRange = sel.docSelection.createRange();
        var rangeElement = getSingleElementFromRange(range);

        // Create a new ControlRange containing all the elements in the selected ControlRange plus the element
        // contained by the supplied range
        var doc = dom.getDocument(controlRange.item(0));
        var newControlRange = dom.getBody(doc).createControlRange();
        for (var i = 0, len = controlRange.length; i < len; ++i) {
            newControlRange.add(controlRange.item(i));
        }
        try {
            newControlRange.add(rangeElement);
        } catch (ex) {
            throw new Error("addRange(): Element within the specified Range could not be added to control selection (does it have layout?)");
        }
        newControlRange.select();

        // Update the wrapped selection based on what's now in the native selection
        updateControlSelection(sel);
    }

    var getSelectionRangeAt;

    if (util.isHostMethod(testSelection,  "getRangeAt")) {
        getSelectionRangeAt = function(sel, index) {
            try {
                return sel.getRangeAt(index);
            } catch(ex) {
                return null;
            }
        };
    } else if (selectionHasAnchorAndFocus) {
        getSelectionRangeAt = function(sel) {
            var doc = dom.getDocument(sel.anchorNode);
            var range = api.createRange(doc);
            range.setStart(sel.anchorNode, sel.anchorOffset);
            range.setEnd(sel.focusNode, sel.focusOffset);

            // Handle the case when the selection was selected backwards (from the end to the start in the
            // document)
            if (range.collapsed !== this.isCollapsed) {
                range.setStart(sel.focusNode, sel.focusOffset);
                range.setEnd(sel.anchorNode, sel.anchorOffset);
            }

            return range;
        };
    }

    /**
     * @constructor
     */
    function WrappedSelection(selection, docSelection, win) {
        this.nativeSelection = selection;
        this.docSelection = docSelection;
        this._ranges = [];
        this.win = win;
        this.refresh();
    }

    api.getSelection = function(win) {
        win = win || window;
        var sel = win[windowPropertyName];
        var nativeSel = getSelection(win), docSel = implementsDocSelection ? getDocSelection(win) : null;
        if (sel) {
            sel.nativeSelection = nativeSel;
            sel.docSelection = docSel;
            sel.refresh(win);
        } else {
            sel = new WrappedSelection(nativeSel, docSel, win);
            win[windowPropertyName] = sel;
        }
        return sel;
    };

    api.getIframeSelection = function(iframeEl) {
        return api.getSelection(dom.getIframeWindow(iframeEl));
    };

    var selProto = WrappedSelection.prototype;

    function createControlSelection(sel, ranges) {
        // Ensure that the selection becomes of type "Control"
        var doc = dom.getDocument(ranges[0].startContainer);
        var controlRange = dom.getBody(doc).createControlRange();
        for (var i = 0, el; i < rangeCount; ++i) {
            el = getSingleElementFromRange(ranges[i]);
            try {
                controlRange.add(el);
            } catch (ex) {
                throw new Error("setRanges(): Element within the one of the specified Ranges could not be added to control selection (does it have layout?)");
            }
        }
        controlRange.select();

        // Update the wrapped selection based on what's now in the native selection
        updateControlSelection(sel);
    }

    // Selecting a range
    if (!useDocumentSelection && selectionHasAnchorAndFocus && util.areHostMethods(testSelection, ["removeAllRanges", "addRange"])) {
        selProto.removeAllRanges = function() {
            this.nativeSelection.removeAllRanges();
            updateEmptySelection(this);
        };

        var addRangeBackwards = function(sel, range) {
            var doc = DomRange.getRangeDocument(range);
            var endRange = api.createRange(doc);
            endRange.collapseToPoint(range.endContainer, range.endOffset);
            sel.nativeSelection.addRange(getNativeRange(endRange));
            sel.nativeSelection.extend(range.startContainer, range.startOffset);
            sel.refresh();
        };

        if (selectionHasRangeCount) {
            selProto.addRange = function(range, backwards) {
                if (implementsControlRange && implementsDocSelection && this.docSelection.type == CONTROL) {
                    addRangeToControlSelection(this, range);
                } else {
                    if (backwards && selectionHasExtend) {
                        addRangeBackwards(this, range);
                    } else {
                        var previousRangeCount;
                        if (selectionSupportsMultipleRanges) {
                            previousRangeCount = this.rangeCount;
                        } else {
                            this.removeAllRanges();
                            previousRangeCount = 0;
                        }
                        this.nativeSelection.addRange(getNativeRange(range));

                        // Check whether adding the range was successful
                        this.rangeCount = this.nativeSelection.rangeCount;

                        if (this.rangeCount == previousRangeCount + 1) {
                            // The range was added successfully

                            // Check whether the range that we added to the selection is reflected in the last range extracted from
                            // the selection
                            if (api.config.checkSelectionRanges) {
                                var nativeRange = getSelectionRangeAt(this.nativeSelection, this.rangeCount - 1);
                                if (nativeRange && !DomRange.rangesEqual(nativeRange, range)) {
                                    // Happens in WebKit with, for example, a selection placed at the start of a text node
                                    range = new WrappedRange(nativeRange);
                                }
                            }
                            this._ranges[this.rangeCount - 1] = range;
                            updateAnchorAndFocusFromRange(this, range, selectionIsBackwards(this.nativeSelection));
                            this.isCollapsed = selectionIsCollapsed(this);
                        } else {
                            // The range was not added successfully. The simplest thing is to refresh
                            this.refresh();
                        }
                    }
                }
            };
        } else {
            selProto.addRange = function(range, backwards) {
                if (backwards && selectionHasExtend) {
                    addRangeBackwards(this, range);
                } else {
                    this.nativeSelection.addRange(getNativeRange(range));
                    this.refresh();
                }
            };
        }

        selProto.setRanges = function(ranges) {
            if (implementsControlRange && ranges.length > 1) {
                createControlSelection(this, ranges);
            } else {
                this.removeAllRanges();
                for (var i = 0, len = ranges.length; i < len; ++i) {
                    this.addRange(ranges[i]);
                }
            }
        };
    } else if (util.isHostMethod(testSelection, "empty") && util.isHostMethod(testRange, "select") &&
               implementsControlRange && useDocumentSelection) {

        selProto.removeAllRanges = function() {
            // Added try/catch as fix for issue #21
            try {
                this.docSelection.empty();

                // Check for empty() not working (issue #24)
                if (this.docSelection.type != "None") {
                    // Work around failure to empty a control selection by instead selecting a TextRange and then
                    // calling empty()
                    var doc;
                    if (this.anchorNode) {
                        doc = dom.getDocument(this.anchorNode);
                    } else if (this.docSelection.type == CONTROL) {
                        var controlRange = this.docSelection.createRange();
                        if (controlRange.length) {
                            doc = dom.getDocument(controlRange.item(0)).body.createTextRange();
                        }
                    }
                    if (doc) {
                        var textRange = doc.body.createTextRange();
                        textRange.select();
                        this.docSelection.empty();
                    }
                }
            } catch(ex) {}
            updateEmptySelection(this);
        };

        selProto.addRange = function(range) {
            if (this.docSelection.type == CONTROL) {
                addRangeToControlSelection(this, range);
            } else {
                WrappedRange.rangeToTextRange(range).select();
                this._ranges[0] = range;
                this.rangeCount = 1;
                this.isCollapsed = this._ranges[0].collapsed;
                updateAnchorAndFocusFromRange(this, range, false);
            }
        };

        selProto.setRanges = function(ranges) {
            this.removeAllRanges();
            var rangeCount = ranges.length;
            if (rangeCount > 1) {
                createControlSelection(this, ranges);
            } else if (rangeCount) {
                this.addRange(ranges[0]);
            }
        };
    } else {
        module.fail("No means of selecting a Range or TextRange was found");
        return false;
    }

    selProto.getRangeAt = function(index) {
        if (index < 0 || index >= this.rangeCount) {
            throw new DOMException("INDEX_SIZE_ERR");
        } else {
            return this._ranges[index];
        }
    };

    var refreshSelection;

    if (useDocumentSelection) {
        refreshSelection = function(sel) {
            var range;
            if (api.isSelectionValid(sel.win)) {
                range = sel.docSelection.createRange();
            } else {
                range = dom.getBody(sel.win.document).createTextRange();
                range.collapse(true);
            }


            if (sel.docSelection.type == CONTROL) {
                updateControlSelection(sel);
            } else if (isTextRange(range)) {
                updateFromTextRange(sel, range);
            } else {
                updateEmptySelection(sel);
            }
        };
    } else if (util.isHostMethod(testSelection, "getRangeAt") && typeof testSelection.rangeCount == "number") {
        refreshSelection = function(sel) {
            if (implementsControlRange && implementsDocSelection && sel.docSelection.type == CONTROL) {
                updateControlSelection(sel);
            } else {
                sel._ranges.length = sel.rangeCount = sel.nativeSelection.rangeCount;
                if (sel.rangeCount) {
                    for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                        sel._ranges[i] = new api.WrappedRange(sel.nativeSelection.getRangeAt(i));
                    }
                    updateAnchorAndFocusFromRange(sel, sel._ranges[sel.rangeCount - 1], selectionIsBackwards(sel.nativeSelection));
                    sel.isCollapsed = selectionIsCollapsed(sel);
                } else {
                    updateEmptySelection(sel);
                }
            }
        };
    } else if (selectionHasAnchorAndFocus && typeof testSelection.isCollapsed == BOOLEAN && typeof testRange.collapsed == BOOLEAN && api.features.implementsDomRange) {
        refreshSelection = function(sel) {
            var range, nativeSel = sel.nativeSelection;
            if (nativeSel.anchorNode) {
                range = getSelectionRangeAt(nativeSel, 0);
                sel._ranges = [range];
                sel.rangeCount = 1;
                updateAnchorAndFocusFromNativeSelection(sel);
                sel.isCollapsed = selectionIsCollapsed(sel);
            } else {
                updateEmptySelection(sel);
            }
        };
    } else {
        module.fail("No means of obtaining a Range or TextRange from the user's selection was found");
        return false;
    }

    selProto.refresh = function(checkForChanges) {
        var oldRanges = checkForChanges ? this._ranges.slice(0) : null;
        refreshSelection(this);
        if (checkForChanges) {
            var i = oldRanges.length;
            if (i != this._ranges.length) {
                return false;
            }
            while (i--) {
                if (!DomRange.rangesEqual(oldRanges[i], this._ranges[i])) {
                    return false;
                }
            }
            return true;
        }
    };

    // Removal of a single range
    var removeRangeManually = function(sel, range) {
        var ranges = sel.getAllRanges(), removed = false;
        sel.removeAllRanges();
        for (var i = 0, len = ranges.length; i < len; ++i) {
            if (removed || range !== ranges[i]) {
                sel.addRange(ranges[i]);
            } else {
                // According to the draft WHATWG Range spec, the same range may be added to the selection multiple
                // times. removeRange should only remove the first instance, so the following ensures only the first
                // instance is removed
                removed = true;
            }
        }
        if (!sel.rangeCount) {
            updateEmptySelection(sel);
        }
    };

    if (implementsControlRange) {
        selProto.removeRange = function(range) {
            if (this.docSelection.type == CONTROL) {
                var controlRange = this.docSelection.createRange();
                var rangeElement = getSingleElementFromRange(range);

                // Create a new ControlRange containing all the elements in the selected ControlRange minus the
                // element contained by the supplied range
                var doc = dom.getDocument(controlRange.item(0));
                var newControlRange = dom.getBody(doc).createControlRange();
                var el, removed = false;
                for (var i = 0, len = controlRange.length; i < len; ++i) {
                    el = controlRange.item(i);
                    if (el !== rangeElement || removed) {
                        newControlRange.add(controlRange.item(i));
                    } else {
                        removed = true;
                    }
                }
                newControlRange.select();

                // Update the wrapped selection based on what's now in the native selection
                updateControlSelection(this);
            } else {
                removeRangeManually(this, range);
            }
        };
    } else {
        selProto.removeRange = function(range) {
            removeRangeManually(this, range);
        };
    }

    // Detecting if a selection is backwards
    var selectionIsBackwards;
    if (!useDocumentSelection && selectionHasAnchorAndFocus && api.features.implementsDomRange) {
        selectionIsBackwards = function(sel) {
            var backwards = false;
            if (sel.anchorNode) {
                backwards = (dom.comparePoints(sel.anchorNode, sel.anchorOffset, sel.focusNode, sel.focusOffset) == 1);
            }
            return backwards;
        };

        selProto.isBackwards = function() {
            return selectionIsBackwards(this);
        };
    } else {
        selectionIsBackwards = selProto.isBackwards = function() {
            return false;
        };
    }

    // Selection text
    // This is conformant to the new WHATWG DOM Range draft spec but differs from WebKit and Mozilla's implementation
    selProto.toString = function() {

        var rangeTexts = [];
        for (var i = 0, len = this.rangeCount; i < len; ++i) {
            rangeTexts[i] = "" + this._ranges[i];
        }
        return rangeTexts.join("");
    };

    function assertNodeInSameDocument(sel, node) {
        if (sel.anchorNode && (dom.getDocument(sel.anchorNode) !== dom.getDocument(node))) {
            throw new DOMException("WRONG_DOCUMENT_ERR");
        }
    }

    // No current browsers conform fully to the HTML 5 draft spec for this method, so Rangy's own method is always used
    selProto.collapse = function(node, offset) {
        assertNodeInSameDocument(this, node);
        var range = api.createRange(dom.getDocument(node));
        range.collapseToPoint(node, offset);
        this.removeAllRanges();
        this.addRange(range);
        this.isCollapsed = true;
    };

    selProto.collapseToStart = function() {
        if (this.rangeCount) {
            var range = this._ranges[0];
            this.collapse(range.startContainer, range.startOffset);
        } else {
            throw new DOMException("INVALID_STATE_ERR");
        }
    };

    selProto.collapseToEnd = function() {
        if (this.rangeCount) {
            var range = this._ranges[this.rangeCount - 1];
            this.collapse(range.endContainer, range.endOffset);
        } else {
            throw new DOMException("INVALID_STATE_ERR");
        }
    };

    // The HTML 5 spec is very specific on how selectAllChildren should be implemented so the native implementation is
    // never used by Rangy.
    selProto.selectAllChildren = function(node) {
        assertNodeInSameDocument(this, node);
        var range = api.createRange(dom.getDocument(node));
        range.selectNodeContents(node);
        this.removeAllRanges();
        this.addRange(range);
    };

    selProto.deleteFromDocument = function() {
        // Sepcial behaviour required for Control selections
        if (implementsControlRange && implementsDocSelection && this.docSelection.type == CONTROL) {
            var controlRange = this.docSelection.createRange();
            var element;
            while (controlRange.length) {
                element = controlRange.item(0);
                controlRange.remove(element);
                element.parentNode.removeChild(element);
            }
            this.refresh();
        } else if (this.rangeCount) {
            var ranges = this.getAllRanges();
            this.removeAllRanges();
            for (var i = 0, len = ranges.length; i < len; ++i) {
                ranges[i].deleteContents();
            }
            // The HTML5 spec says nothing about what the selection should contain after calling deleteContents on each
            // range. Firefox moves the selection to where the final selected range was, so we emulate that
            this.addRange(ranges[len - 1]);
        }
    };

    // The following are non-standard extensions
    selProto.getAllRanges = function() {
        return this._ranges.slice(0);
    };

    selProto.setSingleRange = function(range) {
        this.setRanges( [range] );
    };

    selProto.containsNode = function(node, allowPartial) {
        for (var i = 0, len = this._ranges.length; i < len; ++i) {
            if (this._ranges[i].containsNode(node, allowPartial)) {
                return true;
            }
        }
        return false;
    };

    selProto.toHtml = function() {
        var html = "";
        if (this.rangeCount) {
            var container = DomRange.getRangeDocument(this._ranges[0]).createElement("div");
            for (var i = 0, len = this._ranges.length; i < len; ++i) {
                container.appendChild(this._ranges[i].cloneContents());
            }
            html = container.innerHTML;
        }
        return html;
    };

    function inspect(sel) {
        var rangeInspects = [];
        var anchor = new DomPosition(sel.anchorNode, sel.anchorOffset);
        var focus = new DomPosition(sel.focusNode, sel.focusOffset);
        var name = (typeof sel.getName == "function") ? sel.getName() : "Selection";

        if (typeof sel.rangeCount != "undefined") {
            for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                rangeInspects[i] = DomRange.inspect(sel.getRangeAt(i));
            }
        }
        return "[" + name + "(Ranges: " + rangeInspects.join(", ") +
                ")(anchor: " + anchor.inspect() + ", focus: " + focus.inspect() + "]";

    }

    selProto.getName = function() {
        return "WrappedSelection";
    };

    selProto.inspect = function() {
        return inspect(this);
    };

    selProto.detach = function() {
        this.win[windowPropertyName] = null;
        this.win = this.anchorNode = this.focusNode = null;
    };

    WrappedSelection.inspect = inspect;

    api.Selection = WrappedSelection;

    api.selectionPrototype = selProto;

    api.addCreateMissingNativeApiListener(function(win) {
        if (typeof win.getSelection == "undefined") {
            win.getSelection = function() {
                return api.getSelection(this);
            };
        }
        win = null;
    });
});
/*jslint evil: true */

/**
    WYMeditor.editor.init
    =====================

    Initialize a wymeditor instance, including detecting the
    current browser and enabling the browser-specific subclass.
*/
WYMeditor.editor.prototype.init = function () {
    // Load the browser-specific subclass
    // If this browser isn't supported, do nothing
    var WymClass = false,
        SaxListener,
        prop,
        h,
        iframeHtml,
        boxHtml,
        aTools,
        sTools,
        oTool,
        sTool,
        i,
        aClasses,
        sClasses,
        oClass,
        sClass,
        aContainers,
        sContainers,
        sContainer,
        oContainer;

    if (jQuery.browser.msie) {
        WymClass = new WYMeditor.WymClassExplorer(this);
    } else if (jQuery.browser.mozilla) {
        WymClass = new WYMeditor.WymClassMozilla(this);
    } else if (jQuery.browser.opera) {
        WymClass = new WYMeditor.WymClassOpera(this);
    } else if (jQuery.browser.safari) {
        WymClass = new WYMeditor.WymClassSafari(this);
    }

    if (WymClass === false) {
        return;
    }

    if (jQuery.isFunction(this._options.preInit)) {
        this._options.preInit(this);
    }

    SaxListener = new WYMeditor.XhtmlSaxListener();
    jQuery.extend(SaxListener, WymClass);
    this.parser = new WYMeditor.XhtmlParser(SaxListener);

    if (this._options.styles || this._options.stylesheet) {
        this.configureEditorUsingRawCss();
    }

    this.helper = new WYMeditor.XmlHelper();

    // Extend the editor object with the browser-specific version.
    // We're not using jQuery.extend because we *want* to copy properties via
    // the prototype chain
    for (prop in WymClass) {
        /*jslint forin: true */
        // Explicitly not using hasOwnProperty for the inheritance here
        // because we want to go up the prototype chain to get all of the
        // browser-specific editor methods. This is kind of a code smell,
        // but works just fine.
        this[prop] = WymClass[prop];
    }

    // Load wymbox
    this._box = jQuery(this._element).
        hide().
        after(this._options.boxHtml).
        next().
        addClass('wym_box_' + this._index);

    // Store the instance index and replaced element in wymbox
    // but keep it compatible with jQuery < 1.2.3, see #122
    if (jQuery.isFunction(jQuery.fn.data)) {
        jQuery.data(this._box.get(0), WYMeditor.WYM_INDEX, this._index);
        jQuery.data(this._element.get(0), WYMeditor.WYM_INDEX, this._index);
    }

    h = WYMeditor.Helper;

    // Construct the iframe
    iframeHtml = this._options.iframeHtml;
    iframeHtml = h.replaceAll(iframeHtml, WYMeditor.INDEX, this._index);
    iframeHtml = h.replaceAll(
        iframeHtml,
        WYMeditor.IFRAME_BASE_PATH,
        this._options.iframeBasePath
    );

    // Construct wymbox
    boxHtml = jQuery(this._box).html();

    boxHtml = h.replaceAll(boxHtml, WYMeditor.LOGO, this._options.logoHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.TOOLS, this._options.toolsHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.CONTAINERS, this._options.containersHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.CLASSES, this._options.classesHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.HTML, this._options.htmlHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.IFRAME, iframeHtml);
    boxHtml = h.replaceAll(boxHtml, WYMeditor.STATUS, this._options.statusHtml);

    // Construct the tools list
    aTools = eval(this._options.toolsItems);
    sTools = "";

    for (i = 0; i < aTools.length; i += 1) {
        oTool = aTools[i];
        sTool = '';
        if (oTool.name && oTool.title) {
            sTool = this._options.toolsItemHtml;
        }
        sTool = h.replaceAll(sTool, WYMeditor.TOOL_NAME, oTool.name);
        sTool = h.replaceAll(
            sTool,
            WYMeditor.TOOL_TITLE,
            this._options.stringDelimiterLeft + oTool.title + this._options.stringDelimiterRight
        );
        sTool = h.replaceAll(sTool, WYMeditor.TOOL_CLASS, oTool.css);
        sTools += sTool;
    }

    boxHtml = h.replaceAll(boxHtml, WYMeditor.TOOLS_ITEMS, sTools);

    // Construct the classes list
    aClasses = eval(this._options.classesItems);
    sClasses = "";

    for (i = 0; i < aClasses.length; i += 1) {
        oClass = aClasses[i];
        sClass = '';
        if (oClass.name && oClass.title) {
            sClass = this._options.classesItemHtml;
        }
        sClass = h.replaceAll(sClass, WYMeditor.CLASS_NAME, oClass.name);
        sClass = h.replaceAll(sClass, WYMeditor.CLASS_TITLE, oClass.title);
        sClasses += sClass;
    }

    boxHtml = h.replaceAll(boxHtml, WYMeditor.CLASSES_ITEMS, sClasses);

    // Construct the containers list
    aContainers = eval(this._options.containersItems);
    sContainers = "";

    for (i = 0; i < aContainers.length; i += 1) {
        oContainer = aContainers[i];
        sContainer = '';
        if (oContainer.name && oContainer.title) {
            sContainer = this._options.containersItemHtml;
        }
        sContainer = h.replaceAll(
            sContainer,
            WYMeditor.CONTAINER_NAME,
            oContainer.name
        );
        sContainer = h.replaceAll(sContainer, WYMeditor.CONTAINER_TITLE,
            this._options.stringDelimiterLeft +
            oContainer.title +
            this._options.stringDelimiterRight);
        sContainer = h.replaceAll(
            sContainer,
            WYMeditor.CONTAINER_CLASS,
            oContainer.css
        );
        sContainers += sContainer;
    }

    boxHtml = h.replaceAll(boxHtml, WYMeditor.CONTAINERS_ITEMS, sContainers);

    // I10n
    boxHtml = this.replaceStrings(boxHtml);

    // Load the html in wymbox
    jQuery(this._box).html(boxHtml);

    // Hide the html value
    jQuery(this._box).find(this._options.htmlSelector).hide();

    this.loadSkin();
};

/**
    WYMeditor.editor.bindEvents
    ===========================

    Bind all event handlers including tool/container clicks, focus events
    and change events.
*/
WYMeditor.editor.prototype.bindEvents = function () {
    var wym = this,
        $html_val;

    // Handle click events on tools buttons
    jQuery(this._box).find(this._options.toolSelector).click(function () {
        wym._iframe.contentWindow.focus(); //See #154
        wym.exec(jQuery(this).attr(WYMeditor.NAME));
        return false;
    });

    // Handle click events on containers buttons
    jQuery(this._box).find(this._options.containerSelector).click(function () {
        wym.container(jQuery(this).attr(WYMeditor.NAME));
        return false;
    });

    // Handle keyup event on html value: set the editor value
    // Handle focus/blur events to check if the element has focus, see #147
    $html_val = jQuery(this._box).find(this._options.htmlValSelector);
    $html_val.keyup(function () {
        jQuery(wym._doc.body).html(jQuery(this).val());
    });
    $html_val.focus(function () {
        jQuery(this).toggleClass('hasfocus');
    });
    $html_val.blur(function () {
        jQuery(this).toggleClass('hasfocus');
    });

    // Handle click events on classes buttons
    jQuery(this._box).find(this._options.classSelector).click(function () {
        var aClasses = eval(wym._options.classesItems),
            sName = jQuery(this).attr(WYMeditor.NAME),

            oClass = WYMeditor.Helper.findByName(aClasses, sName),
            jqexpr;

        if (oClass) {
            jqexpr = oClass.expr;
            wym.toggleClass(sName, jqexpr);
        }
        wym._iframe.contentWindow.focus(); //See #154
        return false;
    });

    // Handle update event on update element
    jQuery(this._options.updateSelector).bind(this._options.updateEvent, function () {
        wym.update();
    });
};

WYMeditor.editor.prototype.ready = function () {
    return this._doc !== null;
};

/**
    WYMeditor.editor.box
    ====================

    Get the wymbox container.
*/
WYMeditor.editor.prototype.box = function () {
    return this._box;
};

/**
    WYMeditor.editor.html
    =====================

    Get or set the wymbox html value.
*/
WYMeditor.editor.prototype.html = function (html) {
    if (typeof html === 'string') {
        jQuery(this._doc.body).html(html);
        this.update();
    } else {
        return jQuery(this._doc.body).html();
    }
};

/**
    WYMeditor.editor.xhtml
    ======================

    Take the current editor's DOM and apply strict xhtml nesting rules to
    enforce a valid, well-formed, semantic xhtml result.
*/
WYMeditor.editor.prototype.xhtml = function () {
    var html;

    // Remove any of the placeholder nodes we've created for start/end content
    // insertion
    jQuery(this._doc.body).children(WYMeditor.BR).remove();

    return this.parser.parse(this.html());
};

/**
    WYMeditor.editor.exec
    =====================

    Execute a button command on the currently-selected container. The command
    can be anything from "indent this element" to "open a dialog to create a
    table."

    `cmd` is a string corresponding to the command that should be run, roughly
    matching the designMode execCommand strategy (and falling through to
    execCommand in some cases).
*/
WYMeditor.editor.prototype.exec = function (cmd) {
    var container, custom_run, _this = this;
    switch (cmd) {

    case WYMeditor.CREATE_LINK:
        container = this.container();
        if (container || this._selected_image) {
            this.dialog(WYMeditor.DIALOG_LINK);
        }
        break;

    case WYMeditor.INSERT_IMAGE:
        this.dialog(WYMeditor.DIALOG_IMAGE);
        break;

    case WYMeditor.INSERT_TABLE:
        this.dialog(WYMeditor.DIALOG_TABLE);
        break;

    case WYMeditor.PASTE:
        this.dialog(WYMeditor.DIALOG_PASTE);
        break;

    case WYMeditor.TOGGLE_HTML:
        this.update();
        this.toggleHtml();
        break;

    case WYMeditor.PREVIEW:
        this.dialog(WYMeditor.PREVIEW, this._options.dialogFeaturesPreview);
        break;

    case WYMeditor.INDENT:
        this.indent();
        break;

    case WYMeditor.OUTDENT:
        this.outdent();
        break;


    default:
        custom_run = false;
        jQuery.each(this._options.customCommands, function () {
            if (cmd === this.name) {
                custom_run = true;
                this.run.apply(_this);
                return false;
            }
        });
        if (!custom_run) {
            this._exec(cmd);
        }
        break;
    }
};

/**
    WYMeditor.editor.selection
    ==========================

    Override the default selection function to use rangy.
*/
WYMeditor.editor.prototype.selection = function () {
    if (window.rangy && !rangy.initialized) {
        rangy.init();
    }

    var iframe = this._iframe,
        sel = rangy.getIframeSelection(iframe);

    return sel;
};

/**
    WYMeditor.editor.selection
    ==========================

    Return the selected node.
*/
WYMeditor.editor.prototype.selected = function () {
    var sel = this.selection(),
        node = sel.focusNode;

    if (node) {
        if (node.nodeName === "#text") {
            return node.parentNode;
        } else {
            return node;
        }
    } else {
        return null;
    }
};

/**
    WYMeditor.editor.selection_collapsed
    ====================================

    Return true if all selections are collapsed, false otherwise.
*/
WYMeditor.editor.prototype.selection_collapsed = function () {
    var sel = this.selection(),
        collapsed = false;

    $.each(sel.getAllRanges(), function () {
        if (this.collapsed) {
            collapsed = true;
            //break
            return false;
        }
    });

    return collapsed;
};

/**
    WYMeditor.editor.selected_contains
    ==================================

    Return an array of nodes that match a jQuery selector
    within the current selection.
*/
WYMeditor.editor.prototype.selected_contains = function (selector) {
    var sel = this.selection(),
        matches = [];

    $.each(sel.getAllRanges(), function () {
        $.each(this.getNodes(), function () {
            if ($(this).is(selector)) {
                matches.push(this);
            }
        });
    });

    return matches;
};

/**
    WYMeditor.editor.selected_parents_contains
    ==================================

    Return an array of nodes that match the selector within
    the selection's parents.
*/
WYMeditor.editor.prototype.selected_parents_contains = function (selector) {
    var $matches = $([]),
        $selected = $(this.selected());
    if ($selected.is(selector)) {
        $matches = $matches.add($selected);
    }
    $matches = $matches.add($selected.parents(selector));
    return $matches;
};

/**
    WYMeditor.editor.container
    ==========================

    Get or set the selected container.
*/
WYMeditor.editor.prototype.container = function (sType) {
    if (typeof (sType) === 'undefined') {
        return this.selected();
    }

    var container = null,
        aTypes = null,
        newNode = null,
        blockquote,
        nodes,
        lgt,
        firstNode = null,
        x;

    if (sType.toLowerCase() === WYMeditor.TH) {
        container = this.container();

        // Find the TD or TH container
        switch (container.tagName.toLowerCase()) {

        case WYMeditor.TD:
        case WYMeditor.TH:
            break;
        default:
            aTypes = [WYMeditor.TD, WYMeditor.TH];
            container = this.findUp(this.container(), aTypes);
            break;
        }

        // If it exists, switch
        if (container !== null) {
            sType = WYMeditor.TD;
            if (container.tagName.toLowerCase() === WYMeditor.TD) {
                sType = WYMeditor.TH;
            }
            this.switchTo(container, sType);
            this.update();
        }
    } else {
        // Set the container type
        aTypes = [
            WYMeditor.P,
            WYMeditor.H1,
            WYMeditor.H2,
            WYMeditor.H3,
            WYMeditor.H4,
            WYMeditor.H5,
            WYMeditor.H6,
            WYMeditor.PRE,
            WYMeditor.BLOCKQUOTE
        ];
        container = this.findUp(this.container(), aTypes);

        if (container) {
            if (sType.toLowerCase() === WYMeditor.BLOCKQUOTE) {
                // Blockquotes must contain a block level element
                blockquote = this.findUp(
                    this.container(),
                    WYMeditor.BLOCKQUOTE
                );
                if (blockquote === null) {
                    newNode = this._doc.createElement(sType);
                    container.parentNode.insertBefore(newNode, container);
                    newNode.appendChild(container);
                    this.setFocusToNode(newNode.firstChild);
                } else {
                    nodes = blockquote.childNodes;
                    lgt = nodes.length;

                    if (lgt > 0) {
                        firstNode = nodes.item(0);
                    }
                    for (x = 0; x < lgt; x += 1) {
                        blockquote.parentNode.insertBefore(
                            nodes.item(0),
                            blockquote
                        );
                    }
                    blockquote.parentNode.removeChild(blockquote);
                    if (firstNode) {
                        this.setFocusToNode(firstNode);
                    }
                }
            } else {
                // Not a blockquote
                this.switchTo(container, sType);
            }

            this.update();
        }
    }

    return false;
};

/**
    WYMeditor.editor.toggleClass
    ============================

    Toggle a class on the selected element or one of its parents
*/
WYMeditor.editor.prototype.toggleClass = function (sClass, jqexpr) {
    var container = null;
    if (this._selected_image) {
        container = this._selected_image;
    } else {
        container = jQuery(this.selected());
    }
    container = jQuery(container).parentsOrSelf(jqexpr);
    jQuery(container).toggleClass(sClass);

    if (!jQuery(container).attr(WYMeditor.CLASS)) {
        jQuery(container).removeAttr(this._class);
    }
};

/**
    WYMeditor.editor.findUp
    =======================

    Return the first parent or self container, based on its type

    `filter` is a string or an array of strings on which to filter the container
*/
WYMeditor.editor.prototype.findUp = function (node, filter) {
    if (typeof (node) === 'undefined' || node === null) {
        return null;
    }

    if (node.nodeName === "#text") {
        // For text nodes, we need to look from the nodes container object
        node = node.parentNode;
    }
    var tagname = node.tagName.toLowerCase(),
        bFound,
        i;
    if (typeof (filter) === WYMeditor.STRING) {
        while (tagname !== filter && tagname !== WYMeditor.BODY) {
            node = node.parentNode;
            tagname = node.tagName.toLowerCase();
        }
    } else {
        bFound = false;
        while (!bFound && tagname !== WYMeditor.BODY) {
            for (i = 0; i < filter.length; i += 1) {
                if (tagname === filter[i]) {
                    bFound = true;
                    break;
                }
            }
            if (!bFound) {
                node = node.parentNode;
                if (node === null) {
                    // No parentNode, so we're not going to find anything
                    // up the ancestry chain that matches
                    return null;
                }
                tagname = node.tagName.toLowerCase();
            }
        }
    }

    if (tagname === WYMeditor.BODY) {
        return null;
    }

    return node;
};

/**
    WYMeditor.editor.switchTo
    =========================

    Switch the type of the given `node` to type `sType`
*/
WYMeditor.editor.prototype.switchTo = function (node, sType) {
    var newNode = this._doc.createElement(sType),
        html = jQuery(node).html();

    node.parentNode.replaceChild(newNode, node);
    jQuery(newNode).html(html);

    this.setFocusToNode(newNode);
};

WYMeditor.editor.prototype.replaceStrings = function (sVal) {
    var key;
    // Check if the language file has already been loaded
    // if not, get it via a synchronous ajax call
    if (!WYMeditor.STRINGS[this._options.lang]) {
        try {
            eval(jQuery.ajax({url: this._options.langPath +
                this._options.lang + '.js', async: false}).responseText);
        } catch (e) {
            WYMeditor.console.error(
                "WYMeditor: error while parsing language file."
            );
            return sVal;
        }
    }

    // Replace all the strings in sVal and return it
    for (key in WYMeditor.STRINGS[this._options.lang]) {
        if (WYMeditor.STRINGS[this._options.lang].hasOwnProperty(key)) {
            sVal = WYMeditor.Helper.replaceAll(
                sVal,
                this._options.stringDelimiterLeft + key + this._options.stringDelimiterRight,
                WYMeditor.STRINGS[this._options.lang][key]
            );
        }
    }
    return sVal;
};

WYMeditor.editor.prototype.encloseString = function (sVal) {
    return this._options.stringDelimiterLeft +
        sVal +
        this._options.stringDelimiterRight;
};

/**
    editor.status
    =============

    Print the given string as a status message.
*/
WYMeditor.editor.prototype.status = function (sMessage) {
    // Print status message
    jQuery(this._box).find(this._options.statusSelector).html(sMessage);
};

/**
    editor.update
    =============

    Update the element and textarea values.
*/
WYMeditor.editor.prototype.update = function () {
    var html;

    // Dirty fix to remove stray line breaks (#189)
    jQuery(this._doc.body).children(WYMeditor.BR).remove();

    html = this.xhtml();
    jQuery(this._element).val(html);
    jQuery(this._box).find(this._options.htmlValSelector).not('.hasfocus').val(html); //#147
    this.fixBodyHtml();
};

/**
    editor.fixBodyHtml
    ==================

    Adjust the editor body html to account for editing changes where
    perfect HTML is not optimal. For instance, <br> elements are useful between
    certain block elements.
*/
WYMeditor.editor.prototype.fixBodyHtml = function () {
    this.fixDoubleBr();
    this.spaceBlockingElements();
};

/**
    editor.spaceBlockingElements
    ============================

    Insert <br> elements between adjacent blocking elements and
    p elements, between block elements or blocking elements and the
    start/end of the document.
*/
WYMeditor.editor.prototype.spaceBlockingElements = function () {
    var blockingSelector = WYMeditor.BLOCKING_ELEMENTS.join(', '),

        $body = $(this._doc).find('body.wym_iframe'),
        children = $body.children(),
        placeholderNode = '<br _moz_editor_bogus_node="TRUE" _moz_dirty="">',
        $firstChild,
        $lastChild,
        blockSepSelector;

    // Make sure that we still have a bogus node at both the begining and end
    if (children.length > 0) {
        $firstChild = $(children[0]);
        $lastChild = $(children[children.length - 1]);

        if ($firstChild.is(blockingSelector)) {
            $firstChild.before(placeholderNode);
        }

        if ($lastChild.is(blockingSelector)) {
            $lastChild.after(placeholderNode);
        }
    }

    blockSepSelector = this._getBlockSepSelector();

    // Put placeholder nodes between consecutive blocking elements and between
    // blocking elements and normal block-level elements
    $body.find(blockSepSelector).before(placeholderNode);
};

/**
    editor._buildBlockSepSelector
    =============================

    Build a string representing a jquery selector that will find all
    elements which need a spacer <br> before them. This includes all consecutive
    blocking elements and between blocking elements and normal non-blocking
    elements.
*/
WYMeditor.editor.prototype._getBlockSepSelector = function () {
    if (typeof (this._blockSpacersSel) !== 'undefined') {
        return this._blockSpacersSel;
    }

    var blockCombo = [];
    // Consecutive blocking elements need separators
    $.each(WYMeditor.BLOCKING_ELEMENTS, function (indexO, elementO) {
        $.each(WYMeditor.BLOCKING_ELEMENTS, function (indexI, elementI) {
            blockCombo.push(elementO + ' + ' + elementI);
        });
    });

    // A blocking element either followed by or preceeded by a block elements
    // needs separators
    $.each(WYMeditor.BLOCKING_ELEMENTS, function (indexO, elementO) {
        $.each(WYMeditor.NON_BLOCKING_ELEMENTS, function (indexI, elementI) {
            blockCombo.push(elementO + ' + ' + elementI);
            blockCombo.push(elementI + ' + ' + elementO);
        });
    });
    this._blockSpacersSel = blockCombo.join(', ');
    return this._blockSpacersSel;
};

/**
    editor.fixDoubleBr
    ==================

    Remove the <br><br> elements that are inserted between
    paragraphs, usually after hitting enter from an existing paragraph.
*/
WYMeditor.editor.prototype.fixDoubleBr = function () {
    var $body = $(this._doc).find('body.wym_iframe'),
        $last_br;
    // Strip consecutive brs unless they're in a a pre tag
    $body.children('br + br').filter(':not(pre br)').remove();

    // Also remove any brs between two p's
    $body.find('p + br').next('p').prev('br').remove();

    // Remove brs floating at the end after a p
    $last_br = $body.find('p + br').slice(-1);
    if ($last_br.length > 0) {
        if ($last_br.next().length === 0) {
            $last_br.remove();
        }
    }
};

/**
    editor.dialog
    =============

    Open a dialog box
*/
WYMeditor.editor.prototype.dialog = function (dialogType, dialogFeatures, bodyHtml) {
    var features = dialogFeatures || this._wym._options.dialogFeatures,
        wDialog = window.open('', 'dialog', features),
        sBodyHtml,
        h = WYMeditor.Helper,
        dialogHtml,
        doc;

    if (wDialog) {
        sBodyHtml = "";

        switch (dialogType) {

        case (WYMeditor.DIALOG_LINK):
            sBodyHtml = this._options.dialogLinkHtml;
            break;
        case (WYMeditor.DIALOG_IMAGE):
            sBodyHtml = this._options.dialogImageHtml;
            break;
        case (WYMeditor.DIALOG_TABLE):
            sBodyHtml = this._options.dialogTableHtml;
            break;
        case (WYMeditor.DIALOG_PASTE):
            sBodyHtml = this._options.dialogPasteHtml;
            break;
        case (WYMeditor.PREVIEW):
            sBodyHtml = this._options.dialogPreviewHtml;
            break;
        default:
            sBodyHtml = bodyHtml;
            break;
        }

        // Construct the dialog
        dialogHtml = this._options.dialogHtml;
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.BASE_PATH,
            this._options.basePath
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.DIRECTION,
            this._options.direction
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.CSS_PATH,
            this._options.skinPath + WYMeditor.SKINS_DEFAULT_CSS
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.WYM_PATH,
            this._options.wymPath
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.JQUERY_PATH,
            this._options.jQueryPath
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.DIALOG_TITLE,
            this.encloseString(dialogType)
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.DIALOG_BODY,
            sBodyHtml
        );
        dialogHtml = h.replaceAll(
            dialogHtml,
            WYMeditor.INDEX,
            this._index
        );

        dialogHtml = this.replaceStrings(dialogHtml);

        doc = wDialog.document;
        doc.write(dialogHtml);
        doc.close();
    }
};

/**
    editor.toggleHtml
    =================

    Show/Hide the HTML textarea.
*/
WYMeditor.editor.prototype.toggleHtml = function () {
    jQuery(this._box).find(this._options.htmlSelector).toggle();
};

WYMeditor.editor.prototype.uniqueStamp = function () {
    var now = new Date();
    return "wym-" + now.getTime();
};

/**
    Paste the given array of paragraph-items at the given range inside the given $container.

    It has already been determined that the paragraph has multiple lines and
    that the container we're pasting to is a block container capable of accepting
    further nested blocks.
*/
WYMeditor.editor.prototype._handleMultilineBlockContainerPaste = function (wym, $container, range, paragraphStrings) {

    var i,
        blockSplitter,
        leftSide,
        rightSide,
        rangeNodeComparison,
        $splitRightParagraph,
        firstParagraphString,
        firstParagraphHtml,
        blockParent,
        blockParentType;


    // Now append all subsequent paragraphs
    $insertAfter = $(blockParent);

    // Just need to split the current container and put new block elements
    // in between
    blockSplitter = 'p';
    if ($container.is('li')) {
        // Instead of creating paragraphs on line breaks, we'll need to create li's
        blockSplitter = 'li';
    }
    // Split the selected element then build and insert the appropriate html
    // This accounts for cases where the start selection is at the
    // start of a node or in the middle of a text node by splitting the
    // text nodes using rangy's splitBoundaries()
    range.splitBoundaries(); // Split any partially-select text nodes
    blockParent = wym.findUp(
        range.startContainer,
        ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']
    );
    blockParentType = blockParent.tagName;
    leftSide = [];
    rightSide = [];
    $(blockParent).contents().each(function (index, element) {
        // Capture all of the dom nodes to the left and right of our
        // range. We can't remove them in the same step because that
        // loses the selection in webkit

        rangeNodeComparison = range.compareNode(element);
        if (rangeNodeComparison === range.NODE_BEFORE ||
                (rangeNodeComparison === range.NODE_BEFORE_AND_AFTER &&
                 range.startOffset === range.startContainer.length)) {
            // Because of the way splitBoundaries() works, the
            // collapsed selection might appear in the right-most index
            // of the border node, which means it will show up as
            //
            // eg. | is the selection and <> are text node boundaries
            // <foo|><bar>
            //
            // We detect that case by counting any
            // NODE_BEFORE_AND_AFTER result where the offset is at the
            // very end of the node as a member of the left side
            leftSide.push(element);
        } else {
            rightSide.push(element);
        }
    });
    // Now remove all of the left and right nodes
    for (i = 0; i < leftSide.length; i++) {
        $(leftSide[i]).remove();
    }
    for (i = 0; i < rightSide.length; i++) {
        $(rightSide[i]).remove();
    }

    // Rebuild our split nodes and add the inserted content
    if (leftSide.length > 0) {
        // We have left-of-selection content
        // Put the content back inside our blockParent
        $(blockParent).prepend(leftSide);
    }
    if (rightSide.length > 0) {
        // We have right-of-selection content.
        // Split it off in to a node of the same type after our
        // blockParent
        $splitRightParagraph = $('<' + blockParentType + '>' +
            '</' + blockParentType + '>', wym._doc);
        $splitRightParagraph.insertAfter($(blockParent));
        $splitRightParagraph.append(rightSide);
    }

    // Insert the first paragraph in to the current node, and then
    // start appending subsequent paragraphs
    firstParagraphString = paragraphStrings.splice(
        0,
        1
    )[0];
    firstParagraphHtml = firstParagraphString.split(WYMeditor.NEWLINE).join('<br />');
    $(blockParent).html($(blockParent).html() + firstParagraphHtml);

    // Now append all subsequent paragraphs
    $insertAfter = $(blockParent);
    for (i = 0; i < paragraphStrings.length; i++) {
        html = '<' + blockSplitter + '>' +
            (paragraphStrings[i].split(WYMeditor.NEWLINE).join('<br />')) +
            '</' + blockSplitter + '>';
        $insertAfter = $(html, wym._doc).insertAfter($insertAfter);
    }
};

/**
    editor.paste
    ============

    Paste text into the editor below the carret, used for "Paste from Word".

    Takes the string to insert as an argument. Two or more newlines separates
    paragraphs. May contain inline HTML.
*/
WYMeditor.editor.prototype.paste = function (str) {
    var container = this.selected(),
        $container,
        html = '',
        paragraphs,
        focusNode,
        i,
        l,
        isSingleLine = false,
        sel,
        textNode,
        wym,
        range;
    wym = this;
    sel = rangy.getIframeSelection(wym._iframe);
    range = sel.getRangeAt(0);
    $container = $(container);

    // Start by collapsing the range to the start of the selection. We're
    // punting on implementing a paste that also replaces existing content for
    // now,
    range.collapse(true); // Collapse to the the begining of the selection

    // Split string into paragraphs by two or more newlines
    paragraphStrings = str.split(new RegExp(WYMeditor.NEWLINE + '{2,}', 'g'));

    if (paragraphStrings.length === 1) {
        // This is a one-line paste, which is an easy case.
        // We try not to wrap these in paragraphs
        isSingleLine = true;
    }

    if (typeof container === 'undefined' ||
            (container && container.tagName.toLowerCase() === WYMeditor.BODY)) {
        // No selection, or body selection. Paste at the end of the document

        if (isSingleLine) {
            // Easy case. Wrap the string in p tags
            paragraphs = jQuery(
                '<p>' + paragraphStrings[0] + '</p>',
                this._doc
            ).appendTo(this._doc.body);
        } else {
            // Need to build paragraphs and insert them at the end
            blockSplitter = 'p';
            for (i = paragraphStrings.length - 1; i >= 0; i -= 1) {
                // Going backwards because rangy.insertNode leaves the
                // selection in front of the inserted node
                html = '<' + blockSplitter + '>' +
                    (paragraphStrings[i].split(WYMeditor.NEWLINE).join('<br />')) +
                    '</' + blockSplitter + '>';
                // Build multiple nodes from the HTML because ie6 chokes
                // creating multiple nodes implicitly via jquery
                var insertionNodes = $(html, wym._doc);
                for (j = insertionNodes.length - 1; j >= 0; j--) {
                    // Loop backwards through all of the nodes because
                    // insertNode moves that direction
                    range.insertNode(insertionNodes[j]);
                }
            }
        }
    } else {
        // Pasting inside an existing element
        if (isSingleLine || $container.is('pre')) {
            // Easy case. Insert a text node at the current selection
            textNode = this._doc.createTextNode(str);
            range.insertNode(textNode);
        } else if ($container.is('p,h1,h2,h3,h4,h5,h6,li')) {
            wym._handleMultilineBlockContainerPaste(wym, $container, range, paragraphStrings);
        } else {
            // We're in a container that doesn't accept nested paragraphs (eg. td). Use
            // <br> separators everywhere instead
            textNodesToInsert = str.split(WYMeditor.NEWLINE);
            for (i = textNodesToInsert.length - 1; i >= 0; i -= 1) {
                // Going backwards because rangy.insertNode leaves the
                // selection in front of the inserted node
                textNode = this._doc.createTextNode(textNodesToInsert[i]);
                range.insertNode(textNode);
                if (i > 0) {
                    // Don't insert an opening br
                    range.insertNode($('<br />', wym._doc).get(0));
                }
            }
        }
    }
};

WYMeditor.editor.prototype.insert = function (html) {
    // Do we have a selection?
    var selection = this._iframe.contentWindow.getSelection(),
        range,
        node;
    if (selection.focusNode !== null) {
        // Overwrite selection with provided html
        range = selection.getRangeAt(0);
        node = range.createContextualFragment(html);
        range.deleteContents();
        range.insertNode(node);
    } else {
        // Fall back to the internal paste function if there's no selection
        this.paste(html);
    }
};

WYMeditor.editor.prototype.wrap = function (left, right) {
    this.insert(
        left + this._iframe.contentWindow.getSelection().toString() + right
    );
};

WYMeditor.editor.prototype.unwrap = function () {
    this.insert(this._iframe.contentWindow.getSelection().toString());
};

WYMeditor.editor.prototype.setFocusToNode = function (node, toStart) {
    var range = this._doc.createRange(),
        selection = this._iframe.contentWindow.getSelection();
    toStart = toStart ? 0 : 1;

    range.selectNodeContents(node);
    selection.addRange(range);
    selection.collapse(node, toStart);
    this._iframe.contentWindow.focus();
};

WYMeditor.editor.prototype.addCssRules = function (doc, aCss) {
    var styles = doc.styleSheets[0],
        i,
        oCss;
    if (styles) {
        for (i = 0; i < aCss.length; i += 1) {
            oCss = aCss[i];
            if (oCss.name && oCss.css) {
                this.addCssRule(styles, oCss);
            }
        }
    }
};

/**
    editor._indentSingleItem
    ========================

    Indent a single list item via the dom, ensuring that the selected node moves in
    exactly one level and all other nodes stay at the same level.
 */
WYMeditor.editor.prototype._indentSingleItem = function (listItem) {
    var $spacerList,
        $prevList,
        $listContents,

        listType,
        itemContents,
        spacerHtml,

        $prevLi,
        $prevSubList,
        $children,

        $sublistContents,

        containerHtml,

        $contents,

        $maybeListSpacer,
        $maybePreviousSublist,

        $nextSublist,

        $spacer,
        $spacerContents;

    $liToIndent = $(listItem);
    listType = $liToIndent.parent()[0].tagName.toLowerCase();

    // Extract any non-list children so they can be inserted
    // back in the list item after it is moved
    itemContents = $liToIndent.contents().not('ol,ul');

    if ($liToIndent.prev().length === 0 && $liToIndent.parent().not('ul,ol,li')) {
        // First item at the root level of a list
        // Going to need a spacer list item
        spacerHtml = '<li class="spacer_li">' +
            '<' + listType + '></' + listType + '>' +
            '</li>';
        $liToIndent.before(spacerHtml);
        $spacerList = $liToIndent.prev().find(listType);
        $liToIndent.children().unwrap();
        $spacerList.append($liToIndent);

    } else if ($liToIndent.prev().contents().last().is(listType)) {
        // We have a sublist at the appropriate level as a previous sibling.
        // Leave the children where they are and join the previous sublist
        $prevLi = $liToIndent.prev();
        $prevSubList = $prevLi.contents().last();
        $children = $liToIndent.children();
        $children.unwrap();
        // Join our node at the end of the target sublist
        $prevSubList.append($liToIndent);

        // Stick all of the children at the end of the previous li
        $children.detach();
        $prevLi.append($children);
        // If the first child is of the same list type, join them
        if ($children.first().is(listType)) {
            $sublistContents = $children.first().children();
            $sublistContents.unwrap();
            $sublistContents.detach();
            $prevSubList.append($sublistContents);
        }
    } else if ($liToIndent.children('ol,ul').length === 0) {
        // No sublist to join.
        // Leave the children where they are and join the previous list
        $prevList = $liToIndent.prev().filter('li');
        $liToIndent.children().unwrap();

        if ($prevList.children('ol,ul').length === 0) {
            // The previous list doesn't have a sublist for us to join yet, so
            // we need to create a spot for our li to nest
            containerHtml = '<' + listType + '></' + listType + '>';
            $prevList.append(containerHtml);
        }

        $prevList.children('ol,ul').last().append($liToIndent);
    } else {
        // We have a sublist to join, so just jump to the front there and leave
        // the children where they are
        $contents = $liToIndent.contents().unwrap();
        $contents.wrapAll('<li class="spacer_li"></li>');
        $contents.filter('ol,ul').first().prepend($liToIndent);
    }

    // Put the non-list content back inside the li
    $liToIndent.prepend(itemContents);

    // If we just created lists next to eachother, join them
    $maybeListSpacer = $liToIndent.parent().parent('li.spacer_li');
    if ($maybeListSpacer.length === 1) {
        $maybePreviousSublist = $maybeListSpacer.prev().filter('li').contents().last();
        if ($maybePreviousSublist.is(listType)) {
            // The last child (including text nodes) of the previous li is the
            // same type of list that we just had to wrap in a listSpacer.
            // Join them.
            $listContents = $liToIndent.parent().contents();
            $maybeListSpacer.detach();
            $maybePreviousSublist.append($listContents);
        } else if ($maybeListSpacer.next('li').contents().first().is(listType)) {
            // The first child (including text nodes) of the next li is the same
            // type of list we just wrapped in a listSpacer. Join them.
            $nextSublist = $maybeListSpacer.next('li').children().first();
            $listContents = $liToIndent.parent().contents();
            $maybeListSpacer.detach();
            $nextSublist.prepend($listContents);
        } else if ($maybeListSpacer.prev().is('li')) {
            // There is a normal li before our spacer, but it doesn't have
            // a proper sublist. Just join their contents
            $prevList = $maybeListSpacer.prev();
            $maybeListSpacer.detach();
            $prevList.append($maybeListSpacer.contents());
        }
    }

    // If we eliminated the need for a spacer_li, remove it
    if ($liToIndent.next().is('.spacer_li')) {
        $spacer = $liToIndent.next('.spacer_li');
        $spacerContents = $spacer.contents();
        $spacerContents.detach();
        $liToIndent.append($spacerContents);
        $spacer.remove();
    }

};

/**
    editor._outdentSingleItem
    ========================

    Outdent a single list item via the dom, ensuring that the selected node moves in
    exactly one level and all other nodes stay at the same level.
 */
WYMeditor.editor.prototype._outdentSingleItem = function (listItem) {
    var $liToIndent,
        $parentItem,
        listType,

        $subsequentItems,
        $childLists,
        $orphannedContent,

        $sublist,
        $maybeConsecutiveLists;

    $liToIndent = $(listItem);

    // If this list item isn't already indented at least one level, don't allow
    // outdenting
    if (!$liToIndent.parent().parent().is('ol,ul,li')) {
        return;
    }

    // This item is in a sublist. Firefox doesn't properly dedent this
    // as it's own item, instead it just tacks its content to the end of
    // the parent item after the sublist
    $parentItem = $liToIndent.parent().parent('li');
    listType = $liToIndent.parent()[0].tagName.toLowerCase();

    // If this li has li's following, those will need to be moved as
    // sublist elements after the outdent
    $subsequentItems = $liToIndent.nextAll('li');

    $liToIndent.detach();
    $parentItem.after($liToIndent);

    // If this node has one or more sublist, they will need to be indented
    // by one with a fake parent to hold their previous position
    $childLists = $liToIndent.children('ol,ul');
    $orphannedContent = $liToIndent.contents().not('ol,ul');

    if ($childLists.length > 0) {
        $childLists.each(function (index, childList) {
            var $childList = $(childList),
                spacerListHtml;
            $childList.detach();

            spacerListHtml = '<' + listType + '>' +
                '<li class="spacer_li"></li>' +
                '</' + listType + '>';
            $liToIndent.append(spacerListHtml);
            $liToIndent.children(listType).last().children('li').append($childList);
        });
    }

    if ($subsequentItems.length > 0) {
        // Nest the previously-subsequent items inside the list to
        // retain order and their indent level
        $sublist = $subsequentItems;
        $sublist.detach();

        $liToIndent.append("<" + listType + "></" + listType + ">");
        $liToIndent.find(listType).last().append($subsequentItems);

        // If we just created lists next to eachother, join them
        $maybeConsecutiveLists = $liToIndent
            .children(listType + ' + ' + listType);
        if ($maybeConsecutiveLists.length > 0) {
            // Join the same-type adjacent lists we found
            $maybeConsecutiveLists.each(function (index, list) {
                var $list = $(list),
                    $listContents = $list.contents(),
                    $prevList = $list.prev();

                $listContents.detach();
                $list.remove();
                $prevList.append($listContents);
            });
        }
    }

    // Remove any now-empty lists
    $parentItem.find('ul:empty,ol:empty').remove();

    // If we eliminated the need for a spacer_li, remove it
    // Comes after empty list removal so that we only remove
    // totally empty spacer li's
    if ($parentItem.is('.spacer_li') && $parentItem.is(':empty')) {
        $parentItem.remove();
    }
};

/**
 * Get the common parent ol/ul for the given li nodes. If the closest parent
 * ol/ul for each cell isn't the same, returns null.
 */
WYMeditor.editor.prototype.getCommonParentList = function (listItems) {
    var firstLi,
        parentList,
        rootList;

    listItems = $(listItems).filter('li');
    if (listItems.length === 0) {
        return null;
    }
    firstLi = listItems[0];
    parentList = $(firstLi).parent('ol,ul');

    if (parentList.length === 0) {
        return null;
    }
    rootList = parentList[0];

    // Ensure that all of the li's have the same parent list
    $(listItems).each(function (index, elmnt) {
        parentList = $(elmnt).parent('ol,ul');
        if (parentList.length === 0 || parentList[0] !== rootList) {
            return null;
        }
    });

    return rootList;
};

/**
    editor._getSelectedListItems
    ============================

    Based on the given selection, determine which li nodes are "selected" from
    the user's standpoint. These are the li nodes that they would expect to be
    affected by an action with the given selection.

    Generally, this means any li which has at least some of its text content
    highlighted will be returned.
*/
WYMeditor.editor.prototype._getSelectedListItems = function (sel) {
    var wym = this,
        i,
        range,
        nodes = [],
        containsNodeTextFilter,
        parentsToAdd;

    // Filter function to remove undesired nodes from what rangy.getNodes()
    // gives
    containsNodeTextFilter = function (testNode) {
        var fullyContainsNodeText;

        // Include any partially-selected textNodes
        if (rangy.dom.isCharacterDataNode(testNode)) {
            return testNode;
        }

        try {
            fullyContainsNodeText = range.containsNodeText(testNode);
        } catch (e) {
            // Rangy throws an exception on an internal
            // intersection call on the last node that's
            // actually in the selection
            return true;
        }

        if (fullyContainsNodeText === true) {
            // If we fully contain any text in this node, it's definitely
            // selected
            return true;
        }
    };

    // Iterate through all of the selection ranges and include any li nodes
    // that are user-selected in each range
    for (i = 0; i < sel.rangeCount; i++) {
        range = sel.getRangeAt(i);
        if (range.collapsed === true) {
            // Collapsed ranges don't return the range they're in as part of
            // getNodes, so let's find the next list item up
            nodes = nodes.concat([wym.findUp(range.startContainer, 'li')]);
        } else {
            // getNodes includes the parent list item whenever we have our
            // selection in a sublist. We need to make a distinction between
            // when the parent list item is actually selected and when it's
            // only sort of selected because we're selecting a sub-item
            // (meaning it's partially selected).
            // In the following case, we don't want `2` as one of our nodes:
            // 1
            // 2
            //   2.1
            //   2|.2
            // 3|
            nodes = nodes.concat(
                range.getNodes(
                    [],
                    containsNodeTextFilter
                )
            );

            // We also need to include the parent li if we selected a non-li, non-list node.
            // eg. if we select text inside an li, the user is actually
            // selecting that entire li
            parentsToAdd = [];
            for (j = 0; j < nodes.length; j++) {
                if (!$(nodes[j]).is('li,ol,ul')) {
                    parentsToAdd.push($(nodes[j]).parent('li').get(0));
                }
            }
            // Add in all of the new parents if they're not already included
            // (no duplicates)
            for (j = 0; j < parentsToAdd.length; j++) {
                if ($.inArray(parentsToAdd[j], nodes) === -1) {
                    nodes.push(parentsToAdd[j]);
                }
            }


        }
    }

    return nodes;
};


/**
    editor.indent
    =============

    Indent the selected list items via the dom.

    Only list items that have a common list will be indented.
 */
WYMeditor.editor.prototype.indent = function () {
    var wym = this._wym,
        sel = rangy.getIframeSelection(this._iframe),
        // Starting selection information for selection restore
        startContainer = sel.getRangeAt(0).startContainer,
        startOffset = sel.getRangeAt(0).startOffset,
        endContainer = sel.getRangeAt(0).endContainer,
        endOffset = sel.getRangeAt(0).endOffset,
        nodes = [],
        range,
        listItems,
        rootList;

    nodes = wym._getSelectedListItems(sel);

    // Just use the li nodes
    listItems = $(nodes).filter('li');
    if (listItems.length === 0) {
        return false;
    }

    // If the selection is across paragraphs and other items at the root level,
    // don't indent
    rootList = wym.getCommonParentList(listItems);
    if (rootList === null) {
        return false;
    }

    for (i = 0; i < listItems.length; i++) {
        wym._indentSingleItem(listItems[i]);
    }

    if (listItems.length === 1) {
        // Put the selection back on the last li element
        range = rangy.createRange(this._doc);
        range.setStart(startContainer, startOffset);
        range.setEnd(endContainer, endOffset);
        range.collapse(false);

        sel.setSingleRange(range);
    }

};

/**
    editor.outdent
    ==============

    Outdent a list item, accounting for firefox bugs to ensure consistent
    behavior and valid HTML.
*/
WYMeditor.editor.prototype.outdent = function () {
    var wym = this._wym,
        sel = rangy.getIframeSelection(this._iframe),
        // Starting selection information for selection restore
        startContainer = sel.getRangeAt(0).startContainer,
        startOffset = sel.getRangeAt(0).startOffset,
        endContainer = sel.getRangeAt(0).endContainer,
        endOffset = sel.getRangeAt(0).endOffset,
        nodes = [],
        range,
        listItems,
        rootList;

    nodes = wym._getSelectedListItems(sel);

    // Just use the li nodes
    listItems = $(nodes).filter('li');
    if (listItems.length === 0) {
        return false;
    }

    // If the selection is across paragraphs and other items at the root level,
    // don't indent
    rootList = wym.getCommonParentList(listItems);
    if (rootList === null) {
        return false;
    }

    for (i = 0; i < listItems.length; i++) {
        wym._outdentSingleItem(listItems[i]);
    }

    if (listItems.length === 1) {
        // Put the selection back on the last li element
        range = rangy.createRange(this._doc);
        range.setStart(startContainer, startOffset);
        range.setEnd(endContainer, endOffset);
        range.collapse(false);

        sel.setSingleRange(range);
    }
};

/**
     editor.insertTable
     ==================

     Insert a table at the current selection with the given number of rows
     and columns and with the given caption and summary text.
*/
WYMeditor.editor.prototype.insertTable = function (rows, columns, caption, summary) {
    if ((rows <= 0) || (columns <= 0)) {
        // We need rows and columns to make a table

        // TODO: It seems to me we should warn the user when zero columns and/or
        // rows were entered.
        return;
    }

    var table = this._doc.createElement(WYMeditor.TABLE),
        newRow = null,
        newCol = null,
        newCaption,

        x,
        y,

        container;

    // Create the table caption
    newCaption = table.createCaption();
    newCaption.innerHTML = caption;

    // Create the rows and cells
    for (x = 0; x < rows; x += 1) {
        newRow = table.insertRow(x);
        for (y = 0; y < columns; y += 1) {
            newRow.insertCell(y);
        }
    }

    if (summary !== "") {
        // Only need to set the summary if we actually have a summary
        jQuery(table).attr('summary', summary);
    }

    // Find the currently-selected container
    container = jQuery(
        this.findUp(this.container(), WYMeditor.MAIN_CONTAINERS)
    ).get(0);

    if (!container || !container.parentNode) {
        // No valid selected container. Put the table at the end.
        jQuery(this._doc.body).append(table);
    } else {
        // Append the table after the currently-selected container
        jQuery(container).after(table);
    }

    // Handle any browser-specific cleanup
    this.afterInsertTable(table);
    this.fixBodyHtml();

    return table;
};

/**
    editor.afterInsertTable
    =======================

    Handle cleanup/normalization after inserting a table. Different browsers
    need slightly different tweaks.
*/
WYMeditor.editor.prototype.afterInsertTable = function (table) {};

WYMeditor.editor.prototype.configureEditorUsingRawCss = function () {
    var CssParser = new WYMeditor.WymCssParser();
    if (this._options.stylesheet) {
        CssParser.parse(
            jQuery.ajax({
                url: this._options.stylesheet,
                async: false
            }).responseText
        );
    } else {
        CssParser.parse(this._options.styles, false);
    }

    if (this._options.classesItems.length === 0) {
        this._options.classesItems = CssParser.css_settings.classesItems;
    }
    if (this._options.editorStyles.length === 0) {
        this._options.editorStyles = CssParser.css_settings.editorStyles;
    }
    if (this._options.dialogStyles.length === 0) {
        this._options.dialogStyles = CssParser.css_settings.dialogStyles;
    }
};

WYMeditor.editor.prototype.listen = function () {
    var wym = this;

    // Don't use jQuery.find() on the iframe body
    // because of MSIE + jQuery + expando issue (#JQ1143)

    jQuery(this._doc.body).bind("mousedown", function (e) {
        wym.mousedown(e);
    });
};

WYMeditor.editor.prototype.mousedown = function (evt) {
    // Store the selected image if we clicked an <img> tag
    this._selected_image = null;
    if (evt.target.tagName.toLowerCase() === WYMeditor.IMG) {
        this._selected_image = evt.target;
    }
};

/**
    WYMeditor.loadCss
    =================

    Load a stylesheet in the document.

    href - The CSS path.
*/
WYMeditor.loadCss = function (href) {
    var link = document.createElement('link'),
        head;
    link.rel = 'stylesheet';
    link.href = href;

    head = jQuery('head').get(0);
    head.appendChild(link);
};

/**
    WYMeditor.editor.loadSkin
    =========================

    Load the skin CSS and initialization script (if needed).
*/
WYMeditor.editor.prototype.loadSkin = function () {
    // Does the user want to automatically load the CSS (default: yes)?
    // We also test if it hasn't been already loaded by another instance
    // see below for a better (second) test
    if (this._options.loadSkin && !WYMeditor.SKINS[this._options.skin]) {
        // Check if it hasn't been already loaded so we don't load it more
        // than once (we check the existing <link> elements)
        var found = false,
            rExp = new RegExp(this._options.skin +
                '\/' + WYMeditor.SKINS_DEFAULT_CSS + '$');

        jQuery('link').each(function () {
            if (this.href.match(rExp)) {
                found = true;
            }
        });

        // Load it, using the skin path
        if (!found) {
            WYMeditor.loadCss(
                this._options.skinPath + WYMeditor.SKINS_DEFAULT_CSS
            );
        }
    }

    // Put the classname (ex. wym_skin_default) on wym_box
    jQuery(this._box).addClass("wym_skin_" + this._options.skin);

    // Does the user want to use some JS to initialize the skin (default: yes)?
    // Also check if it hasn't already been loaded by another instance
    if (this._options.initSkin && !WYMeditor.SKINS[this._options.skin]) {
        eval(jQuery.ajax({url: this._options.skinPath +
            WYMeditor.SKINS_DEFAULT_JS, async: false}).responseText);
    }

    // Init the skin, if needed
    if (WYMeditor.SKINS[this._options.skin] && WYMeditor.SKINS[this._options.skin].init) {
        WYMeditor.SKINS[this._options.skin].init(this);
    }
};
/*jslint evil: true */
/*
 * WYMeditor : what you see is What You Mean web-based editor
 * Copyright (c) 2005 - 2009 Jean-Francois Hovinne, http://www.wymeditor.org/
 * Dual licensed under the MIT (MIT-license.txt)
 * and GPL (GPL-license.txt) licenses.
 *
 * For further information visit:
 *        http://www.wymeditor.org/
 *
 * File Name:
 *        jquery.wymeditor.explorer.js
 *        MSIE specific class and functions.
 *        See the documentation for more info.
 *
 * File Authors:
 *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
 *        Bermi Ferrer (wymeditor a-t bermi dotorg)
 *        Frédéric Palluel-Lafleur (fpalluel a-t gmail dotcom)
 *        Jonatan Lundin (jonatan.lundin a-t gmail dotcom)
 */

WYMeditor.WymClassExplorer = function (wym) {
    this._wym = wym;
    this._class = "className";
};

WYMeditor.WymClassExplorer.PLACEHOLDER_NODE = '<br>';

WYMeditor.WymClassExplorer.prototype.initIframe = function (iframe) {
    //This function is executed twice, though it is called once!
    //But MSIE needs that, otherwise designMode won't work.
    //Weird.
    this._iframe = iframe;
    this._doc = iframe.contentWindow.document;

    //add css rules from options
    var styles = this._doc.styleSheets[0];
    var aCss = eval(this._options.editorStyles);

    this.addCssRules(this._doc, aCss);

    this._doc.title = this._wym._index;

    //set the text direction
    jQuery('html', this._doc).attr('dir', this._options.direction);

    //init html value
    jQuery(this._doc.body).html(this._wym._html);

    //handle events
    var wym = this;

    this._doc.body.onfocus = function () {
        wym._doc.designMode = "on";
        wym._doc = iframe.contentWindow.document;
    };
    this._doc.onbeforedeactivate = function () {
        wym.saveCaret();
    };
    $(this._doc).bind('keyup', wym.keyup);
    // Workaround for an ie8 => ie7 compatibility mode bug triggered
    // intermittently by certain combinations of CSS on the iframe
    var ieVersion = parseInt($.browser.version, 10);
    if (ieVersion >= 8 && ieVersion < 9) {
        $(this._doc).bind('keydown', function () {
            wym.fixBluescreenOfDeath();
        });
    }
    this._doc.onkeyup = function () {
        wym.saveCaret();
    };
    this._doc.onclick = function () {
        wym.saveCaret();
    };

    this._doc.body.onbeforepaste = function () {
        wym._iframe.contentWindow.event.returnValue = false;
    };

    this._doc.body.onpaste = function () {
        wym._iframe.contentWindow.event.returnValue = false;
        wym.paste(window.clipboardData.getData("Text"));
    };

    //callback can't be executed twice, so we check
    if (this._initialized) {

        //pre-bind functions
        if (jQuery.isFunction(this._options.preBind)) {
            this._options.preBind(this);
        }


        //bind external events
        this._wym.bindEvents();

        //post-init functions
        if (jQuery.isFunction(this._options.postInit)) {
            this._options.postInit(this);
        }

        //add event listeners to doc elements, e.g. images
        this.listen();
    }

    this._initialized = true;

    //init designMode
    this._doc.designMode = "on";
    try {
        // (bermi's note) noticed when running unit tests on IE6
        // Is this really needed, it trigger an unexisting property on IE6
        this._doc = iframe.contentWindow.document;
    } catch (e) {}
};

(function (editorLoadSkin) {
    WYMeditor.WymClassExplorer.prototype.loadSkin = function () {
        // Mark container items as unselectable (#203)
        // Fix for issue explained:
        // http://stackoverflow.com/questions/1470932/ie8-iframe-designmode-loses-selection
        jQuery(this._box).find(this._options.containerSelector).attr('unselectable', 'on');

        editorLoadSkin.call(this);
    };
}(WYMeditor.editor.prototype.loadSkin));

/**
    fixBluescreenOfDeath
    ====================

    In ie8 when using ie7 compatibility mode, certain combinations of CSS on
    the iframe will trigger a bug that causes the rendering engine to give all
    block-level editable elements a negative left position that puts them off of
    the screen. This results in the editor looking blank (just the blue background)
    and requires the user to move the mouse or manipulate the DOM to force a
    re-render, which fixes the problem.

    This workaround detects the negative position and then manipulates the DOM
    to cause a re-render, which puts the elements back in position.

    A real fix would be greatly appreciated.
*/
WYMeditor.WymClassExplorer.prototype.fixBluescreenOfDeath = function () {
    var position = $(this._doc).find('p').eq(0).position();
    if (position !== null && typeof position !== 'undefined' && position.left < 0) {
        $(this._box).append('<br id="wym-bluescreen-bug-fix" />');
        $(this._box).find('#wym-bluescreen-bug-fix').remove();
    }
};


WYMeditor.WymClassExplorer.prototype._exec = function (cmd, param) {
    if (param) {
        this._doc.execCommand(cmd, false, param);
    } else {
        this._doc.execCommand(cmd);
    }
};

WYMeditor.WymClassExplorer.prototype.selected = function () {
    var caretPos = this._iframe.contentWindow.document.caretPos;
    if (caretPos) {
        if (caretPos.parentElement) {
            return caretPos.parentElement();
        }
    }
};

WYMeditor.WymClassExplorer.prototype.saveCaret = function () {
    this._doc.caretPos = this._doc.selection.createRange();
};

WYMeditor.WymClassExplorer.prototype.addCssRule = function (styles, oCss) {
    // IE doesn't handle combined selectors (#196)
    var selectors = oCss.name.split(','),
        i;
    for (i = 0; i < selectors.length; i++) {
        styles.addRule(selectors[i], oCss.css);
    }
};

WYMeditor.WymClassExplorer.prototype.insert = function (html) {

    // Get the current selection
    var range = this._doc.selection.createRange();

    // Check if the current selection is inside the editor
    if (jQuery(range.parentElement()).parents().is(this._options.iframeBodySelector)) {
        try {
            // Overwrite selection with provided html
            range.pasteHTML(html);
        } catch (e) {}
    } else {
        // Fall back to the internal paste function if there's no selection
        this.paste(html);
    }
};

WYMeditor.WymClassExplorer.prototype.wrap = function (left, right) {
    // Get the current selection
    var range = this._doc.selection.createRange();

    // Check if the current selection is inside the editor
    if (jQuery(range.parentElement()).parents().is(this._options.iframeBodySelector)) {
        try {
            // Overwrite selection with provided html
            range.pasteHTML(left + range.text + right);
        } catch (e) {}
    }
};

WYMeditor.WymClassExplorer.prototype.unwrap = function () {
    // Get the current selection
    var range = this._doc.selection.createRange();

    // Check if the current selection is inside the editor
    if (jQuery(range.parentElement()).parents().is(this._options.iframeBodySelector)) {
        try {
            // Unwrap selection
            var text = range.text;
            this._exec('Cut');
            range.pasteHTML(text);
        } catch (e) {}
    }
};

WYMeditor.WymClassExplorer.prototype.keyup = function (evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title];

    this._selected_image = null;

    var container = null;

    if (evt.keyCode !== WYMeditor.KEY.BACKSPACE &&
            evt.keyCode !== WYMeditor.KEY.CTRL &&
            evt.keyCode !== WYMeditor.KEY.DELETE &&
            evt.keyCode !== WYMeditor.KEY.COMMAND &&
            evt.keyCode !== WYMeditor.KEY.UP &&
            evt.keyCode !== WYMeditor.KEY.DOWN &&
            evt.keyCode !== WYMeditor.KEY.ENTER &&
            !evt.metaKey &&
            !evt.ctrlKey) { // Not BACKSPACE, DELETE, CTRL, or COMMAND key

        container = wym.selected();
        var name = '';
        if (container !== null) {
            name = container.tagName.toLowerCase();
        }

        // Fix forbidden main containers
        if (name === "strong" ||
                name === "b" ||
                name === "em" ||
                name === "i" ||
                name === "sub" ||
                name === "sup" ||
                name === "a") {

            name = container.parentNode.tagName.toLowerCase();
        }

        if (name === WYMeditor.BODY) {
            // Replace text nodes with <p> tags
            wym._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
            wym.fixBodyHtml();
        }
    }

    // If we potentially created a new block level element or moved to a new one
    // then we should ensure that they're in the proper format
    if (evt.keyCode === WYMeditor.KEY.UP ||
            evt.keyCode === WYMeditor.KEY.DOWN ||
            evt.keyCode === WYMeditor.KEY.BACKSPACE ||
            evt.keyCode === WYMeditor.KEY.ENTER) {

        wym.fixBodyHtml();
    }
};

WYMeditor.WymClassExplorer.prototype.setFocusToNode = function (node, toStart) {
    var range = this._doc.selection.createRange();
    toStart = toStart ? true : false;

    range.moveToElementText(node);
    range.collapse(toStart);
    range.select();
    node.focus();
};

/* @name spaceBlockingElements
 * @description Insert <br> elements between adjacent blocking elements and
 * p elements, between block elements or blocking elements and after blocking
 * elements.
 */
WYMeditor.WymClassExplorer.prototype.spaceBlockingElements = function () {
    var blockingSelector = WYMeditor.BLOCKING_ELEMENTS.join(', ');

    var $body = $(this._doc).find('body.wym_iframe');
    var children = $body.children();
    var placeholderNode = WYMeditor.WymClassExplorer.PLACEHOLDER_NODE;

    // Make sure we have the appropriate placeholder nodes
    if (children.length > 0) {
        var $firstChild = $(children[0]);
        var $lastChild = $(children[children.length - 1]);

        // Ensure begining placeholder
        if ($firstChild.is(blockingSelector)) {
            $firstChild.before(placeholderNode);
        }
        if ($.browser.version >= "7.0" && $lastChild.is(blockingSelector)) {
            $lastChild.after(placeholderNode);
        }
    }

    var blockSepSelector = this._getBlockSepSelector();

    // Put placeholder nodes between consecutive blocking elements and between
    // blocking elements and normal block-level elements
    $body.find(blockSepSelector).before(placeholderNode);
};

/*jslint evil: true */
/*
 * WYMeditor : what you see is What You Mean web-based editor
 * Copyright (c) 2005 - 2009 Jean-Francois Hovinne, http://www.wymeditor.org/
 * Dual licensed under the MIT (MIT-license.txt)
 * and GPL (GPL-license.txt) licenses.
 *
 * For further information visit:
 *        http://www.wymeditor.org/
 *
 * File Name:
 *        jquery.wymeditor.mozilla.js
 *        Gecko specific class and functions.
 *        See the documentation for more info.
 *
 * File Authors:
 *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
 *        Volker Mische (vmx a-t gmx dotde)
 *        Bermi Ferrer (wymeditor a-t bermi dotorg)
 *        Frédéric Palluel-Lafleur (fpalluel a-t gmail dotcom)
 *        Jonatan Lundin (jonatan.lundin a-t gmail dotcom)
 */

WYMeditor.WymClassMozilla = function (wym) {
    this._wym = wym;
    this._class = "class";
};

// Placeholder cell to allow content in TD cells for FF 3.5+
WYMeditor.WymClassMozilla.CELL_PLACEHOLDER = '<br _moz_dirty="">';

// Firefox 3.5 and 3.6 require the CELL_PLACEHOLDER and 4.0 doesn't
WYMeditor.WymClassMozilla.NEEDS_CELL_FIX = $.browser.version >= '1.9.1' &&
    $.browser.version < '2.0';

WYMeditor.WymClassMozilla.prototype.initIframe = function (iframe) {
    var wym = this,
        styles,
        aCss;

    this._iframe = iframe;
    this._doc = iframe.contentDocument;

    //add css rules from options
    styles = this._doc.styleSheets[0];

    aCss = eval(this._options.editorStyles);

    this.addCssRules(this._doc, aCss);

    this._doc.title = this._wym._index;

    //set the text direction
    jQuery('html', this._doc).attr('dir', this._options.direction);

    //init html value
    this.html(this._wym._html);

    //init designMode
    this.enableDesignMode();

    //pre-bind functions
    if (jQuery.isFunction(this._options.preBind)) {
        this._options.preBind(this);
    }

    //bind external events
    this._wym.bindEvents();

    //bind editor keydown events
    jQuery(this._doc).bind("keydown", this.keydown);

    //bind editor keyup events
    jQuery(this._doc).bind("keyup", this.keyup);

    //bind editor click events
    jQuery(this._doc).bind("click", this.click);

    //bind editor focus events (used to reset designmode - Gecko bug)
    jQuery(this._doc).bind("focus", function () {
        // Fix scope
        wym.enableDesignMode.call(wym);
    });

    //post-init functions
    if (jQuery.isFunction(this._options.postInit)) {
        this._options.postInit(this);
    }

    //add event listeners to doc elements, e.g. images
    this.listen();
};

/* @name html
 * @description Get/Set the html value
 */
WYMeditor.WymClassMozilla.prototype.html = function (html) {
    if (typeof html === 'string') {
        //disable designMode
        try {
            this._doc.designMode = "off";
        } catch (e) {
            //do nothing
        }

        //replace em by i and strong by bold
        //(designMode issue)
        html = html.replace(/<em(\b[^>]*)>/gi, "<i$1>");
        html = html.replace(/<\/em>/gi, "</i>");
        html = html.replace(/<strong(\b[^>]*)>/gi, "<b$1>");
        html = html.replace(/<\/strong>/gi, "</b>");

        //update the html body
        jQuery(this._doc.body).html(html);
        this._wym.fixBodyHtml();

        //re-init designMode
        this.enableDesignMode();
    } else {
        return jQuery(this._doc.body).html();
    }
    return false;
};

WYMeditor.WymClassMozilla.prototype._exec = function (cmd, param) {
    if (!this.selected()) {
        return false;
    }

    if (param) {
        this._doc.execCommand(cmd, '', param);
    } else {
        this._doc.execCommand(cmd, '', null);
    }

    //set to P if parent = BODY
    var container = this.selected();
    if (container.tagName.toLowerCase() === WYMeditor.BODY) {
        this._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
    }

    return true;
};

WYMeditor.WymClassMozilla.prototype.addCssRule = function (styles, oCss) {

    styles.insertRule(oCss.name + " {" + oCss.css + "}",
        styles.cssRules.length);
};

//keydown handler, mainly used for keyboard shortcuts
WYMeditor.WymClassMozilla.prototype.keydown = function (evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title];

    if (evt.ctrlKey) {
        if (evt.keyCode === 66) {
            //CTRL+b => STRONG
            wym._exec(WYMeditor.BOLD);
            return false;
        }
        if (evt.keyCode === 73) {
            //CTRL+i => EMPHASIS
            wym._exec(WYMeditor.ITALIC);
            return false;
        }
    }

    return true;
};

// Keyup handler, mainly used for cleanups
WYMeditor.WymClassMozilla.prototype.keyup = function (evt) {
    // 'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title],
        container,
        name;

    wym._selected_image = null;
    container = null;

    if (evt.keyCode !== WYMeditor.KEY.BACKSPACE &&
            evt.keyCode !== WYMeditor.KEY.CTRL &&
            evt.keyCode !== WYMeditor.KEY.DELETE &&
            evt.keyCode !== WYMeditor.KEY.COMMAND &&
            evt.keyCode !== WYMeditor.KEY.UP &&
            evt.keyCode !== WYMeditor.KEY.DOWN &&
            evt.keyCode !== WYMeditor.KEY.LEFT &&
            evt.keyCode !== WYMeditor.KEY.RIGHT &&
            evt.keyCode !== WYMeditor.KEY.ENTER &&
            !evt.metaKey &&
            !evt.ctrlKey) { // Not BACKSPACE, DELETE, CTRL, or COMMAND key

        container = wym.selected();
        name = container.tagName.toLowerCase();

        //fix forbidden main containers
        if (name === "strong" ||
                name === "b" ||
                name === "em" ||
                name === "i" ||
                name === "sub" ||
                name === "sup" ||
                name === "a") {

            name = container.parentNode.tagName.toLowerCase();
        }

        if (name === WYMeditor.BODY) {
            // Replace text nodes with <p> tags
            wym._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
            wym.fixBodyHtml();
        }
    }

    // If we potentially created a new block level element or moved to a new one
    // then we should ensure that they're in the proper format
    if (evt.keyCode === WYMeditor.KEY.UP ||
            evt.keyCode === WYMeditor.KEY.DOWN ||
            evt.keyCode === WYMeditor.KEY.LEFT ||
            evt.keyCode === WYMeditor.KEY.RIGHT ||
            evt.keyCode === WYMeditor.KEY.BACKSPACE ||
            evt.keyCode === WYMeditor.KEY.ENTER) {
        wym.fixBodyHtml();
    }
};

WYMeditor.WymClassMozilla.prototype.click = function (evt) {
    var wym = WYMeditor.INSTANCES[this.title],
        container = wym.selected(),
        sel;

    if (WYMeditor.WymClassMozilla.NEEDS_CELL_FIX === true) {
        if (container && container.tagName.toLowerCase() === WYMeditor.TR) {
            // Starting with FF 3.6, inserted tables need some content in their
            // cells before they're editable
            jQuery(WYMeditor.TD, wym._doc.body).
                append(WYMeditor.WymClassMozilla.CELL_PLACEHOLDER);

            // The user is still going to need to move out of and then back in
            // to this cell if the table was inserted via an inner_html call
            // (like via the manual HTML editor).
            // TODO: Use rangy or some other selection library to consistently
            // put the users selection out of and then back in this cell
            // so that it appears to be instantly editable
            // Once accomplished, can remove the afterInsertTable handling
        }
    }

    if (container && container.tagName.toLowerCase() === WYMeditor.BODY) {
        // A click in the body means there is no content at all, so we
        // should automatically create a starter paragraph
        sel = wym._iframe.contentWindow.getSelection();
        if (sel.isCollapsed === true) {
            // If the selection isn't collapsed, we might have a selection that
            // drags over the body, but we shouldn't turn everything in to a
            // paragraph tag. Otherwise, double-clicking in the space to the
            // right of an h2 tag would turn it in to a paragraph
            wym._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
        }
    }
};

WYMeditor.WymClassMozilla.prototype.enableDesignMode = function () {
    if (this._doc.designMode === "off") {
        try {
            this._doc.designMode = "on";
            this._doc.execCommand("styleWithCSS", '', false);
            this._doc.execCommand("enableObjectResizing", false, true);
        } catch (e) {}
    }
};

WYMeditor.WymClassMozilla.prototype.openBlockTag = function (tag, attributes) {
    attributes = this.validator.getValidTagAttributes(tag, attributes);

    // Handle Mozilla styled spans
    if (tag === 'span' && attributes.style) {
        var new_tag = this.getTagForStyle(attributes.style);
        if (new_tag) {
            tag = new_tag;
            this._tag_stack.pop();
            this._tag_stack.push(tag);
            attributes.style = '';
        }
    }

    this.output += this.helper.tag(tag, attributes, true);
};

WYMeditor.WymClassMozilla.prototype.getTagForStyle = function (style) {
    if (/bold/.test(style)) {
        return 'strong';
    } else if (/italic/.test(style)) {
        return 'em';
    } else if (/sub/.test(style)) {
        return 'sub';
    } else if (/super/.test(style)) {
        return 'sup';
    }

    return false;
};

/*
 * Fix new cell contents and ability to insert content at the front and end of
 * the contents.
 */
WYMeditor.WymClassMozilla.prototype.afterInsertTable = function (table) {
    if (WYMeditor.WymClassMozilla.NEEDS_CELL_FIX === true) {
        // In certain FF versions, inserted tables need some content in their
        // cells before they're editable, otherwise the user has to move focus
        // in and then out of a cell first, even with our click() hack
        $(table).find('td').each(function (index, element) {
            $(element).append(WYMeditor.WymClassMozilla.CELL_PLACEHOLDER);
        });
    }
};
/*jslint evil: true */
/*
 * WYMeditor : what you see is What You Mean web-based editor
 * Copyright (c) 2005 - 2009 Jean-Francois Hovinne, http://www.wymeditor.org/
 * Dual licensed under the MIT (MIT-license.txt)
 * and GPL (GPL-license.txt) licenses.
 *
 * For further information visit:
 *        http://www.wymeditor.org/
 *
 * File Name:
 *        jquery.wymeditor.opera.js
 *        Opera specific class and functions.
 *        See the documentation for more info.
 *
 * File Authors:
 *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
 */

WYMeditor.WymClassOpera = function(wym) {
    this._wym = wym;
    this._class = "class";
};

WYMeditor.WymClassOpera.prototype.initIframe = function(iframe) {
    this._iframe = iframe;
    this._doc = iframe.contentWindow.document;

    //add css rules from options
    var styles = this._doc.styleSheets[0];
    var aCss = eval(this._options.editorStyles);

    this.addCssRules(this._doc, aCss);

    this._doc.title = this._wym._index;

    //set the text direction
    jQuery('html', this._doc).attr('dir', this._options.direction);

    //init designMode
    this._doc.designMode = "on";

    //init html value
    this.html(this._wym._html);

    //pre-bind functions
    if (jQuery.isFunction(this._options.preBind)) {
        this._options.preBind(this);
    }

    //bind external events
    this._wym.bindEvents();

    //bind editor keydown events
    jQuery(this._doc).bind("keydown", this.keydown);

    //bind editor events
    jQuery(this._doc).bind("keyup", this.keyup);

    //post-init functions
    if (jQuery.isFunction(this._options.postInit)) {
        this._options.postInit(this);
    }

    //add event listeners to doc elements, e.g. images
    this.listen();
};

WYMeditor.WymClassOpera.prototype._exec = function(cmd, param) {
    if (param) {
        this._doc.execCommand(cmd, false, param);
    }
    else {
        this._doc.execCommand(cmd);
    }
};

WYMeditor.WymClassOpera.prototype.selected = function() {
    var sel = this._iframe.contentWindow.getSelection();
    var node = sel.focusNode;
    if (node) {
        if (node.nodeName == "#text") {
            return node.parentNode;
        } else {
            return node;
        }
    } else {
        return null;
    }
};

WYMeditor.WymClassOpera.prototype.addCssRule = function(styles, oCss) {
    styles.insertRule(
            oCss.name + " {" + oCss.css + "}", styles.cssRules.length);
};

WYMeditor.WymClassOpera.prototype.keydown = function(evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title];
    var sel = wym._iframe.contentWindow.getSelection();
    startNode = sel.getRangeAt(0).startContainer;

    //Get a P instead of no container
    if (!jQuery(startNode).parentsOrSelf(WYMeditor.MAIN_CONTAINERS.join(","))[0] &&
            !jQuery(startNode).parentsOrSelf('li') &&
            evt.keyCode != WYMeditor.KEY.ENTER &&
            evt.keyCode != WYMeditor.KEY.LEFT &&
            evt.keyCode != WYMeditor.KEY.UP &&
            evt.keyCode != WYMeditor.KEY.RIGHT &&
            evt.keyCode != WYMeditor.KEY.DOWN &&
            evt.keyCode != WYMeditor.KEY.BACKSPACE &&
            evt.keyCode != WYMeditor.KEY.DELETE) {

        wym._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
    }
};

WYMeditor.WymClassOpera.prototype.keyup = function(evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title];
    wym._selected_image = null;
};
/*jslint evil: true */
/*
 * WYMeditor : what you see is What You Mean web-based editor
 * Copyright (c) 2005 - 2009 Jean-Francois Hovinne, http://www.wymeditor.org/
 * Dual licensed under the MIT (MIT-license.txt)
 * and GPL (GPL-license.txt) licenses.
 *
 * For further information visit:
 *        http://www.wymeditor.org/
 *
 * File Name:
 *        jquery.wymeditor.safari.js
 *        Safari specific class and functions.
 *        See the documentation for more info.
 *
 * File Authors:
 *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
 *        Scott Lewis (lewiscot a-t gmail dotcom)
 */

WYMeditor.WymClassSafari = function (wym) {
    this._wym = wym;
    this._class = "class";
};

WYMeditor.WymClassSafari.prototype.initIframe = function (iframe) {
    var wym = this,
        styles,
        aCss;

    this._iframe = iframe;
    this._doc = iframe.contentDocument;

    //add css rules from options
    styles = this._doc.styleSheets[0];
    aCss = eval(this._options.editorStyles);

    this.addCssRules(this._doc, aCss);

    this._doc.title = this._wym._index;

    //set the text direction
    jQuery('html', this._doc).attr('dir', this._options.direction);

    //init designMode
    this._doc.designMode = "on";

    //init html value
    this.html(this._wym._html);

    //pre-bind functions
    if (jQuery.isFunction(this._options.preBind)) {
        this._options.preBind(this);
    }

    //bind external events
    this._wym.bindEvents();

    //bind editor keydown events
    jQuery(this._doc).bind("keydown", this.keydown);

    //bind editor keyup events
    jQuery(this._doc).bind("keyup", this.keyup);

    //post-init functions
    if (jQuery.isFunction(this._options.postInit)) {
        this._options.postInit(this);
    }

    //add event listeners to doc elements, e.g. images
    this.listen();
};

WYMeditor.WymClassSafari.prototype._exec = function (cmd, param) {
    if (!this.selected()) {
        return false;
    }

    var focusNode = this.selected(),
        container;

    switch (cmd) {
    case WYMeditor.INSERT_ORDEREDLIST:
    case WYMeditor.INSERT_UNORDEREDLIST:

        this._doc.execCommand(cmd, '', null);

        //Safari creates lists in e.g. paragraphs.
        //Find the container, and remove it.
        container = this.findUp(focusNode, WYMeditor.MAIN_CONTAINERS);
        if (container) {
            jQuery(container).replaceWith(jQuery(container).html());
        }

        break;
    default:
        if (param) {
            this._doc.execCommand(cmd, '', param);
        } else {
            this._doc.execCommand(cmd, '', null);
        }

        break;
    }

    //set to P if parent = BODY
    container = this.selected();
    if (container && container.tagName.toLowerCase() === WYMeditor.BODY) {
        this._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
    }

    return true;
};

WYMeditor.WymClassSafari.prototype.addCssRule = function (styles, oCss) {
    styles.insertRule(oCss.name + " {" + oCss.css + "}",
        styles.cssRules.length);
};


//keydown handler, mainly used for keyboard shortcuts
WYMeditor.WymClassSafari.prototype.keydown = function (e) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title];

    if (e.ctrlKey) {
        if (e.keyCode === WYMeditor.KEY.B) {
            //CTRL+b => STRONG
            wym._exec(WYMeditor.BOLD);
            e.preventDefault();
        }
        if (e.keyCode === WYMeditor.KEY.I) {
            //CTRL+i => EMPHASIS
            wym._exec(WYMeditor.ITALIC);
            e.preventDefault();
        }
    } else if (e.shiftKey && e.keyCode === WYMeditor.KEY.ENTER) {
        // Safari 4 and earlier would show a proper linebreak in the editor and
        // then strip it upon save with the default action in the case of inserting
        // a new line after bold text
        wym._exec('InsertLineBreak');
        e.preventDefault();
    }
};

// Keyup handler, mainly used for cleanups
WYMeditor.WymClassSafari.prototype.keyup = function (evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title],
        container,
        name;

    wym._selected_image = null;

    // Fix to allow shift + return to insert a line break in older safari
    if ($.browser.version < 534.1) {
        // Not needed in AT MAX chrome 6.0. Probably safe earlier
        if (evt.keyCode === WYMeditor.KEY.ENTER && evt.shiftKey) {
            wym._exec('InsertLineBreak');
        }
    }

    if (evt.keyCode !== WYMeditor.KEY.BACKSPACE &&
            evt.keyCode !== WYMeditor.KEY.CTRL &&
            evt.keyCode !== WYMeditor.KEY.DELETE &&
            evt.keyCode !== WYMeditor.KEY.COMMAND &&
            evt.keyCode !== WYMeditor.KEY.UP &&
            evt.keyCode !== WYMeditor.KEY.DOWN &&
            evt.keyCode !== WYMeditor.KEY.LEFT &&
            evt.keyCode !== WYMeditor.KEY.RIGHT &&
            evt.keyCode !== WYMeditor.KEY.ENTER &&
            !evt.metaKey &&
            !evt.ctrlKey) {// Not BACKSPACE, DELETE, CTRL, or COMMAND key

        container = wym.selected();
        name = container.tagName.toLowerCase();

        // Fix forbidden main containers
        if (name === "strong" ||
                name === "b" ||
                name === "em" ||
                name === "i" ||
                name === "sub" ||
                name === "sup" ||
                name === "a" ||
                name === "span") {
            // Webkit tries to use spans as a main container

            name = container.parentNode.tagName.toLowerCase();
        }

        if (name === WYMeditor.BODY || name === WYMeditor.DIV) {
            // Replace text nodes with <p> tags
            wym._exec(WYMeditor.FORMAT_BLOCK, WYMeditor.P);
            wym.fixBodyHtml();
        }
    }

    // If we potentially created a new block level element or moved to a new one
    // then we should ensure that they're in the proper format
    if (evt.keyCode === WYMeditor.KEY.UP ||
            evt.keyCode === WYMeditor.KEY.DOWN ||
            evt.keyCode === WYMeditor.KEY.LEFT ||
            evt.keyCode === WYMeditor.KEY.RIGHT ||
            evt.keyCode === WYMeditor.KEY.BACKSPACE ||
            evt.keyCode === WYMeditor.KEY.ENTER) {
        wym.fixBodyHtml();
    }
};

WYMeditor.WymClassSafari.prototype.openBlockTag = function (tag, attributes) {
    var new_tag;

    attributes = this.validator.getValidTagAttributes(tag, attributes);

    // Handle Safari styled spans
    if (tag === 'span' && attributes.style) {
        new_tag = this.getTagForStyle(attributes.style);
        if (new_tag) {
            tag = new_tag;
            this._tag_stack.pop();
            this._tag_stack.push(tag);
            attributes.style = '';

            // Should fix #125 - also removed the xhtml() override
            if (typeof attributes['class'] === 'string') {
                attributes['class'] = attributes['class'].replace(
                    /apple-style-span/gi,
                    ''
                );
            }
        }
    }

    this.output += this.helper.tag(tag, attributes, true);
};

WYMeditor.WymClassSafari.prototype.getTagForStyle = function (style) {
    if (/bold/.test(style)) {
        return 'strong';
    } else if (/italic/.test(style)) {
        return 'em';
    } else if (/sub/.test(style)) {
        return 'sub';
    } else if (/super/.test(style)) {
        return 'sup';
    }

    return false;
};
/********** XHTML LEXER/PARSER **********/

/*
* @name xml
* @description Use these methods to generate XML and XHTML compliant tags and
* escape tag attributes correctly
* @author Bermi Ferrer - http://bermi.org
* @author David Heinemeier Hansson http://loudthinking.com
*/
WYMeditor.XmlHelper = function()
{
    this._entitiesDiv = document.createElement('div');
    return this;
};


/*
* @name tag
* @description
* Returns an empty HTML tag of type *name* which by default is XHTML
* compliant. Setting *open* to true will create an open tag compatible
* with HTML 4.0 and below. Add HTML attributes by passing an attributes
* array to *options*. For attributes with no value like (disabled and
* readonly), give it a value of true in the *options* array.
*
* Examples:
*
*   this.tag('br')
*    # => <br />
*   this.tag ('br', false, true)
*    # => <br>
*   this.tag ('input', jQuery({type:'text',disabled:true }) )
*    # => <input type="text" disabled="disabled" />
*/
WYMeditor.XmlHelper.prototype.tag = function(name, options, open)
{
    options = options || false;
    open = open || false;
    return '<'+name+(options ? this.tagOptions(options) : '')+(open ? '>' : ' />');
};

/*
* @name contentTag
* @description
* Returns a XML block tag of type *name* surrounding the *content*. Add
* XML attributes by passing an attributes array to *options*. For attributes
* with no value like (disabled and readonly), give it a value of true in
* the *options* array. You can use symbols or strings for the attribute names.
*
*   this.contentTag ('p', 'Hello world!' )
*    # => <p>Hello world!</p>
*   this.contentTag('div', this.contentTag('p', "Hello world!"), jQuery({class : "strong"}))
*    # => <div class="strong"><p>Hello world!</p></div>
*   this.contentTag("select", options, jQuery({multiple : true}))
*    # => <select multiple="multiple">...options...</select>
*/
WYMeditor.XmlHelper.prototype.contentTag = function(name, content, options)
{
    options = options || false;
    return '<'+name+(options ? this.tagOptions(options) : '')+'>'+content+'</'+name+'>';
};

/*
* @name cdataSection
* @description
* Returns a CDATA section for the given +content+.  CDATA sections
* are used to escape blocks of text containing characters which would
* otherwise be recognized as markup. CDATA sections begin with the string
* <tt>&lt;![CDATA[</tt> and } with (and may not contain) the string
* <tt>]]></tt>.
*/
WYMeditor.XmlHelper.prototype.cdataSection = function(content)
{
    return '<![CDATA['+content+']]>';
};


/*
* @name escapeOnce
* @description
* Returns the escaped +xml+ without affecting existing escaped entities.
*
*  this.escapeOnce( "1 > 2 &amp; 3")
*    # => "1 &gt; 2 &amp; 3"
*/
WYMeditor.XmlHelper.prototype.escapeOnce = function(xml)
{
    return this._fixDoubleEscape(this.escapeEntities(xml));
};

/*
* @name _fixDoubleEscape
* @description
* Fix double-escaped entities, such as &amp;amp;, &amp;#123;, etc.
*/
WYMeditor.XmlHelper.prototype._fixDoubleEscape = function(escaped)
{
    return escaped.replace(/&amp;([a-z]+|(#\d+));/ig, "&$1;");
};

/*
* @name tagOptions
* @description
* Takes an array like the one generated by Tag.parseAttributes
*  [["src", "http://www.editam.com/?a=b&c=d&amp;f=g"], ["title", "Editam, <Simplified> CMS"]]
* or an object like {src:"http://www.editam.com/?a=b&c=d&amp;f=g", title:"Editam, <Simplified> CMS"}
* and returns a string properly escaped like
* ' src = "http://www.editam.com/?a=b&amp;c=d&amp;f=g" title = "Editam, &lt;Simplified&gt; CMS"'
* which is valid for strict XHTML
*/
WYMeditor.XmlHelper.prototype.tagOptions = function(options)
{
    var xml = this;
    xml._formated_options = '';

    for (var key in options) {
        var formated_options = '';
        var value = options[key];
        if(typeof value != 'function' && value.length > 0) {

    if(parseInt(key, 10) == key && typeof value == 'object'){
        key = value.shift();
        value = value.pop();
    }
    if(key !== '' && value !== ''){
        xml._formated_options += ' '+key+'="'+xml.escapeOnce(value)+'"';
    }
}
}
return xml._formated_options;
};

/*
* @name escapeEntities
* @description
* Escapes XML/HTML entities <, >, & and ". If seccond parameter is set to false it
* will not escape ". If set to true it will also escape '
*/
WYMeditor.XmlHelper.prototype.escapeEntities = function(string, escape_quotes)
{
    this._entitiesDiv.innerHTML = string;
    this._entitiesDiv.textContent = string;
    var result = this._entitiesDiv.innerHTML;
    if(typeof escape_quotes == 'undefined'){
        if(escape_quotes !== false) result = result.replace('"', '&quot;');
        if(escape_quotes === true)  result = result.replace('"', '&#039;');
    }
    return result;
};

/*
* Parses a string conatining tag attributes and values an returns an array formated like
*  [["src", "http://www.editam.com"], ["title", "Editam, Simplified CMS"]]
*/
WYMeditor.XmlHelper.prototype.parseAttributes = function(tag_attributes)
{
    // Use a compounded regex to match single quoted, double quoted and unquoted attribute pairs
    var result = [];
    var matches = tag_attributes.split(/((=\s*")(")("))|((=\s*\')(\')(\'))|((=\s*[^>\s]*))/g);
    if(matches.toString() != tag_attributes){
        for (var k in matches) {
            var v = matches[k];
            if(typeof v != 'function' && v.length !== 0){
                var re = new RegExp('(\\w+)\\s*'+v);
                var match = tag_attributes.match(re);
                if(match) {
                    var value = v.replace(/^[\s=]+/, "");
                    var delimiter = value.charAt(0);
                    delimiter = delimiter == '"' ? '"' : (delimiter=="'"?"'":'');
                    if(delimiter !== ''){
                        value = delimiter == '"' ? value.replace(/^"|"+$/g, '') :  value.replace(/^'|'+$/g, '');
                    }
                    tag_attributes = tag_attributes.replace(match[0],'');
                    result.push([match[1] , value]);
                }
            }
        }
    }
    return result;
};
/**
* XhtmlValidator for validating tag attributes
*
* @author Bermi Ferrer - http://bermi.org
*/
WYMeditor.XhtmlValidator = {
    "_attributes":
    {
        "core":
        {
            "except":[
            "base",
            "head",
            "html",
            "meta",
            "param",
            "script",
            "style",
            "title"
            ],
            "attributes":[
            "class",
            "id",
            "style",
            "title",
            "accesskey",
            "tabindex",
            "/^data-.*/"
            ]
        },
        "language":
        {
            "except":[
            "base",
            "br",
            "hr",
            "iframe",
            "param",
            "script"
            ],
            "attributes":
            {
                "dir":[
                "ltr",
                "rtl"
                ],
                "0":"lang",
                "1":"xml:lang"
            }
        },
        "keyboard":
        {
            "attributes":
            {
                "accesskey":/^(\w){1}$/,
                "tabindex":/^(\d)+$/
            }
        }
    },
    "_events":
    {
        "window":
        {
            "only":[
            "body"
            ],
            "attributes":[
            "onload",
            "onunload"
            ]
        },
        "form":
        {
            "only":[
            "form",
            "input",
            "textarea",
            "select",
            "a",
            "label",
            "button"
            ],
            "attributes":[
            "onchange",
            "onsubmit",
            "onreset",
            "onselect",
            "onblur",
            "onfocus"
            ]
        },
        "keyboard":
        {
            "except":[
            "base",
            "bdo",
            "br",
            "frame",
            "frameset",
            "head",
            "html",
            "iframe",
            "meta",
            "param",
            "script",
            "style",
            "title"
            ],
            "attributes":[
            "onkeydown",
            "onkeypress",
            "onkeyup"
            ]
        },
        "mouse":
        {
            "except":[
            "base",
            "bdo",
            "br",
            "head",
            "html",
            "meta",
            "param",
            "script",
            "style",
            "title"
            ],
            "attributes":[
            "onclick",
            "ondblclick",
            "onmousedown",
            "onmousemove",
            "onmouseover",
            "onmouseout",
            "onmouseup"
            ]
        }
    },
    "_tags":
    {
        "a":
        {
            "attributes":
            {
                "0":"charset",
                "1":"coords",
                "2":"href",
                "3":"hreflang",
                "4":"name",
                "5":"rel",
                "6":"rev",
                "shape":/^(rect|rectangle|circ|circle|poly|polygon)$/,
                "7":"type"
            }
        },
        "0":"abbr",
        "1":"acronym",
        "2":"address",
        "area":
        {
            "attributes":
            {
                "0":"alt",
                "1":"coords",
                "2":"href",
                "nohref":/^(true|false)$/,
                "shape":/^(rect|rectangle|circ|circle|poly|polygon)$/
            },
            "required":[
            "alt"
            ]
        },
        "3":"b",
        "base":
        {
            "attributes":[
            "href"
            ],
            "required":[
            "href"
            ]
        },
        "bdo":
        {
            "attributes":
            {
                "dir":/^(ltr|rtl)$/
            },
            "required":[
            "dir"
            ]
        },
        "4":"big",
        "blockquote":
        {
            "attributes":[
            "cite"
            ]
        },
        "5":"body",
        "6":"br",
        "button":
        {
            "attributes":
            {
                "disabled":/^(disabled)$/,
                "type":/^(button|reset|submit)$/,
                "0":"value"
            },
            "inside":"form"
        },
        "7":"caption",
        "8":"cite",
        "9":"code",
        "col":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify)$/,
                "0":"char",
                "1":"charoff",
                "span":/^(\d)+$/,
                "valign":/^(top|middle|bottom|baseline)$/,
                "2":"width"
            },
            "inside":"colgroup"
        },
        "colgroup":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify)$/,
                "0":"char",
                "1":"charoff",
                "span":/^(\d)+$/,
                "valign":/^(top|middle|bottom|baseline)$/,
                "2":"width"
            }
        },
        "10":"dd",
        "del":
        {
            "attributes":
            {
                "0":"cite",
                "datetime":/^([0-9]){8}/
            }
        },
        "11":"div",
        "12":"dfn",
        "13":"dl",
        "14":"dt",
        "15":"em",
        "fieldset":
        {
            "inside":"form"
        },
        "form":
        {
            "attributes":
            {
                "0":"action",
                "1":"accept",
                "2":"accept-charset",
                "3":"enctype",
                "method":/^(get|post)$/
            },
            "required":[
            "action"
            ]
        },
        "head":
        {
            "attributes":[
            "profile"
            ]
        },
        "16":"h1",
        "17":"h2",
        "18":"h3",
        "19":"h4",
        "20":"h5",
        "21":"h6",
        "22":"hr",
        "html":
        {
            "attributes":[
            "xmlns"
            ]
        },
        "23":"i",
        "img":
        {
            "attributes":[
            "alt",
            "src",
            "height",
            "ismap",
            "longdesc",
            "usemap",
            "width"
            ],
            "required":[
            "alt",
            "src"
            ]
        },
        "input":
        {
            "attributes":
            {
                "0":"accept",
                "1":"alt",
                "checked":/^(checked)$/,
                "disabled":/^(disabled)$/,
                "maxlength":/^(\d)+$/,
                "2":"name",
                "readonly":/^(readonly)$/,
                "size":/^(\d)+$/,
                "3":"src",
                "type":/^(button|checkbox|file|hidden|image|password|radio|reset|submit|text)$/,
                "4":"value"
            },
            "inside":"form"
        },
        "ins":
        {
            "attributes":
            {
                "0":"cite",
                "datetime":/^([0-9]){8}/
            }
        },
        "24":"kbd",
        "label":
        {
            "attributes":[
            "for"
            ],
            "inside":"form"
        },
        "25":"legend",
        "26":"li",
        "link":
        {
            "attributes":
            {
                "0":"charset",
                "1":"href",
                "2":"hreflang",
                "media":/^(all|braille|print|projection|screen|speech|,|;| )+$/i,
                //next comment line required by Opera!
                /*"rel":/^(alternate|appendix|bookmark|chapter|contents|copyright|glossary|help|home|index|next|prev|section|start|stylesheet|subsection| |shortcut|icon)+$/i,*/
                "rel":/^(alternate|appendix|bookmark|chapter|contents|copyright|glossary|help|home|index|next|prev|section|start|stylesheet|subsection| |shortcut|icon)+$/i,
                "rev":/^(alternate|appendix|bookmark|chapter|contents|copyright|glossary|help|home|index|next|prev|section|start|stylesheet|subsection| |shortcut|icon)+$/i,
                "3":"type"
            },
            "inside":"head"
        },
        "map":
        {
            "attributes":[
            "id",
            "name"
            ],
            "required":[
            "id"
            ]
        },
        "meta":
        {
            "attributes":
            {
                "0":"content",
                "http-equiv":/^(content\-type|expires|refresh|set\-cookie)$/i,
                "1":"name",
                "2":"scheme"
            },
            "required":[
            "content"
            ]
        },
        "27":"noscript",
        "object":
        {
            "attributes":[
            "archive",
            "classid",
            "codebase",
            "codetype",
            "data",
            "declare",
            "height",
            "name",
            "standby",
            "type",
            "usemap",
            "width"
            ]
        },
        "28":"ol",
        "optgroup":
        {
            "attributes":
            {
                "0":"label",
                "disabled": /^(disabled)$/
            },
            "required":[
            "label"
            ]
        },
        "option":
        {
            "attributes":
            {
                "0":"label",
                "disabled":/^(disabled)$/,
                "selected":/^(selected)$/,
                "1":"value"
            },
            "inside":"select"
        },
        "29":"p",
        "param":
        {
            "attributes":
            {
                "0":"type",
                "valuetype":/^(data|ref|object)$/,
                "1":"valuetype",
                "2":"value"
            },
            "required":[
            "name"
            ]
        },
        "30":"pre",
        "q":
        {
            "attributes":[
            "cite"
            ]
        },
        "31":"samp",
        "script":
        {
            "attributes":
            {
                "type":/^(text\/ecmascript|text\/javascript|text\/jscript|text\/vbscript|text\/vbs|text\/xml)$/,
                "0":"charset",
                "defer":/^(defer)$/,
                "1":"src"
            },
            "required":[
            "type"
            ]
        },
        "select":
        {
            "attributes":
            {
                "disabled":/^(disabled)$/,
                "multiple":/^(multiple)$/,
                "0":"name",
                "1":"size"
            },
            "inside":"form"
        },
        "32":"small",
        "33":"span",
        "34":"strong",
        "style":
        {
            "attributes":
            {
                "0":"type",
                "media":/^(screen|tty|tv|projection|handheld|print|braille|aural|all)$/
            },
            "required":[
            "type"
            ]
        },
        "35":"sub",
        "36":"sup",
        "table":
        {
            "attributes":
            {
                "0":"border",
                "1":"cellpadding",
                "2":"cellspacing",
                "frame":/^(void|above|below|hsides|lhs|rhs|vsides|box|border)$/,
                "rules":/^(none|groups|rows|cols|all)$/,
                "3":"summary",
                "4":"width"
            }
        },
        "tbody":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify)$/,
                "0":"char",
                "1":"charoff",
                "valign":/^(top|middle|bottom|baseline)$/
            }
        },
        "td":
        {
            "attributes":
            {
                "0":"abbr",
                "align":/^(left|right|center|justify|char)$/,
                "1":"axis",
                "2":"char",
                "3":"charoff",
                "colspan":/^(\d)+$/,
                "4":"headers",
                "rowspan":/^(\d)+$/,
                "scope":/^(col|colgroup|row|rowgroup)$/,
                "valign":/^(top|middle|bottom|baseline)$/
            }
        },
        "textarea":
        {
            "attributes":[
            "cols",
            "rows",
            "disabled",
            "name",
            "readonly"
            ],
            "required":[
            "cols",
            "rows"
            ],
            "inside":"form"
        },
        "tfoot":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify)$/,
                "0":"char",
                "1":"charoff",
                "valign":/^(top|middle|bottom)$/,
                "2":"baseline"
            }
        },
        "th":
        {
            "attributes":
            {
                "0":"abbr",
                "align":/^(left|right|center|justify|char)$/,
                "1":"axis",
                "2":"char",
                "3":"charoff",
                "colspan":/^(\d)+$/,
                "4":"headers",
                "rowspan":/^(\d)+$/,
                "scope":/^(col|colgroup|row|rowgroup)$/,
                "valign":/^(top|middle|bottom|baseline)$/
            }
        },
        "thead":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify)$/,
                "0":"char",
                "1":"charoff",
                "valign":/^(top|middle|bottom|baseline)$/
            }
        },
        "37":"title",
        "tr":
        {
            "attributes":
            {
                "align":/^(right|left|center|justify|char)$/,
                "0":"char",
                "1":"charoff",
                "valign":/^(top|middle|bottom|baseline)$/
            }
        },
        "38":"tt",
        "39":"ul",
        "40":"var"
    },

    // Temporary skiped attributes
    skiped_attributes : [],
    skiped_attribute_values : [],

    getValidTagAttributes: function(tag, attributes)
    {
        var valid_attributes = {};
        var possible_attributes = this.getPossibleTagAttributes(tag);
        for(var attribute in attributes) {
            var value = attributes[attribute];
            attribute = attribute.toLowerCase(); // ie8 uses colSpan
            var h = WYMeditor.Helper;
            if(!h.contains(this.skiped_attributes, attribute) && !h.contains(this.skiped_attribute_values, value)){
                if (typeof value != 'function' && h.contains(possible_attributes, attribute)) {
                    if (this.doesAttributeNeedsValidation(tag, attribute)) {
                        if(this.validateAttribute(tag, attribute, value)){
                            valid_attributes[attribute] = value;
                        }
                    }else{
                        valid_attributes[attribute] = value;
                    }
                } else {
                    jQuery.each(possible_attributes, function() {
                        if(this.match(/\/(.*)\//)) {
                            regex = new RegExp(this.match(/\/(.*)\//)[1]);
                            if(regex.test(attribute)) {
                                valid_attributes[attribute] = value;
                            }
                        }
                    });
                }
            }
        }
        return valid_attributes;
    },
    getUniqueAttributesAndEventsForTag : function(tag)
    {
        var result = [];

        if (this._tags[tag] && this._tags[tag].attributes) {
            for (var k in this._tags[tag].attributes) {
                result.push(parseInt(k, 10) == k ? this._tags[tag].attributes[k] : k);
            }
        }
        return result;
    },
getDefaultAttributesAndEventsForTags : function()
{
    var result = [];
    for (var key in this._events){
        result.push(this._events[key]);
    }
    for (key in this._attributes){
        result.push(this._attributes[key]);
    }
    return result;
},
isValidTag : function(tag)
{
    if(this._tags[tag]){
        return true;
    }
    for(var key in this._tags){
        if(this._tags[key] == tag){
            return true;
        }
    }
    return false;
},
getDefaultAttributesAndEventsForTag : function(tag)
{
    var default_attributes = [];
    if (this.isValidTag(tag)) {
        var default_attributes_and_events = this.getDefaultAttributesAndEventsForTags();

    for(var key in default_attributes_and_events) {
        var defaults = default_attributes_and_events[key];
        if(typeof defaults == 'object'){
            var h = WYMeditor.Helper;
            if ((defaults['except'] && h.contains(defaults['except'], tag)) || (defaults['only'] && !h.contains(defaults['only'], tag))) {
                continue;
            }

    var tag_defaults = defaults['attributes'] ? defaults['attributes'] : defaults['events'];
    for(var k in tag_defaults) {
        default_attributes.push(typeof tag_defaults[k] != 'string' ? k : tag_defaults[k]);
    }
}
}
}
return default_attributes;
},
doesAttributeNeedsValidation: function(tag, attribute)
{
    return this._tags[tag] && ((this._tags[tag]['attributes'] && this._tags[tag]['attributes'][attribute]) || (this._tags[tag]['required'] &&
        WYMeditor.Helper.contains(this._tags[tag]['required'], attribute)));
},
validateAttribute : function(tag, attribute, value)
{
    if ( this._tags[tag] &&
        (this._tags[tag]['attributes'] && this._tags[tag]['attributes'][attribute] && value.length > 0 && !value.match(this._tags[tag]['attributes'][attribute])) || // invalid format
        (this._tags[tag] && this._tags[tag]['required'] && WYMeditor.Helper.contains(this._tags[tag]['required'], attribute) && value.length === 0)) // required attribute
    {
        return false;
    }
    return typeof this._tags[tag] != 'undefined';
},
getPossibleTagAttributes : function(tag)
{
    if (!this._possible_tag_attributes) {
        this._possible_tag_attributes = {};
    }
    if (!this._possible_tag_attributes[tag]) {
        this._possible_tag_attributes[tag] = this.getUniqueAttributesAndEventsForTag(tag).concat(this.getDefaultAttributesAndEventsForTag(tag));
    }
    return this._possible_tag_attributes[tag];
}
};

/**
*    Compounded regular expression. Any of
*    the contained patterns could match and
*    when one does, it's label is returned.
*
*    Constructor. Starts with no patterns.
*    @param boolean case    True for case sensitive, false
*                            for insensitive.
*    @access public
*    @author Marcus Baker (http://lastcraft.com)
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.ParallelRegex = function(case_sensitive)
{
    this._case = case_sensitive;
    this._patterns = [];
    this._labels = [];
    this._regex = null;
    return this;
};


/**
*    Adds a pattern with an optional label.
*    @param string pattern      Perl style regex, but ( and )
*                                lose the usual meaning.
*    @param string label        Label of regex to be returned
*                                on a match.
*    @access public
*/
WYMeditor.ParallelRegex.prototype.addPattern = function(pattern, label)
{
    label = label || true;
    var count = this._patterns.length;
    this._patterns[count] = pattern;
    this._labels[count] = label;
    this._regex = null;
};

/**
*    Attempts to match all patterns at once against
*    a string.
*    @param string subject      String to match against.
*
*    @return boolean             True on success.
*    @return string match         First matched portion of
*                                subject.
*    @access public
*/
WYMeditor.ParallelRegex.prototype.match = function(subject)
{
    if (this._patterns.length === 0) {
        return [false, ''];
    }
    var matches = subject.match(this._getCompoundedRegex());

    if(!matches){
        return [false, ''];
    }
    var match = matches[0];
    for (var i = 1; i < matches.length; i++) {
        if (matches[i]) {
            return [this._labels[i-1], match];
        }
    }
    return [true, matches[0]];
};

/**
*    Compounds the patterns into a single
*    regular expression separated with the
*    "or" operator. Caches the regex.
*    Will automatically escape (, ) and / tokens.
*    @param array patterns    List of patterns in order.
*    @access private
*/
WYMeditor.ParallelRegex.prototype._getCompoundedRegex = function()
{
    if (this._regex === null) {
        for (var i = 0, count = this._patterns.length; i < count; i++) {
            this._patterns[i] = '(' + this._untokenizeRegex(this._tokenizeRegex(this._patterns[i]).replace(/([\/\(\)])/g,'\\$1')) + ')';
        }
        this._regex = new RegExp(this._patterns.join("|") ,this._getPerlMatchingFlags());
    }
    return this._regex;
};

/**
* Escape lookahead/lookbehind blocks
*/
WYMeditor.ParallelRegex.prototype._tokenizeRegex = function(regex)
{
    return regex.
    replace(/\(\?(i|m|s|x|U)\)/,     '~~~~~~Tk1\$1~~~~~~').
    replace(/\(\?(\-[i|m|s|x|U])\)/, '~~~~~~Tk2\$1~~~~~~').
    replace(/\(\?\=(.*)\)/,          '~~~~~~Tk3\$1~~~~~~').
    replace(/\(\?\!(.*)\)/,          '~~~~~~Tk4\$1~~~~~~').
    replace(/\(\?\<\=(.*)\)/,        '~~~~~~Tk5\$1~~~~~~').
    replace(/\(\?\<\!(.*)\)/,        '~~~~~~Tk6\$1~~~~~~').
    replace(/\(\?\:(.*)\)/,          '~~~~~~Tk7\$1~~~~~~');
};

/**
* Unscape lookahead/lookbehind blocks
*/
WYMeditor.ParallelRegex.prototype._untokenizeRegex = function(regex)
{
    return regex.
    replace(/~~~~~~Tk1(.{1})~~~~~~/,    "(?\$1)").
    replace(/~~~~~~Tk2(.{2})~~~~~~/,    "(?\$1)").
    replace(/~~~~~~Tk3(.*)~~~~~~/,      "(?=\$1)").
    replace(/~~~~~~Tk4(.*)~~~~~~/,      "(?!\$1)").
    replace(/~~~~~~Tk5(.*)~~~~~~/,      "(?<=\$1)").
    replace(/~~~~~~Tk6(.*)~~~~~~/,      "(?<!\$1)").
    replace(/~~~~~~Tk7(.*)~~~~~~/,      "(?:\$1)");
};


/**
*    Accessor for perl regex mode flags to use.
*    @return string       Perl regex flags.
*    @access private
*/
WYMeditor.ParallelRegex.prototype._getPerlMatchingFlags = function()
{
    return (this._case ? "m" : "mi");
};

/**
*    States for a stack machine.
*
*    Constructor. Starts in named state.
*    @param string start        Starting state name.
*    @access public
*    @author Marcus Baker (http://lastcraft.com)
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.StateStack = function(start)
{
    this._stack = [start];
    return this;
};

/**
*    Accessor for current state.
*    @return string       State.
*    @access public
*/
WYMeditor.StateStack.prototype.getCurrent = function()
{
    return this._stack[this._stack.length - 1];
};

/**
*    Adds a state to the stack and sets it
*    to be the current state.
*    @param string state        New state.
*    @access public
*/
WYMeditor.StateStack.prototype.enter = function(state)
{
    this._stack.push(state);
};

/**
*    Leaves the current state and reverts
*    to the previous one.
*    @return boolean    False if we drop off
*                       the bottom of the list.
*    @access public
*/
WYMeditor.StateStack.prototype.leave = function()
{
    if (this._stack.length == 1) {
        return false;
    }
    this._stack.pop();
    return true;
};

// GLOBALS
WYMeditor.LEXER_ENTER = 1;
WYMeditor.LEXER_MATCHED = 2;
WYMeditor.LEXER_UNMATCHED = 3;
WYMeditor.LEXER_EXIT = 4;
WYMeditor.LEXER_SPECIAL = 5;


/**
*    Accepts text and breaks it into tokens.
*    Some optimisation to make the sure the
*    content is only scanned by the PHP regex
*    parser once. Lexer modes must not start
*    with leading underscores.
*
*    Sets up the lexer in case insensitive matching
*    by default.
*    @param Parser parser  Handling strategy by reference.
*    @param string start            Starting handler.
*    @param boolean case            True for case sensitive.
*    @access public
*    @author Marcus Baker (http://lastcraft.com)
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.Lexer = function(parser, start, case_sensitive)
{
    start = start || 'accept';
    this._case = case_sensitive || false;
    this._regexes = {};
    this._parser = parser;
    this._mode = new WYMeditor.StateStack(start);
    this._mode_handlers = {};
    this._mode_handlers[start] = start;
    return this;
};

/**
*    Adds a token search pattern for a particular
*    parsing mode. The pattern does not change the
*    current mode.
*    @param string pattern      Perl style regex, but ( and )
*                                lose the usual meaning.
*    @param string mode         Should only apply this
*                                pattern when dealing with
*                                this type of input.
*    @access public
*/
WYMeditor.Lexer.prototype.addPattern = function(pattern, mode)
{
    mode = mode || "accept";
    if (typeof this._regexes[mode] == 'undefined') {
        this._regexes[mode] = new WYMeditor.ParallelRegex(this._case);
    }
    this._regexes[mode].addPattern(pattern);
    if (typeof this._mode_handlers[mode] == 'undefined') {
        this._mode_handlers[mode] = mode;
    }
};

/**
*    Adds a pattern that will enter a new parsing
*    mode. Useful for entering parenthesis, strings,
*    tags, etc.
*    @param string pattern      Perl style regex, but ( and )
*                                lose the usual meaning.
*    @param string mode         Should only apply this
*                                pattern when dealing with
*                                this type of input.
*    @param string new_mode     Change parsing to this new
*                                nested mode.
*    @access public
*/
WYMeditor.Lexer.prototype.addEntryPattern = function(pattern, mode, new_mode)
{
    if (typeof this._regexes[mode] == 'undefined') {
        this._regexes[mode] = new WYMeditor.ParallelRegex(this._case);
    }
    this._regexes[mode].addPattern(pattern, new_mode);
    if (typeof this._mode_handlers[new_mode] == 'undefined') {
        this._mode_handlers[new_mode] = new_mode;
    }
};

/**
*    Adds a pattern that will exit the current mode
*    and re-enter the previous one.
*    @param string pattern      Perl style regex, but ( and )
*                                lose the usual meaning.
*    @param string mode         Mode to leave.
*    @access public
*/
WYMeditor.Lexer.prototype.addExitPattern = function(pattern, mode)
{
    if (typeof this._regexes[mode] == 'undefined') {
        this._regexes[mode] = new WYMeditor.ParallelRegex(this._case);
    }
    this._regexes[mode].addPattern(pattern, "__exit");
    if (typeof this._mode_handlers[mode] == 'undefined') {
        this._mode_handlers[mode] = mode;
    }
};

/**
*    Adds a pattern that has a special mode. Acts as an entry
*    and exit pattern in one go, effectively calling a special
*    parser handler for this token only.
*    @param string pattern      Perl style regex, but ( and )
*                                lose the usual meaning.
*    @param string mode         Should only apply this
*                                pattern when dealing with
*                                this type of input.
*    @param string special      Use this mode for this one token.
*    @access public
*/
WYMeditor.Lexer.prototype.addSpecialPattern =  function(pattern, mode, special)
{
    if (typeof this._regexes[mode] == 'undefined') {
        this._regexes[mode] = new WYMeditor.ParallelRegex(this._case);
    }
    this._regexes[mode].addPattern(pattern, '_'+special);
    if (typeof this._mode_handlers[special] == 'undefined') {
        this._mode_handlers[special] = special;
    }
};

/**
*    Adds a mapping from a mode to another handler.
*    @param string mode        Mode to be remapped.
*    @param string handler     New target handler.
*    @access public
*/
WYMeditor.Lexer.prototype.mapHandler = function(mode, handler)
{
    this._mode_handlers[mode] = handler;
};

/**
*    Splits the page text into tokens. Will fail
*    if the handlers report an error or if no
*    content is consumed. If successful then each
*    unparsed and parsed token invokes a call to the
*    held listener.
*    @param string raw        Raw HTML text.
*    @return boolean           True on success, else false.
*    @access public
*/
WYMeditor.Lexer.prototype.parse = function(raw) {
    if (typeof this._parser == 'undefined') {
        return false;
    }

    var length = raw.length;
    var parsed;
    while (typeof (parsed = this._reduce(raw)) == 'object') {
        raw = parsed[0];
        var unmatched = parsed[1];
        var matched = parsed[2];
        var mode = parsed[3];

        if (! this._dispatchTokens(unmatched, matched, mode)) {
            return false;
        }

        if (raw === '') {
            return true;
        }
        if (raw.length == length) {
            return false;
        }
        length = raw.length;
    }
    if (! parsed ) {
        return false;
    }

    return this._invokeParser(raw, WYMeditor.LEXER_UNMATCHED);
};

/**
*    Sends the matched token and any leading unmatched
*    text to the parser changing the lexer to a new
*    mode if one is listed.
*    @param string unmatched    Unmatched leading portion.
*    @param string matched      Actual token match.
*    @param string mode         Mode after match. A boolean
*                                false mode causes no change.
*    @return boolean             False if there was any error
*                                from the parser.
*    @access private
*/
WYMeditor.Lexer.prototype._dispatchTokens = function(unmatched, matched, mode) {
    mode = mode || false;

    if (! this._invokeParser(unmatched, WYMeditor.LEXER_UNMATCHED)) {
        return false;
    }

    if (typeof mode == 'boolean') {
        return this._invokeParser(matched, WYMeditor.LEXER_MATCHED);
    }
    if (this._isModeEnd(mode)) {
        if (! this._invokeParser(matched, WYMeditor.LEXER_EXIT)) {
            return false;
        }
        return this._mode.leave();
    }
    if (this._isSpecialMode(mode)) {
        this._mode.enter(this._decodeSpecial(mode));
        if (! this._invokeParser(matched, WYMeditor.LEXER_SPECIAL)) {
            return false;
        }
        return this._mode.leave();
    }
    this._mode.enter(mode);

    return this._invokeParser(matched, WYMeditor.LEXER_ENTER);
};

/**
*    Tests to see if the new mode is actually to leave
*    the current mode and pop an item from the matching
*    mode stack.
*    @param string mode    Mode to test.
*    @return boolean        True if this is the exit mode.
*    @access private
*/
WYMeditor.Lexer.prototype._isModeEnd = function(mode) {
    return (mode === "__exit");
};

/**
*    Test to see if the mode is one where this mode
*    is entered for this token only and automatically
*    leaves immediately afterwoods.
*    @param string mode    Mode to test.
*    @return boolean        True if this is the exit mode.
*    @access private
*/
WYMeditor.Lexer.prototype._isSpecialMode = function(mode) {
    return (mode.substring(0,1) == "_");
};

/**
*    Strips the magic underscore marking single token
*    modes.
*    @param string mode    Mode to decode.
*    @return string         Underlying mode name.
*    @access private
*/
WYMeditor.Lexer.prototype._decodeSpecial = function(mode) {
    return mode.substring(1);
};

/**
*    Calls the parser method named after the current
*    mode. Empty content will be ignored. The lexer
*    has a parser handler for each mode in the lexer.
*    @param string content        Text parsed.
*    @param boolean is_match      Token is recognised rather
*                                  than unparsed data.
*    @access private
*/
WYMeditor.Lexer.prototype._invokeParser = function(content, is_match) {
    if (content === '') {
        return true;
    }
    var current = this._mode.getCurrent();
    var handler = this._mode_handlers[current];
    var result = this._parser[handler](content, is_match);
    return result;
};

/**
*    Tries to match a chunk of text and if successful
*    removes the recognised chunk and any leading
*    unparsed data. Empty strings will not be matched.
*    @param string raw         The subject to parse. This is the
*                               content that will be eaten.
*    @return array/boolean      Three item list of unparsed
*                               content followed by the
*                               recognised token and finally the
*                               action the parser is to take.
*                               True if no match, false if there
*                               is a parsing error.
*    @access private
*/
WYMeditor.Lexer.prototype._reduce = function(raw) {
    var matched = this._regexes[this._mode.getCurrent()].match(raw);
    var match = matched[1];
    var action = matched[0];
    if (action) {
        var unparsed_character_count = raw.indexOf(match);
        var unparsed = raw.substr(0, unparsed_character_count);
        raw = raw.substring(unparsed_character_count + match.length);
        return [raw, unparsed, match, action];
    }
    return true;
};

/**
* This are the rules for breaking the XHTML code into events
* handled by the provided parser.
*
*    @author Marcus Baker (http://lastcraft.com)
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.XhtmlLexer = function(parser) {
    jQuery.extend(this, new WYMeditor.Lexer(parser, 'Text'));

    this.mapHandler('Text', 'Text');

    this.addTokens();

    this.init();

    return this;
};


WYMeditor.XhtmlLexer.prototype.init = function() {
};

WYMeditor.XhtmlLexer.prototype.addTokens = function() {
    this.addCommentTokens('Text');
    this.addScriptTokens('Text');
    this.addCssTokens('Text');
    this.addTagTokens('Text');
};

WYMeditor.XhtmlLexer.prototype.addCommentTokens = function(scope) {
    this.addEntryPattern("<!--", scope, 'Comment');
    this.addExitPattern("-->", 'Comment');
};

WYMeditor.XhtmlLexer.prototype.addScriptTokens = function(scope) {
    this.addEntryPattern("<script", scope, 'Script');
    this.addExitPattern("</script>", 'Script');
};

WYMeditor.XhtmlLexer.prototype.addCssTokens = function(scope) {
    this.addEntryPattern("<style", scope, 'Css');
    this.addExitPattern("</style>", 'Css');
};

WYMeditor.XhtmlLexer.prototype.addTagTokens = function(scope) {
    this.addSpecialPattern("<\\s*[a-z0-9:\-]+\\s*>", scope, 'OpeningTag');
    this.addEntryPattern("<[a-z0-9:\-]+"+'[\\\/ \\\>]+', scope, 'OpeningTag');
    this.addInTagDeclarationTokens('OpeningTag');

    this.addSpecialPattern("</\\s*[a-z0-9:\-]+\\s*>", scope, 'ClosingTag');

};

WYMeditor.XhtmlLexer.prototype.addInTagDeclarationTokens = function(scope) {
    this.addSpecialPattern('\\s+', scope, 'Ignore');

    this.addAttributeTokens(scope);

    this.addExitPattern('/>', scope);
    this.addExitPattern('>', scope);

};

WYMeditor.XhtmlLexer.prototype.addAttributeTokens = function(scope) {
    this.addSpecialPattern("\\s*[a-z-_0-9]*:?[a-z-_0-9]+\\s*(?=\=)\\s*", scope, 'TagAttributes');

    this.addEntryPattern('=\\s*"', scope, 'DoubleQuotedAttribute');
    this.addPattern("\\\\\"", 'DoubleQuotedAttribute');
    this.addExitPattern('"', 'DoubleQuotedAttribute');

    this.addEntryPattern("=\\s*'", scope, 'SingleQuotedAttribute');
    this.addPattern("\\\\'", 'SingleQuotedAttribute');
    this.addExitPattern("'", 'SingleQuotedAttribute');

    this.addSpecialPattern('=\\s*[^>\\s]*', scope, 'UnquotedAttribute');
};

/**
* XHTML Parser.
*
* This XHTML parser will trigger the events available on on
* current SaxListener
*
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.XhtmlParser = function(Listener, mode) {
    mode = mode || 'Text';
    this._Lexer = new WYMeditor.XhtmlLexer(this);
    this._Listener = Listener;
    this._mode = mode;
    this._matches = [];
    this._last_match = '';
    this._current_match = '';

    return this;
};

WYMeditor.XhtmlParser.prototype.parse = function(raw) {
    this._Lexer.parse(this.beforeParsing(raw));
    return this.afterParsing(this._Listener.getResult());
};

WYMeditor.XhtmlParser.prototype.beforeParsing = function(raw) {
    if (raw.match(/class="MsoNormal"/) || raw.match(/ns = "urn:schemas-microsoft-com/)) {
        // Usefull for cleaning up content pasted from other sources (MSWord)
        this._Listener.avoidStylingTagsAndAttributes();
    }
    return this._Listener.beforeParsing(raw);
};

WYMeditor.XhtmlParser.prototype.afterParsing = function(parsed) {
    if (this._Listener._avoiding_tags_implicitly) {
        this._Listener.allowStylingTagsAndAttributes();
    }
    return this._Listener.afterParsing(parsed);
};


WYMeditor.XhtmlParser.prototype.Ignore = function(match, state) {
    return true;
};

WYMeditor.XhtmlParser.prototype.Text = function(text) {
    this._Listener.addContent(text);
    return true;
};

WYMeditor.XhtmlParser.prototype.Comment = function(match, status) {
    return this._addNonTagBlock(match, status, 'addComment');
};

WYMeditor.XhtmlParser.prototype.Script = function(match, status) {
    return this._addNonTagBlock(match, status, 'addScript');
};

WYMeditor.XhtmlParser.prototype.Css = function(match, status) {
    return this._addNonTagBlock(match, status, 'addCss');
};

WYMeditor.XhtmlParser.prototype._addNonTagBlock = function(match, state, type) {
    switch (state) {
        case WYMeditor.LEXER_ENTER:
            this._non_tag = match;
            break;
        case WYMeditor.LEXER_UNMATCHED:
            this._non_tag += match;
            break;
        case WYMeditor.LEXER_EXIT:
            switch(type) {
                case 'addComment':
                    this._Listener.addComment(this._non_tag+match);
                    break;
                case 'addScript':
                    this._Listener.addScript(this._non_tag+match);
                    break;
                case 'addCss':
                    this._Listener.addCss(this._non_tag+match);
                    break;
                default:
                    break;
            }
            break;
        default:
            break;
    }
    return true;
};

WYMeditor.XhtmlParser.prototype.OpeningTag = function(match, state) {
    switch (state){
        case WYMeditor.LEXER_ENTER:
            this._tag = this.normalizeTag(match);
            this._tag_attributes = {};
            break;
        case WYMeditor.LEXER_SPECIAL:
            this._callOpenTagListener(this.normalizeTag(match));
            break;
        case WYMeditor.LEXER_EXIT:
            this._callOpenTagListener(this._tag, this._tag_attributes);
            break;
        default:
            break;
    }
    return true;
};

WYMeditor.XhtmlParser.prototype.ClosingTag = function(match, state) {
    this._callCloseTagListener(this.normalizeTag(match));
    return true;
};

WYMeditor.XhtmlParser.prototype._callOpenTagListener = function(tag, attributes) {
    attributes = attributes || {};
    this.autoCloseUnclosedBeforeNewOpening(tag);

    if (this._Listener.isBlockTag(tag)) {
        this._Listener._tag_stack.push(tag);
        this._Listener.fixNestingBeforeOpeningBlockTag(tag, attributes);
        this._Listener.openBlockTag(tag, attributes);
        this._increaseOpenTagCounter(tag);
    } else if (this._Listener.isInlineTag(tag)) {
        this._Listener.inlineTag(tag, attributes);
    } else {
        this._Listener.openUnknownTag(tag, attributes);
        this._increaseOpenTagCounter(tag);
    }
    this._Listener.last_tag = tag;
    this._Listener.last_tag_opened = true;
    this._Listener.last_tag_attributes = attributes;
};

WYMeditor.XhtmlParser.prototype._callCloseTagListener = function(tag) {
    if (this._decreaseOpenTagCounter(tag)) {
        this.autoCloseUnclosedBeforeTagClosing(tag);

        if (this._Listener.isBlockTag(tag)) {
            var expected_tag = this._Listener._tag_stack.pop();
            if (expected_tag === false) {
                return;
            } else if (expected_tag != tag) {
                tag = expected_tag;
            }
            this._Listener.closeBlockTag(tag);
        } else {
            this._Listener.closeUnknownTag(tag);
        }
    } else {
        this._Listener.closeUnopenedTag(tag);
    }
    this._Listener.last_tag = tag;
    this._Listener.last_tag_opened = false;
};

WYMeditor.XhtmlParser.prototype._increaseOpenTagCounter = function(tag) {
    this._Listener._open_tags[tag] = this._Listener._open_tags[tag] || 0;
    this._Listener._open_tags[tag]++;
};

WYMeditor.XhtmlParser.prototype._decreaseOpenTagCounter = function(tag) {
    if (this._Listener._open_tags[tag]) {
        this._Listener._open_tags[tag]--;
        if (this._Listener._open_tags[tag] === 0) {
            this._Listener._open_tags[tag] = undefined;
        }
        return true;
    }
    return false;
};

WYMeditor.XhtmlParser.prototype.autoCloseUnclosedBeforeNewOpening = function(new_tag) {
    this._autoCloseUnclosed(new_tag, false);
};

WYMeditor.XhtmlParser.prototype.autoCloseUnclosedBeforeTagClosing = function(tag) {
    this._autoCloseUnclosed(tag, true);
};

WYMeditor.XhtmlParser.prototype._autoCloseUnclosed = function(new_tag, closing) {
    closing = closing || false;
    if (this._Listener._open_tags) {
        for (var tag in this._Listener._open_tags) {
            var counter = this._Listener._open_tags[tag];
            if (counter > 0 && this._Listener.shouldCloseTagAutomatically(tag, new_tag, closing)) {
                this._callCloseTagListener(tag, true);
            }
        }
    }
};

WYMeditor.XhtmlParser.prototype.getTagReplacements = function() {
    return this._Listener.getTagReplacements();
};

WYMeditor.XhtmlParser.prototype.normalizeTag = function(tag) {
    tag = tag.replace(/^([\s<\/>]*)|([\s<\/>]*)$/gm,'').toLowerCase();
    var tags = this._Listener.getTagReplacements();
    if (tags[tag]) {
        return tags[tag];
    }
    return tag;
};

WYMeditor.XhtmlParser.prototype.TagAttributes = function(match, state) {
    if (WYMeditor.LEXER_SPECIAL == state) {
        this._current_attribute = match;
    }
    return true;
};

WYMeditor.XhtmlParser.prototype.DoubleQuotedAttribute = function(match, state) {
    if (WYMeditor.LEXER_UNMATCHED == state) {
        this._tag_attributes[this._current_attribute] = match;
    }
    return true;
};

WYMeditor.XhtmlParser.prototype.SingleQuotedAttribute = function(match, state) {
    if (WYMeditor.LEXER_UNMATCHED == state) {
        this._tag_attributes[this._current_attribute] = match;
    }
    return true;
};

WYMeditor.XhtmlParser.prototype.UnquotedAttribute = function(match, state) {
    this._tag_attributes[this._current_attribute] = match.replace(/^=/,'');
    return true;
};

/**
* XHTML Sax parser.
*
*    @author Bermi Ferrer (http://bermi.org)
*/
WYMeditor.XhtmlSaxListener = function() {
    this.output = '';
    this.helper = new WYMeditor.XmlHelper();
    this._open_tags = {};
    this.validator = WYMeditor.XhtmlValidator;
    this._tag_stack = [];
    this.avoided_tags = [];

    this.entities = {
        '&nbsp;':'&#160;','&iexcl;':'&#161;','&cent;':'&#162;',
        '&pound;':'&#163;','&curren;':'&#164;','&yen;':'&#165;',
        '&brvbar;':'&#166;','&sect;':'&#167;','&uml;':'&#168;',
        '&copy;':'&#169;','&ordf;':'&#170;','&laquo;':'&#171;',
        '&not;':'&#172;','&shy;':'&#173;','&reg;':'&#174;',
        '&macr;':'&#175;','&deg;':'&#176;','&plusmn;':'&#177;',
        '&sup2;':'&#178;','&sup3;':'&#179;','&acute;':'&#180;',
        '&micro;':'&#181;','&para;':'&#182;','&middot;':'&#183;',
        '&cedil;':'&#184;','&sup1;':'&#185;','&ordm;':'&#186;',
        '&raquo;':'&#187;','&frac14;':'&#188;','&frac12;':'&#189;',
        '&frac34;':'&#190;','&iquest;':'&#191;','&Agrave;':'&#192;',
        '&Aacute;':'&#193;','&Acirc;':'&#194;','&Atilde;':'&#195;',
        '&Auml;':'&#196;','&Aring;':'&#197;','&AElig;':'&#198;',
        '&Ccedil;':'&#199;','&Egrave;':'&#200;','&Eacute;':'&#201;',
        '&Ecirc;':'&#202;','&Euml;':'&#203;','&Igrave;':'&#204;',
        '&Iacute;':'&#205;','&Icirc;':'&#206;','&Iuml;':'&#207;',
        '&ETH;':'&#208;','&Ntilde;':'&#209;','&Ograve;':'&#210;',
        '&Oacute;':'&#211;','&Ocirc;':'&#212;','&Otilde;':'&#213;',
        '&Ouml;':'&#214;','&times;':'&#215;','&Oslash;':'&#216;',
        '&Ugrave;':'&#217;','&Uacute;':'&#218;','&Ucirc;':'&#219;',
        '&Uuml;':'&#220;','&Yacute;':'&#221;','&THORN;':'&#222;',
        '&szlig;':'&#223;','&agrave;':'&#224;','&aacute;':'&#225;',
        '&acirc;':'&#226;','&atilde;':'&#227;','&auml;':'&#228;',
        '&aring;':'&#229;','&aelig;':'&#230;','&ccedil;':'&#231;',
        '&egrave;':'&#232;','&eacute;':'&#233;','&ecirc;':'&#234;',
        '&euml;':'&#235;','&igrave;':'&#236;','&iacute;':'&#237;',
        '&icirc;':'&#238;','&iuml;':'&#239;','&eth;':'&#240;',
        '&ntilde;':'&#241;','&ograve;':'&#242;','&oacute;':'&#243;',
        '&ocirc;':'&#244;','&otilde;':'&#245;','&ouml;':'&#246;',
        '&divide;':'&#247;','&oslash;':'&#248;','&ugrave;':'&#249;',
        '&uacute;':'&#250;','&ucirc;':'&#251;','&uuml;':'&#252;',
        '&yacute;':'&#253;','&thorn;':'&#254;','&yuml;':'&#255;',
        '&OElig;':'&#338;','&oelig;':'&#339;','&Scaron;':'&#352;',
        '&scaron;':'&#353;','&Yuml;':'&#376;','&fnof;':'&#402;',
        '&circ;':'&#710;','&tilde;':'&#732;','&Alpha;':'&#913;',
        '&Beta;':'&#914;','&Gamma;':'&#915;','&Delta;':'&#916;',
        '&Epsilon;':'&#917;','&Zeta;':'&#918;','&Eta;':'&#919;',
        '&Theta;':'&#920;','&Iota;':'&#921;','&Kappa;':'&#922;',
        '&Lambda;':'&#923;','&Mu;':'&#924;','&Nu;':'&#925;',
        '&Xi;':'&#926;','&Omicron;':'&#927;','&Pi;':'&#928;',
        '&Rho;':'&#929;','&Sigma;':'&#931;','&Tau;':'&#932;',
        '&Upsilon;':'&#933;','&Phi;':'&#934;','&Chi;':'&#935;',
        '&Psi;':'&#936;','&Omega;':'&#937;','&alpha;':'&#945;',
        '&beta;':'&#946;','&gamma;':'&#947;','&delta;':'&#948;',
        '&epsilon;':'&#949;','&zeta;':'&#950;','&eta;':'&#951;',
        '&theta;':'&#952;','&iota;':'&#953;','&kappa;':'&#954;',
        '&lambda;':'&#955;','&mu;':'&#956;','&nu;':'&#957;',
        '&xi;':'&#958;','&omicron;':'&#959;','&pi;':'&#960;',
        '&rho;':'&#961;','&sigmaf;':'&#962;','&sigma;':'&#963;',
        '&tau;':'&#964;','&upsilon;':'&#965;','&phi;':'&#966;',
        '&chi;':'&#967;','&psi;':'&#968;','&omega;':'&#969;',
        '&thetasym;':'&#977;','&upsih;':'&#978;','&piv;':'&#982;',
        '&ensp;':'&#8194;','&emsp;':'&#8195;','&thinsp;':'&#8201;',
        '&zwnj;':'&#8204;','&zwj;':'&#8205;','&lrm;':'&#8206;',
        '&rlm;':'&#8207;','&ndash;':'&#8211;','&mdash;':'&#8212;',
        '&lsquo;':'&#8216;','&rsquo;':'&#8217;','&sbquo;':'&#8218;',
        '&ldquo;':'&#8220;','&rdquo;':'&#8221;','&bdquo;':'&#8222;',
        '&dagger;':'&#8224;','&Dagger;':'&#8225;','&bull;':'&#8226;',
        '&hellip;':'&#8230;','&permil;':'&#8240;','&prime;':'&#8242;',
        '&Prime;':'&#8243;','&lsaquo;':'&#8249;','&rsaquo;':'&#8250;',
        '&oline;':'&#8254;','&frasl;':'&#8260;','&euro;':'&#8364;',
        '&image;':'&#8465;','&weierp;':'&#8472;','&real;':'&#8476;',
        '&trade;':'&#8482;','&alefsym;':'&#8501;','&larr;':'&#8592;',
        '&uarr;':'&#8593;','&rarr;':'&#8594;','&darr;':'&#8595;',
        '&harr;':'&#8596;','&crarr;':'&#8629;','&lArr;':'&#8656;',
        '&uArr;':'&#8657;','&rArr;':'&#8658;','&dArr;':'&#8659;',
        '&hArr;':'&#8660;','&forall;':'&#8704;','&part;':'&#8706;',
        '&exist;':'&#8707;','&empty;':'&#8709;','&nabla;':'&#8711;',
        '&isin;':'&#8712;','&notin;':'&#8713;','&ni;':'&#8715;',
        '&prod;':'&#8719;','&sum;':'&#8721;','&minus;':'&#8722;',
        '&lowast;':'&#8727;','&radic;':'&#8730;','&prop;':'&#8733;',
        '&infin;':'&#8734;','&ang;':'&#8736;','&and;':'&#8743;',
        '&or;':'&#8744;','&cap;':'&#8745;','&cup;':'&#8746;',
        '&int;':'&#8747;','&there4;':'&#8756;','&sim;':'&#8764;',
        '&cong;':'&#8773;','&asymp;':'&#8776;','&ne;':'&#8800;',
        '&equiv;':'&#8801;','&le;':'&#8804;','&ge;':'&#8805;',
        '&sub;':'&#8834;','&sup;':'&#8835;','&nsub;':'&#8836;',
        '&sube;':'&#8838;','&supe;':'&#8839;','&oplus;':'&#8853;',
        '&otimes;':'&#8855;','&perp;':'&#8869;','&sdot;':'&#8901;',
        '&lceil;':'&#8968;','&rceil;':'&#8969;','&lfloor;':'&#8970;',
        '&rfloor;':'&#8971;','&lang;':'&#9001;','&rang;':'&#9002;',
        '&loz;':'&#9674;','&spades;':'&#9824;','&clubs;':'&#9827;',
        '&hearts;':'&#9829;','&diams;':'&#9830;'};

    this.block_tags = [
        "a", "abbr", "acronym", "address", "area", "b",
        "base", "bdo", "big", "blockquote", "body", "button",
        "caption", "cite", "code", "col", "colgroup", "dd", "del", "div",
        "dfn", "dl", "dt", "em", "fieldset", "form", "head", "h1", "h2",
        "h3", "h4", "h5", "h6", "html", "i", "ins",
        "kbd", "label", "legend", "li", "map", "noscript",
        "object", "ol", "optgroup", "option", "p", "param", "pre", "q",
        "samp", "script", "select", "small", "span", "strong", "style",
        "sub", "sup", "table", "tbody", "td", "textarea", "tfoot", "th",
        "thead", "title", "tr", "tt", "ul", "var", "extends"];


    this.inline_tags = ["br", "hr", "img", "input"];

    return this;
};

WYMeditor.XhtmlSaxListener.prototype.shouldCloseTagAutomatically = function(tag, now_on_tag, closing) {
    closing = closing || false;
    if (tag == 'td') {
        if ((closing && now_on_tag == 'tr') || (!closing && now_on_tag == 'td')) {
            return true;
        }
    } else if (tag == 'option') {
        if ((closing && now_on_tag == 'select') || (!closing && now_on_tag == 'option')) {
            return true;
        }
    }
    return false;
};

WYMeditor.XhtmlSaxListener.prototype.beforeParsing = function(raw) {
    this.output = '';
    return raw;
};

WYMeditor.XhtmlSaxListener.prototype.afterParsing = function(xhtml) {
    xhtml = this.replaceNamedEntities(xhtml);
    xhtml = this.joinRepeatedEntities(xhtml);
    xhtml = this.removeEmptyTags(xhtml);
    xhtml = this.removeBrInPre(xhtml);
    return xhtml;
};

WYMeditor.XhtmlSaxListener.prototype.replaceNamedEntities = function(xhtml) {
    for (var entity in this.entities) {
        xhtml = xhtml.replace(new RegExp(entity, 'g'), this.entities[entity]);
    }
    return xhtml;
};

WYMeditor.XhtmlSaxListener.prototype.joinRepeatedEntities = function(xhtml) {
    var tags = 'em|strong|sub|sup|acronym|pre|del|address';
    return xhtml.replace(new RegExp('<\/('+tags+')><\\1>' ,''), '').
            replace(
                new RegExp('(\s*<('+tags+')>\s*){2}(.*)(\s*<\/\\2>\s*){2}' ,''),
                '<\$2>\$3<\$2>');
};

WYMeditor.XhtmlSaxListener.prototype.removeEmptyTags = function(xhtml) {
    return xhtml.replace(
            new RegExp(
                '<('+this.block_tags.join("|").
                    replace(/\|td/,'').
                    replace(/\|th/, '') +
                ')>(<br \/>|&#160;|&nbsp;|\\s)*<\/\\1>' ,'g'),
            '');
};

WYMeditor.XhtmlSaxListener.prototype.removeBrInPre = function(xhtml) {
    var matches = xhtml.match(new RegExp('<pre[^>]*>(.*?)<\/pre>','gmi'));
    if (matches) {
        for (var i=0; i<matches.length; i++) {
            xhtml = xhtml.replace(
                matches[i],
                matches[i].replace(new RegExp('<br \/>', 'g'), String.fromCharCode(13,10)));
        }
    }
    return xhtml;
};

WYMeditor.XhtmlSaxListener.prototype.getResult = function() {
    return this.output;
};

WYMeditor.XhtmlSaxListener.prototype.getTagReplacements = function() {
    return {'b':'strong', 'i':'em'};
};

WYMeditor.XhtmlSaxListener.prototype.addContent = function(text) {
    if (this.last_tag && this.last_tag == 'li') {
        // We should strip trailing newlines from text inside li tags because
        // IE adds random significant newlines inside nested lists
        text = text.replace(/\n/, '');
        text = text.replace(/\r/, '');
    }
    this.output += text;
};

WYMeditor.XhtmlSaxListener.prototype.addComment = function(text) {
    if (this.remove_comments) {
        this.output += text;
    }
};

WYMeditor.XhtmlSaxListener.prototype.addScript = function(text) {
    if (!this.remove_scripts) {
        this.output += text;
    }
};

WYMeditor.XhtmlSaxListener.prototype.addCss = function(text) {
    if (!this.remove_embeded_styles) {
        this.output += text;
    }
};

WYMeditor.XhtmlSaxListener.prototype.openBlockTag = function(tag, attributes) {
    this.output += this.helper.tag(
        tag,
        this.validator.getValidTagAttributes(tag, attributes),
        true);
};

WYMeditor.XhtmlSaxListener.prototype.inlineTag = function(tag, attributes) {
    this.output += this.helper.tag(
        tag,
        this.validator.getValidTagAttributes(tag, attributes));
};

WYMeditor.XhtmlSaxListener.prototype.openUnknownTag = function(tag, attributes) {
    //this.output += this.helper.tag(tag, attributes, true);
};

WYMeditor.XhtmlSaxListener.prototype.closeBlockTag = function(tag) {
    this.output = this.output.replace(/<br \/>$/, '') +
        this._getClosingTagContent('before', tag) +
        "</"+tag+">" +
        this._getClosingTagContent('after', tag);
};

WYMeditor.XhtmlSaxListener.prototype.closeUnknownTag = function(tag) {
    //this.output += "</"+tag+">";
};

WYMeditor.XhtmlSaxListener.prototype.closeUnopenedTag = function(tag) {
    this.output += "</" + tag + ">";
};

WYMeditor.XhtmlSaxListener.prototype.avoidStylingTagsAndAttributes = function() {
    this.avoided_tags = ['div','span'];
    this.validator.skiped_attributes = ['style'];
    this.validator.skiped_attribute_values = ['MsoNormal','main1']; // MS Word attributes for class
    this._avoiding_tags_implicitly = true;
};

WYMeditor.XhtmlSaxListener.prototype.allowStylingTagsAndAttributes = function() {
    this.avoided_tags = [];
    this.validator.skiped_attributes = [];
    this.validator.skiped_attribute_values = [];
    this._avoiding_tags_implicitly = false;
};

WYMeditor.XhtmlSaxListener.prototype.isBlockTag = function(tag) {
    return !WYMeditor.Helper.contains(this.avoided_tags, tag) &&
            WYMeditor.Helper.contains(this.block_tags, tag);
};

WYMeditor.XhtmlSaxListener.prototype.isInlineTag = function(tag) {
    return !WYMeditor.Helper.contains(this.avoided_tags, tag) &&
            WYMeditor.Helper.contains(this.inline_tags, tag);
};

WYMeditor.XhtmlSaxListener.prototype.insertContentAfterClosingTag = function(tag, content) {
    this._insertContentWhenClosingTag('after', tag, content);
};

WYMeditor.XhtmlSaxListener.prototype.insertContentBeforeClosingTag = function(tag, content) {
    this._insertContentWhenClosingTag('before', tag, content);
};

WYMeditor.XhtmlSaxListener.prototype.fixNestingBeforeOpeningBlockTag = function(tag, attributes) {
    if ((tag == 'ul' || tag == 'ol') && this.last_tag &&
            !this.last_tag_opened && this.last_tag == 'li') {
        // We have a <li></li><ol>... situation. The new list should be a
        // child of the li tag. Not a sibling.

        this.output = this.output.replace(/<\/li>\s*$/, '');
        this.insertContentAfterClosingTag(tag, '</li>');
    } else if ((tag == 'ul' || tag == 'ol') && this.last_tag &&
            this.last_tag_opened && (this.last_tag == 'ul' || this.last_tag == 'ol')) {
        // We have a <ol|ul><ol|ul>... situation. The new list should be have
        // a li tag parent and shouldn't be directly nested.

        // Add an opening li tag before and after this tag
        this.output += this.helper.tag('li', {}, true);
        this.insertContentAfterClosingTag(tag, '</li>');
    } else if (tag == 'li' && !this.last_tag_opened) {
        // Closest open tag that's not this tag
        if (this._tag_stack.length >= 2) {
            var closestOpenTag = this._tag_stack[this._tag_stack.length - 2];
            if (closestOpenTag == 'li'){
                // Pop the tag off of the stack to indicate we closed it
                this._open_tags['li']--;
                if (this._open_tags['li'] === 0) {
                    this._open_tags['li'] = undefined;
                }
                this._tag_stack.pop(this._tag_stack.length - 2);
                this.output += '</li>';
            }
        }
        // Opening a new li tag while another li tag is still open.
        // LI tags aren't allowed to be nested within eachother
        // It probably means we forgot to close the last LI tag
        //return true;
    }
};

WYMeditor.XhtmlSaxListener.prototype._insertContentWhenClosingTag = function(position, tag, content) {
    if (!this['_insert_'+position+'_closing']) {
        this['_insert_'+position+'_closing'] = [];
    }
    if (!this['_insert_'+position+'_closing'][tag]) {
        this['_insert_'+position+'_closing'][tag] = [];
    }
    this['_insert_'+position+'_closing'][tag].push(content);
};

WYMeditor.XhtmlSaxListener.prototype._getClosingTagContent = function(position, tag) {
    if (this['_insert_'+position+'_closing'] &&
            this['_insert_'+position+'_closing'][tag] &&
            this['_insert_'+position+'_closing'][tag].length > 0) {
        return this['_insert_'+position+'_closing'][tag].pop();
    }
    return '';
};

WYMeditor.WymCssLexer = function(parser, only_wym_blocks)
{
    only_wym_blocks = (typeof only_wym_blocks == 'undefined' ? true : only_wym_blocks);

    jQuery.extend(this, new WYMeditor.Lexer(parser, (only_wym_blocks?'Ignore':'WymCss')));

    this.mapHandler('WymCss', 'Ignore');

    if(only_wym_blocks === true){
        this.addEntryPattern("/\\\x2a[<\\s]*WYMeditor[>\\s]*\\\x2a/", 'Ignore', 'WymCss');
        this.addExitPattern("/\\\x2a[<\/\\s]*WYMeditor[>\\s]*\\\x2a/", 'WymCss');
    }

    this.addSpecialPattern("[\\sa-z1-6]*\\\x2e[a-z-_0-9]+", 'WymCss', 'WymCssStyleDeclaration');

    this.addEntryPattern("/\\\x2a", 'WymCss', 'WymCssComment');
    this.addExitPattern("\\\x2a/", 'WymCssComment');

    this.addEntryPattern("\x7b", 'WymCss', 'WymCssStyle');
    this.addExitPattern("\x7d", 'WymCssStyle');

    this.addEntryPattern("/\\\x2a", 'WymCssStyle', 'WymCssFeedbackStyle');
    this.addExitPattern("\\\x2a/", 'WymCssFeedbackStyle');

    return this;
};

WYMeditor.WymCssParser = function()
{
    this._in_style = false;
    this._has_title = false;
    this.only_wym_blocks = true;
    this.css_settings = {'classesItems':[], 'editorStyles':[], 'dialogStyles':[]};
    return this;
};

WYMeditor.WymCssParser.prototype.parse = function(raw, only_wym_blocks)
{
    only_wym_blocks = (typeof only_wym_blocks == 'undefined' ? this.only_wym_blocks : only_wym_blocks);
    this._Lexer = new WYMeditor.WymCssLexer(this, only_wym_blocks);
    this._Lexer.parse(raw);
};

WYMeditor.WymCssParser.prototype.Ignore = function(match, state)
{
    return true;
};

WYMeditor.WymCssParser.prototype.WymCssComment = function(text, status)
{
    if(text.match(/end[a-z0-9\s]*wym[a-z0-9\s]*/mi)){
        return false;
    }
    if(status == WYMeditor.LEXER_UNMATCHED){
        if(!this._in_style){
            this._has_title = true;
            this._current_item = {'title':WYMeditor.Helper.trim(text)};
        }else{
            if(this._current_item[this._current_element]){
                if(!this._current_item[this._current_element].expressions){
                    this._current_item[this._current_element].expressions = [text];
                }else{
                    this._current_item[this._current_element].expressions.push(text);
                }
            }
        }
        this._in_style = true;
    }
    return true;
};

WYMeditor.WymCssParser.prototype.WymCssStyle = function(match, status)
{
    if(status == WYMeditor.LEXER_UNMATCHED){
        match = WYMeditor.Helper.trim(match);
        if(match !== ''){
            this._current_item[this._current_element].style = match;
        }
    }else if (status == WYMeditor.LEXER_EXIT){
        this._in_style = false;
        this._has_title = false;
        this.addStyleSetting(this._current_item);
    }
    return true;
};

WYMeditor.WymCssParser.prototype.WymCssFeedbackStyle = function(match, status)
{
    if(status == WYMeditor.LEXER_UNMATCHED){
        this._current_item[this._current_element].feedback_style = match.replace(/^([\s\/\*]*)|([\s\/\*]*)$/gm,'');
    }
    return true;
};

WYMeditor.WymCssParser.prototype.WymCssStyleDeclaration = function(match)
{
    match = match.replace(/^([\s\.]*)|([\s\.*]*)$/gm, '');

    var tag = '';
    if(match.indexOf('.') > 0){
        var parts = match.split('.');
        this._current_element = parts[1];
        tag = parts[0];
    }else{
        this._current_element = match;
    }

    if(!this._has_title){
        this._current_item = {'title':(!tag?'':tag.toUpperCase()+': ')+this._current_element};
        this._has_title = true;
    }

    if(!this._current_item[this._current_element]){
        this._current_item[this._current_element] = {'name':this._current_element};
    }
    if(tag){
        if(!this._current_item[this._current_element].tags){
            this._current_item[this._current_element].tags = [tag];
        }else{
            this._current_item[this._current_element].tags.push(tag);
        }
    }
    return true;
};

WYMeditor.WymCssParser.prototype.addStyleSetting = function(style_details)
{
    for (var name in style_details){
        var details = style_details[name];
        if(typeof details == 'object' && name != 'title'){

    this.css_settings.classesItems.push({
        'name': WYMeditor.Helper.trim(details.name),
        'title': style_details.title,
        'expr' : WYMeditor.Helper.trim((details.expressions||details.tags).join(', '))
    });
    if(details.feedback_style){
        this.css_settings.editorStyles.push({
            'name': '.'+ WYMeditor.Helper.trim(details.name),
            'css': details.feedback_style
        });
    }
    if(details.style){
        this.css_settings.dialogStyles.push({
            'name': '.'+ WYMeditor.Helper.trim(details.name),
            'css': details.style
        });
    }
}
}
};



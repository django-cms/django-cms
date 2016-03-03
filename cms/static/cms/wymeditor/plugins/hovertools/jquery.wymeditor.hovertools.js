/*jslint evil: true */
/**
    WYMeditor.hovertools
    ====================

    A hovertools plugin.
*/

WYMeditor.editor.prototype.hovertools = function() {
    var wym = this;

    wym.status('&nbsp;');

    // Bind events on buttons
    jQuery(this._box).find(this._options.toolSelector).hover(
        function() {
            wym.status(jQuery(this).html());
        },
        function() {
            wym.status('&nbsp;');
        }
    );

    // Classes: add/remove a style attr to matching elems
    // while mouseover/mouseout
    jQuery(this._box).find(this._options.classSelector).hover(
        function() {
            var aClasses = eval(wym._options.classesItems);
            var sName = jQuery(this).attr(WYMeditor.NAME);
            var oClass = WYMeditor.Helper.findByName(aClasses, sName);

            if (oClass){
                jqexpr = oClass.expr;
                // Don't use jQuery.find() on the iframe body
                // because of MSIE + jQuery + expando issue (#JQ1143)
                if (!jQuery.browser.msie) {
                    jQuery(wym._doc).find(jqexpr).css('background-color','#cfc');
                }
            }
        },
        function() {
            // Don't use jQuery.find() on the iframe body
            // because of MSIE + jQuery + expando issue (#JQ1143)
            if (!jQuery.browser.msie) {
                jQuery(wym._doc).find('*').removeAttr('style');
            }
        }
    );
};

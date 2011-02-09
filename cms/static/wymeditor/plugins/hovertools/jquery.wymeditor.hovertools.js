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
 *        jquery.wymeditor.hovertools.js
 *        hovertools plugin for WYMeditor
 *
 * File Authors:
 *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
 */

//Extend WYMeditor
WYMeditor.editor.prototype.hovertools = function() {
  
  var wym = this;
  
  //bind events on buttons
  jQuery(this._box).find(this._options.toolSelector).hover(
    function() {
      wym.status(jQuery(this).html());
    },
    function() {
      wym.status('&nbsp;');
    }
  );

  //classes: add/remove a style attr to matching elems
  //while mouseover/mouseout
  jQuery(this._box).find(this._options.classSelector).hover(
    function() {
      var aClasses = eval(wym._options.classesItems);
      var sName = jQuery(this).attr(WYMeditor.NAME);
      var oClass = WYMeditor.Helper.findByName(aClasses, sName);

      if(oClass){
        jqexpr = oClass.expr;
        //don't use jQuery.find() on the iframe body
        //because of MSIE + jQuery + expando issue (#JQ1143)
        if(!jQuery.browser.msie)
          jQuery(wym._doc).find(jqexpr).css('background-color','#cfc');
      }
    },
    function() {
      //don't use jQuery.find() on the iframe body
      //because of MSIE + jQuery + expando issue (#JQ1143)
      if(!jQuery.browser.msie)
        jQuery(wym._doc).find('*').removeAttr('style');
    }
  );

};

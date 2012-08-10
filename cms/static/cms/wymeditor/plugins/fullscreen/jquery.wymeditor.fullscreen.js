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
 *        jquery.wymeditor.fullscreen.js
 *        Fullscreen plugin for WYMeditor
 *
 * File Authors:
 *        Luis Santos (luis.santos a-t openquest dotpt)
 */

//Extend WYMeditor
WYMeditor.editor.prototype.fullscreen = function() {
  var wym = this;

 //construct the button's html
  var html = "<li class='wym_tools_fullscreen'>"
         + "<a name='Fullscreen' href='#'"
         + " style='background-image:"
         + " url(" + wym._options.basePath +"plugins/fullscreen/icon_fullscreen.gif)'>"
         + "Fullscreen"
         + "</a></li>";

  //add the button to the tools box
  jQuery(wym._box)
    .find(wym._options.toolsSelector + wym._options.toolsListSelector)
    .append(html);

  //handle click event
  jQuery(wym._box).find('li.wym_tools_fullscreen a').click(function() {
    if (jQuery(wym._box).css('position') != 'fixed') {
      jQuery('body').append('<div id="loader"></div>');
      jQuery('#loader').css({'position' : 'fixed', 'background-color': 'rgb(0, 0, 0)', 'opacity': '0.8', 'z-index': '98', 'width': '100%', 'height': '100%', 'top': '0px', 'left': '0px'});
      jQuery(wym._box).css({'position' : 'fixed', 'z-index' : '99', 'top': '5%', 'left': '5%', 'width': '90%', 'height': '90%'});
    } else {
      jQuery('#loader').remove();
      jQuery(wym._box).css({'position' : 'static', 'z-index' : '99', 'height' : '100%', 'width' : '100%', 'top': '0px', 'left': '0px'});
    }

    return(false);
  });
};

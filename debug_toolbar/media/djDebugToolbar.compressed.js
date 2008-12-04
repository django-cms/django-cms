
jQuery(function()
{jQuery.noConflict();var $body=jQuery('body');var $djDebug=jQuery('#djDebug');var $djDebugOpenToolbarButton=jQuery('#djDebugToggleToolbar');var $djDebugCloseToolbarButton=jQuery('#djDebug #djDebugCloseToolbar');var $djDebugButtons=jQuery('#djDebug .djDebugButton:not(.disabled)');var $djDebugDecorations=jQuery('#decoration');var $document=jQuery(document);var $djDebugDebugBarHeight=29;function djDebugCreateCookie(name,value)
{document.cookie=name+'='+value+'; path=/';}
function djDebugReadCookie(name){var nameEQ=name+'=';var ca=document.cookie.split(';');for(var i=0,l=ca.length;i<l;i++){var c=ca[i];while(c.charAt(0)===' ')
{c=c.substring(1,c.length);}
if(c.indexOf(nameEQ)===0)
{return c.substring(nameEQ.length,c.length);}}
return null;}
function djDebugHandleToolbar(action)
{var marginTop=$body.css('margin-top');marginTop=marginTop.substr(0,marginTop.indexOf('px'));marginTop=parseInt(marginTop,10);if(action==='open')
{marginTop=marginTop+$djDebugDebugBarHeight;$djDebug.removeClass('hide');djDebugCreateCookie('djDebugShow','true');}
else
{marginTop=marginTop-$djDebugDebugBarHeight;$djDebug.addClass('hide');djDebugCreateCookie('djDebugShow','false');}
$body.css('margin-top',marginTop);}
function djDebugHidePanel()
{$djDebugDecorations.hide();jQuery('#djDebug .panelContent').hide();jQuery('#djDebug .djDebugButton.current').removeClass('current');}
function djDebugShowPanel(obj)
{$djDebugDecorations.show();jQuery('.tabSet li:not(.filterContainer,.close)',obj).click(function(event)
{var $this=jQuery(this);var current=jQuery('li.current',$this.parent());current.removeClass('current');jQuery('#'+current.attr('rel')).hide();$this.addClass('current');jQuery('#'+$this.attr('rel')).show();}).append('<div class="decoration" id="leftDecoration" /><div class="decoration" id="rightDecoration" />');jQuery('.tabSet li.close',obj).click(function(event)
{djDebugHidePanel();});jQuery('#djDebug table.data.sortable thead tr').one('click',function()
{jQuery('table.data.sortable:not(.sorted)',obj).addClass('sorted').tablesorter({widgets:['zebra']});jQuery('th',this).addClass('headerSort').one('mousedown',function()
{jQuery(this).parent().find('th').removeClass('headerSort');});});jQuery('a.infoIcon',obj).each(function(index)
{jQuery(this).click(function(event)
{eval(jQuery(this).attr('href'));return false;});});var widthArray=[];jQuery('table',obj).each(function(index)
{jQuery('colgroup col',this).each(function(index)
{widthArray[widthArray.length]=jQuery(this).css('width');});if(widthArray.length!==0)
{jQuery('thead th',this).each(function(index)
{jQuery(this).css('width',widthArray[index]);});}
widthArray=[];});obj.show();}
function djDebugWindow(panel,params,locals)	
{params.djDebug=panel;jQuery('html, body').animate({scrollTop:0});jQuery.ajax({type:'GET',url:djDebugBaseUrl,data:params,success:function(html)
{jQuery('#djDebug .panelContent').hide();var obj=jQuery('#djDebugTempPanelContent');document.getElementById('djDebugTempPanelContent').innerHTML=html;var el;var els=jQuery('script',obj);for(var i=0;(el=els[i]);i++){eval(jQuery(el).html());jQuery(el).remove();}
djDebugShowPanel(jQuery('#djDebugTempPanel'));jQuery('.back',obj).click(function(event)
{jQuery('#djDebugTempPanel').hide();jQuery('#'+jQuery('#djDebug .djDebugButton.current').attr('rel')).show();});}});}
function djDebugInitiateFiltering()
{jQuery.extend(jQuery.expr[':'],{icontains:"(a.textContent||a.innerText||jQuery(a).text()||'').toLowerCase().indexOf((m[3]||'').toLowerCase())>=0"});jQuery.fn.djDebugFilter=function()
{return this.each(function(){jQuery(this).each(function()
{jQuery(this).one('focus',function()
{jQuery(this).val('');}).keyup(function()
{var filterParent=jQuery(this).parents('.panelContent');var values=jQuery(this).val().split(' ');var rows=jQuery('table.data tbody tr',filterParent);var pos=[];var posIndex=0;var neg=[];var negIndex=0;rows.hide();jQuery('.error-message',filterParent).remove();for(var i=0,l=values.length;i<l;i++)
{var firstChar=values[i].substr(0,1);if(firstChar==='-'&&values[i].length>1)
{neg[posIndex]=values[i].substr(1);negIndex++;}
else if(firstChar!=='-')
{pos[posIndex]=values[i];posIndex++;}}
for(i=0,l=pos.length;i<l;i++)
{rows=rows.filter(':icontains('+pos[i]+')');}
for(i=0,l=neg.length;i<l;i++)
{rows=rows.filter(':not(:icontains('+neg[i]+'))');}
if(rows.length===0)
{jQuery('table.data tbody',filterParent).append('<tr class="error-message"><td colspan="100"><strong>Could not find any matching entries</strong></td></tr>');}
else
{rows.removeClass('even odd').show().filter(':odd').addClass('odd');}}).after('<div class="djDebugFilterReset"></div>').next().click(function(event)
{jQuery(this).prev().val('').keyup();});});});};jQuery('#djDebug input.filter').djDebugFilter();}
if(djDebugReadCookie('djDebugShow')!=='false')
{djDebugHandleToolbar('open');}
jQuery('li.name').append('<div class="overlay"/>');$djDebugCloseToolbarButton.click(function(event)
{djDebugHandleToolbar('close');});$djDebugOpenToolbarButton.click(function(event)
{djDebugHandleToolbar('open');});$djDebugButtons.each(function()
{jQuery(this).click(function(event)
{var $this=jQuery(this);if($this.hasClass('current'))
{djDebugHidePanel();}
else
{djDebugHidePanel();$this.addClass('current');djDebugShowPanel(jQuery('#'+$this.attr('rel')));}
return false;});});jQuery('#djDebugFireBug').click(function(event)
{jQuery.getScript('http://getfirebug.com/releases/lite/1.2/firebug-lite-compressed.js',function()
{firebug.init();});});$document.keydown(function(e)
{if(e.keyCode===27)
{if(!$djDebug.hasClass('hide'))
{$djDebugCloseToolbarButton.click();}
return false;}
if(e.metaKey===true)
{switch(e.keyCode)
{case 37:jQuery('.current').prevAll('.djDebugButton:not(.disabled):first').click();return false;case 39:jQuery('.current').nextAll('.djDebugButton:not(.disabled):first').click();return false;case 38:djDebugHidePanel();return false;case 40:if(jQuery('li.current').length!==2)
{$djDebugButtons.filter(':first').click();}
return false;case 83:if($djDebug.hasClass('hide'))
{$djDebugOpenToolbarButton.click();}
else
{$djDebugCloseToolbarButton.click();}
return false;default:}}});djDebugInitiateFiltering();});
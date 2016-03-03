
/* * ====================================================================
 * About: This a a compressed JS file from the Sarissa library. 
 * see http://dev.abiss.gr/sarissa
 * 
 * Copyright: Manos Batsis, http://dev.abiss.gr
 * 
 * Licence:
 * Sarissa is free software distributed under the GNU GPL version 2 
 * or higher, GNU LGPL version 2.1 or higher and Apache Software 
 * License 2.0 or higher. The licenses are available online see: 
 * http://www.gnu.org  
 * http://www.apache.org
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY 
 * KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
 * WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE 
 * AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 * ====================================================================*/

function Sarissa(){}
Sarissa.VERSION="0.9.9.4";Sarissa.PARSED_OK="Document contains no parsing errors";Sarissa.PARSED_EMPTY="Document is empty";Sarissa.PARSED_UNKNOWN_ERROR="Not well-formed or other error";Sarissa.IS_ENABLED_TRANSFORM_NODE=false;Sarissa.REMOTE_CALL_FLAG="gr.abiss.sarissa.REMOTE_CALL_FLAG";Sarissa._lastUniqueSuffix=0;Sarissa._getUniqueSuffix=function(){return Sarissa._lastUniqueSuffix++;};Sarissa._SARISSA_IEPREFIX4XSLPARAM="";Sarissa._SARISSA_HAS_DOM_IMPLEMENTATION=document.implementation&&true;Sarissa._SARISSA_HAS_DOM_CREATE_DOCUMENT=Sarissa._SARISSA_HAS_DOM_IMPLEMENTATION&&document.implementation.createDocument;Sarissa._SARISSA_HAS_DOM_FEATURE=Sarissa._SARISSA_HAS_DOM_IMPLEMENTATION&&document.implementation.hasFeature;Sarissa._SARISSA_IS_MOZ=Sarissa._SARISSA_HAS_DOM_CREATE_DOCUMENT&&Sarissa._SARISSA_HAS_DOM_FEATURE;Sarissa._SARISSA_IS_SAFARI=navigator.userAgent.toLowerCase().indexOf("safari")!=-1||navigator.userAgent.toLowerCase().indexOf("konqueror")!=-1;Sarissa._SARISSA_IS_SAFARI_OLD=Sarissa._SARISSA_IS_SAFARI&&(parseInt((navigator.userAgent.match(/AppleWebKit\/(\d+)/)||{})[1],10)<420);Sarissa._SARISSA_IS_IE=document.all&&window.ActiveXObject&&navigator.userAgent.toLowerCase().indexOf("msie")>-1&&navigator.userAgent.toLowerCase().indexOf("opera")==-1;Sarissa._SARISSA_IS_OPERA=navigator.userAgent.toLowerCase().indexOf("opera")!=-1;if(!window.Node||!Node.ELEMENT_NODE){Node={ELEMENT_NODE:1,ATTRIBUTE_NODE:2,TEXT_NODE:3,CDATA_SECTION_NODE:4,ENTITY_REFERENCE_NODE:5,ENTITY_NODE:6,PROCESSING_INSTRUCTION_NODE:7,COMMENT_NODE:8,DOCUMENT_NODE:9,DOCUMENT_TYPE_NODE:10,DOCUMENT_FRAGMENT_NODE:11,NOTATION_NODE:12};}
if(Sarissa._SARISSA_IS_SAFARI_OLD){HTMLHtmlElement=document.createElement("html").constructor;Node=HTMLElement={};HTMLElement.prototype=HTMLHtmlElement.__proto__.__proto__;HTMLDocument=Document=document.constructor;var x=new DOMParser();XMLDocument=x.constructor;Element=x.parseFromString("<Single />","text/xml").documentElement.constructor;x=null;}
if(typeof XMLDocument=="undefined"&&typeof Document!="undefined"){XMLDocument=Document;}
if(Sarissa._SARISSA_IS_IE){Sarissa._SARISSA_IEPREFIX4XSLPARAM="xsl:";var _SARISSA_DOM_PROGID="";var _SARISSA_XMLHTTP_PROGID="";var _SARISSA_DOM_XMLWRITER="";Sarissa.pickRecentProgID=function(idList){var bFound=false,e;var o2Store;for(var i=0;i<idList.length&&!bFound;i++){try{var oDoc=new ActiveXObject(idList[i]);o2Store=idList[i];bFound=true;}catch(objException){e=objException;}}
if(!bFound){throw"Could not retrieve a valid progID of Class: "+idList[idList.length-1]+". (original exception: "+e+")";}
idList=null;return o2Store;};_SARISSA_DOM_PROGID=null;_SARISSA_THREADEDDOM_PROGID=null;_SARISSA_XSLTEMPLATE_PROGID=null;_SARISSA_XMLHTTP_PROGID=null;XMLHttpRequest=function(){if(!_SARISSA_XMLHTTP_PROGID){_SARISSA_XMLHTTP_PROGID=Sarissa.pickRecentProgID(["Msxml2.XMLHTTP.6.0","MSXML2.XMLHTTP.3.0","MSXML2.XMLHTTP","Microsoft.XMLHTTP"]);}
return new ActiveXObject(_SARISSA_XMLHTTP_PROGID);};Sarissa.getDomDocument=function(sUri,sName){if(!_SARISSA_DOM_PROGID){_SARISSA_DOM_PROGID=Sarissa.pickRecentProgID(["Msxml2.DOMDocument.6.0","Msxml2.DOMDocument.3.0","MSXML2.DOMDocument","MSXML.DOMDocument","Microsoft.XMLDOM"]);}
var oDoc=new ActiveXObject(_SARISSA_DOM_PROGID);if(sName){var prefix="";if(sUri){if(sName.indexOf(":")>1){prefix=sName.substring(0,sName.indexOf(":"));sName=sName.substring(sName.indexOf(":")+1);}else{prefix="a"+Sarissa._getUniqueSuffix();}}
if(sUri){oDoc.loadXML('<'+prefix+':'+sName+" xmlns:"+prefix+"=\""+sUri+"\""+" />");}else{oDoc.loadXML('<'+sName+" />");}}
return oDoc;};Sarissa.getParseErrorText=function(oDoc){var parseErrorText=Sarissa.PARSED_OK;if(oDoc&&oDoc.parseError&&oDoc.parseError.errorCode&&oDoc.parseError.errorCode!=0){parseErrorText="XML Parsing Error: "+oDoc.parseError.reason+"\nLocation: "+oDoc.parseError.url+"\nLine Number "+oDoc.parseError.line+", Column "+
oDoc.parseError.linepos+":\n"+oDoc.parseError.srcText+"\n";for(var i=0;i<oDoc.parseError.linepos;i++){parseErrorText+="-";}
parseErrorText+="^\n";}
else if(oDoc.documentElement===null){parseErrorText=Sarissa.PARSED_EMPTY;}
return parseErrorText;};Sarissa.setXpathNamespaces=function(oDoc,sNsSet){oDoc.setProperty("SelectionLanguage","XPath");oDoc.setProperty("SelectionNamespaces",sNsSet);};XSLTProcessor=function(){if(!_SARISSA_XSLTEMPLATE_PROGID){_SARISSA_XSLTEMPLATE_PROGID=Sarissa.pickRecentProgID(["Msxml2.XSLTemplate.6.0","MSXML2.XSLTemplate.3.0"]);}
this.template=new ActiveXObject(_SARISSA_XSLTEMPLATE_PROGID);this.processor=null;};XSLTProcessor.prototype.importStylesheet=function(xslDoc){if(!_SARISSA_THREADEDDOM_PROGID){_SARISSA_THREADEDDOM_PROGID=Sarissa.pickRecentProgID(["MSXML2.FreeThreadedDOMDocument.6.0","MSXML2.FreeThreadedDOMDocument.3.0"]);}
xslDoc.setProperty("SelectionLanguage","XPath");xslDoc.setProperty("SelectionNamespaces","xmlns:xsl='http://www.w3.org/1999/XSL/Transform'");var converted=new ActiveXObject(_SARISSA_THREADEDDOM_PROGID);try{converted.resolveExternals=true;converted.setProperty("AllowDocumentFunction",true);}
catch(e){}
if(xslDoc.url&&xslDoc.selectSingleNode("//xsl:*[local-name() = 'import' or local-name() = 'include']")!=null){converted.async=false;converted.load(xslDoc.url);}
else{converted.loadXML(xslDoc.xml);}
converted.setProperty("SelectionNamespaces","xmlns:xsl='http://www.w3.org/1999/XSL/Transform'");var output=converted.selectSingleNode("//xsl:output");if(output){this.outputMethod=output.getAttribute("method");}
else{delete this.outputMethod;}
this.template.stylesheet=converted;this.processor=this.template.createProcessor();this.paramsSet=[];};XSLTProcessor.prototype.transformToDocument=function(sourceDoc){var outDoc;if(_SARISSA_THREADEDDOM_PROGID){this.processor.input=sourceDoc;outDoc=new ActiveXObject(_SARISSA_DOM_PROGID);this.processor.output=outDoc;this.processor.transform();return outDoc;}
else{if(!_SARISSA_DOM_XMLWRITER){_SARISSA_DOM_XMLWRITER=Sarissa.pickRecentProgID(["Msxml2.MXXMLWriter.6.0","Msxml2.MXXMLWriter.3.0","MSXML2.MXXMLWriter","MSXML.MXXMLWriter","Microsoft.XMLDOM"]);}
this.processor.input=sourceDoc;outDoc=new ActiveXObject(_SARISSA_DOM_XMLWRITER);this.processor.output=outDoc;this.processor.transform();var oDoc=new ActiveXObject(_SARISSA_DOM_PROGID);oDoc.loadXML(outDoc.output+"");return oDoc;}};XSLTProcessor.prototype.transformToFragment=function(sourceDoc,ownerDoc){this.processor.input=sourceDoc;this.processor.transform();var s=this.processor.output;var f=ownerDoc.createDocumentFragment();var container;if(this.outputMethod=='text'){f.appendChild(ownerDoc.createTextNode(s));}else if(ownerDoc.body&&ownerDoc.body.innerHTML){container=ownerDoc.createElement('div');container.innerHTML=s;while(container.hasChildNodes()){f.appendChild(container.firstChild);}}
else{var oDoc=new ActiveXObject(_SARISSA_DOM_PROGID);if(s.substring(0,5)=='<?xml'){s=s.substring(s.indexOf('?>')+2);}
var xml=''.concat('<my>',s,'</my>');oDoc.loadXML(xml);container=oDoc.documentElement;while(container.hasChildNodes()){f.appendChild(container.firstChild);}}
return f;};XSLTProcessor.prototype.setParameter=function(nsURI,name,value){value=value?value:"";if(nsURI){this.processor.addParameter(name,value,nsURI);}else{this.processor.addParameter(name,value);}
nsURI=""+(nsURI||"");if(!this.paramsSet[nsURI]){this.paramsSet[nsURI]=[];}
this.paramsSet[nsURI][name]=value;};XSLTProcessor.prototype.getParameter=function(nsURI,name){nsURI=""+(nsURI||"");if(this.paramsSet[nsURI]&&this.paramsSet[nsURI][name]){return this.paramsSet[nsURI][name];}else{return null;}};XSLTProcessor.prototype.clearParameters=function(){for(var nsURI in this.paramsSet){for(var name in this.paramsSet[nsURI]){if(nsURI!=""){this.processor.addParameter(name,"",nsURI);}else{this.processor.addParameter(name,"");}}}
this.paramsSet=[];};}else{if(Sarissa._SARISSA_HAS_DOM_CREATE_DOCUMENT){Sarissa.__handleLoad__=function(oDoc){Sarissa.__setReadyState__(oDoc,4);};_sarissa_XMLDocument_onload=function(){Sarissa.__handleLoad__(this);};Sarissa.__setReadyState__=function(oDoc,iReadyState){oDoc.readyState=iReadyState;oDoc.readystate=iReadyState;if(oDoc.onreadystatechange!=null&&typeof oDoc.onreadystatechange=="function"){oDoc.onreadystatechange();}};Sarissa.getDomDocument=function(sUri,sName){var oDoc=document.implementation.createDocument(sUri?sUri:null,sName?sName:null,null);if(!oDoc.onreadystatechange){oDoc.onreadystatechange=null;}
if(!oDoc.readyState){oDoc.readyState=0;}
oDoc.addEventListener("load",_sarissa_XMLDocument_onload,false);return oDoc;};if(window.XMLDocument){}
else if(Sarissa._SARISSA_HAS_DOM_FEATURE&&window.Document&&!Document.prototype.load&&document.implementation.hasFeature('LS','3.0')){Sarissa.getDomDocument=function(sUri,sName){var oDoc=document.implementation.createDocument(sUri?sUri:null,sName?sName:null,null);return oDoc;};}
else{Sarissa.getDomDocument=function(sUri,sName){var oDoc=document.implementation.createDocument(sUri?sUri:null,sName?sName:null,null);if(oDoc&&(sUri||sName)&&!oDoc.documentElement){oDoc.appendChild(oDoc.createElementNS(sUri,sName));}
return oDoc;};}}}
if(!window.DOMParser){if(Sarissa._SARISSA_IS_SAFARI){DOMParser=function(){};DOMParser.prototype.parseFromString=function(sXml,contentType){var xmlhttp=new XMLHttpRequest();xmlhttp.open("GET","data:text/xml;charset=utf-8,"+encodeURIComponent(sXml),false);xmlhttp.send(null);return xmlhttp.responseXML;};}else if(Sarissa.getDomDocument&&Sarissa.getDomDocument()&&Sarissa.getDomDocument(null,"bar").xml){DOMParser=function(){};DOMParser.prototype.parseFromString=function(sXml,contentType){var doc=Sarissa.getDomDocument();doc.loadXML(sXml);return doc;};}}
if((typeof(document.importNode)=="undefined")&&Sarissa._SARISSA_IS_IE){try{document.importNode=function(oNode,bChildren){var tmp;if(oNode.nodeName=='#text'){return document.createTextNode(oNode.data);}
else{if(oNode.nodeName=="tbody"||oNode.nodeName=="tr"){tmp=document.createElement("table");}
else if(oNode.nodeName=="td"){tmp=document.createElement("tr");}
else if(oNode.nodeName=="option"){tmp=document.createElement("select");}
else{tmp=document.createElement("div");}
if(bChildren){tmp.innerHTML=oNode.xml?oNode.xml:oNode.outerHTML;}else{tmp.innerHTML=oNode.xml?oNode.cloneNode(false).xml:oNode.cloneNode(false).outerHTML;}
return tmp.getElementsByTagName("*")[0];}};}catch(e){}}
if(!Sarissa.getParseErrorText){Sarissa.getParseErrorText=function(oDoc){var parseErrorText=Sarissa.PARSED_OK;if((!oDoc)||(!oDoc.documentElement)){parseErrorText=Sarissa.PARSED_EMPTY;}else if(oDoc.documentElement.tagName=="parsererror"){parseErrorText=oDoc.documentElement.firstChild.data;parseErrorText+="\n"+oDoc.documentElement.firstChild.nextSibling.firstChild.data;}else if(oDoc.getElementsByTagName("parsererror").length>0){var parsererror=oDoc.getElementsByTagName("parsererror")[0];parseErrorText=Sarissa.getText(parsererror,true)+"\n";}else if(oDoc.parseError&&oDoc.parseError.errorCode!=0){parseErrorText=Sarissa.PARSED_UNKNOWN_ERROR;}
return parseErrorText;};}
Sarissa.getText=function(oNode,deep){var s="";var nodes=oNode.childNodes;for(var i=0;i<nodes.length;i++){var node=nodes[i];var nodeType=node.nodeType;if(nodeType==Node.TEXT_NODE||nodeType==Node.CDATA_SECTION_NODE){s+=node.data;}else if(deep===true&&(nodeType==Node.ELEMENT_NODE||nodeType==Node.DOCUMENT_NODE||nodeType==Node.DOCUMENT_FRAGMENT_NODE)){s+=Sarissa.getText(node,true);}}
return s;};if(!window.XMLSerializer&&Sarissa.getDomDocument&&Sarissa.getDomDocument("","foo",null).xml){XMLSerializer=function(){};XMLSerializer.prototype.serializeToString=function(oNode){return oNode.xml;};}
Sarissa.stripTags=function(s){return s?s.replace(/<[^>]+>/g,""):s;};Sarissa.clearChildNodes=function(oNode){while(oNode.firstChild){oNode.removeChild(oNode.firstChild);}};Sarissa.copyChildNodes=function(nodeFrom,nodeTo,bPreserveExisting){if(Sarissa._SARISSA_IS_SAFARI&&nodeTo.nodeType==Node.DOCUMENT_NODE){nodeTo=nodeTo.documentElement;}
if((!nodeFrom)||(!nodeTo)){throw"Both source and destination nodes must be provided";}
if(!bPreserveExisting){Sarissa.clearChildNodes(nodeTo);}
var ownerDoc=nodeTo.nodeType==Node.DOCUMENT_NODE?nodeTo:nodeTo.ownerDocument;var nodes=nodeFrom.childNodes;var i;if(typeof(ownerDoc.importNode)!="undefined"){for(i=0;i<nodes.length;i++){nodeTo.appendChild(ownerDoc.importNode(nodes[i],true));}}else{for(i=0;i<nodes.length;i++){nodeTo.appendChild(nodes[i].cloneNode(true));}}};Sarissa.moveChildNodes=function(nodeFrom,nodeTo,bPreserveExisting){if((!nodeFrom)||(!nodeTo)){throw"Both source and destination nodes must be provided";}
if(!bPreserveExisting){Sarissa.clearChildNodes(nodeTo);}
var nodes=nodeFrom.childNodes;if(nodeFrom.ownerDocument==nodeTo.ownerDocument){while(nodeFrom.firstChild){nodeTo.appendChild(nodeFrom.firstChild);}}else{var ownerDoc=nodeTo.nodeType==Node.DOCUMENT_NODE?nodeTo:nodeTo.ownerDocument;var i;if(typeof(ownerDoc.importNode)!="undefined"){for(i=0;i<nodes.length;i++){nodeTo.appendChild(ownerDoc.importNode(nodes[i],true));}}else{for(i=0;i<nodes.length;i++){nodeTo.appendChild(nodes[i].cloneNode(true));}}
Sarissa.clearChildNodes(nodeFrom);}};Sarissa.xmlize=function(anyObject,objectName,indentSpace){indentSpace=indentSpace?indentSpace:'';var s=indentSpace+'<'+objectName+'>';var isLeaf=false;if(!(anyObject instanceof Object)||anyObject instanceof Number||anyObject instanceof String||anyObject instanceof Boolean||anyObject instanceof Date){s+=Sarissa.escape(""+anyObject);isLeaf=true;}else{s+="\n";var isArrayItem=anyObject instanceof Array;for(var name in anyObject){s+=Sarissa.xmlize(anyObject[name],(isArrayItem?"array-item key=\""+name+"\"":name),indentSpace+"   ");}
s+=indentSpace;}
return(s+=(objectName.indexOf(' ')!=-1?"</array-item>\n":"</"+objectName+">\n"));};Sarissa.escape=function(sXml){return sXml.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;");};Sarissa.unescape=function(sXml){return sXml.replace(/&apos;/g,"'").replace(/&quot;/g,"\"").replace(/&gt;/g,">").replace(/&lt;/g,"<").replace(/&amp;/g,"&");};Sarissa.updateCursor=function(oTargetElement,sValue){if(oTargetElement&&oTargetElement.style&&oTargetElement.style.cursor!=undefined){oTargetElement.style.cursor=sValue;}};Sarissa.updateContentFromURI=function(sFromUrl,oTargetElement,xsltproc,callback,skipCache){try{Sarissa.updateCursor(oTargetElement,"wait");var xmlhttp=new XMLHttpRequest();xmlhttp.open("GET",sFromUrl,true);xmlhttp.onreadystatechange=function(){if(xmlhttp.readyState==4){try{var oDomDoc=xmlhttp.responseXML;if(oDomDoc&&Sarissa.getParseErrorText(oDomDoc)==Sarissa.PARSED_OK){Sarissa.updateContentFromNode(xmlhttp.responseXML,oTargetElement,xsltproc);if(callback){callback(sFromUrl,oTargetElement);}}
else{throw Sarissa.getParseErrorText(oDomDoc);}}
catch(e){if(callback){callback(sFromUrl,oTargetElement,e);}
else{throw e;}}}};if(skipCache){var oldage="Sat, 1 Jan 2000 00:00:00 GMT";xmlhttp.setRequestHeader("If-Modified-Since",oldage);}
xmlhttp.send("");}
catch(e){Sarissa.updateCursor(oTargetElement,"auto");if(callback){callback(sFromUrl,oTargetElement,e);}
else{throw e;}}};Sarissa.updateContentFromNode=function(oNode,oTargetElement,xsltproc){try{Sarissa.updateCursor(oTargetElement,"wait");Sarissa.clearChildNodes(oTargetElement);var ownerDoc=oNode.nodeType==Node.DOCUMENT_NODE?oNode:oNode.ownerDocument;if(ownerDoc.parseError&&ownerDoc.parseError.errorCode!=0){var pre=document.createElement("pre");pre.appendChild(document.createTextNode(Sarissa.getParseErrorText(ownerDoc)));oTargetElement.appendChild(pre);}
else{if(xsltproc){oNode=xsltproc.transformToDocument(oNode);}
if(oTargetElement.tagName.toLowerCase()=="textarea"||oTargetElement.tagName.toLowerCase()=="input"){oTargetElement.value=new XMLSerializer().serializeToString(oNode);}
else{try{oTargetElement.appendChild(oTargetElement.ownerDocument.importNode(oNode,true));}
catch(e){oTargetElement.innerHTML=new XMLSerializer().serializeToString(oNode);}}}}
catch(e){throw e;}
finally{Sarissa.updateCursor(oTargetElement,"auto");}};Sarissa.formToQueryString=function(oForm){var qs="";for(var i=0;i<oForm.elements.length;i++){var oField=oForm.elements[i];var sFieldName=oField.getAttribute("name")?oField.getAttribute("name"):oField.getAttribute("id");if(sFieldName&&((!oField.disabled)||oField.type=="hidden")){switch(oField.type){case"hidden":case"text":case"textarea":case"password":qs+=sFieldName+"="+encodeURIComponent(oField.value)+"&";break;case"select-one":qs+=sFieldName+"="+encodeURIComponent(oField.options[oField.selectedIndex].value)+"&";break;case"select-multiple":for(var j=0;j<oField.length;j++){var optElem=oField.options[j];if(optElem.selected===true){qs+=sFieldName+"[]"+"="+encodeURIComponent(optElem.value)+"&";}}
break;case"checkbox":case"radio":if(oField.checked){qs+=sFieldName+"="+encodeURIComponent(oField.value)+"&";}
break;}}}
return qs.substr(0,qs.length-1);};Sarissa.updateContentFromForm=function(oForm,oTargetElement,xsltproc,callback){try{Sarissa.updateCursor(oTargetElement,"wait");var params=Sarissa.formToQueryString(oForm)+"&"+Sarissa.REMOTE_CALL_FLAG+"=true";var xmlhttp=new XMLHttpRequest();var bUseGet=oForm.getAttribute("method")&&oForm.getAttribute("method").toLowerCase()=="get";if(bUseGet){xmlhttp.open("GET",oForm.getAttribute("action")+"?"+params,true);}
else{xmlhttp.open('POST',oForm.getAttribute("action"),true);xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");xmlhttp.setRequestHeader("Content-length",params.length);xmlhttp.setRequestHeader("Connection","close");}
xmlhttp.onreadystatechange=function(){try{if(xmlhttp.readyState==4){var oDomDoc=xmlhttp.responseXML;if(oDomDoc&&Sarissa.getParseErrorText(oDomDoc)==Sarissa.PARSED_OK){Sarissa.updateContentFromNode(xmlhttp.responseXML,oTargetElement,xsltproc);if(callback){callback(oForm,oTargetElement);}}
else{throw Sarissa.getParseErrorText(oDomDoc);}}}
catch(e){if(callback){callback(oForm,oTargetElement,e);}
else{throw e;}}};xmlhttp.send(bUseGet?"":params);}
catch(e){Sarissa.updateCursor(oTargetElement,"auto");if(callback){callback(oForm,oTargetElement,e);}
else{throw e;}}
return false;};Sarissa.FUNCTION_NAME_REGEXP=new RegExp("");Sarissa.getFunctionName=function(oFunc,bForce){var name;if(!name){if(bForce){name="SarissaAnonymous"+Sarissa._getUniqueSuffix();window[name]=oFunc;}
else{name=null;}}
if(name){window[name]=oFunc;}
return name;};Sarissa.setRemoteJsonCallback=function(url,callback,callbackParam){if(!callbackParam){callbackParam="callback";}
var callbackFunctionName=Sarissa.getFunctionName(callback,true);var id="sarissa_json_script_id_"+Sarissa._getUniqueSuffix();var oHead=document.getElementsByTagName("head")[0];var scriptTag=document.createElement('script');scriptTag.type='text/javascript';scriptTag.id=id;scriptTag.onload=function(){};if(url.indexOf("?")!=-1){url+=("&"+callbackParam+"="+callbackFunctionName);}
else{url+=("?"+callbackParam+"="+callbackFunctionName);}
scriptTag.src=url;oHead.appendChild(scriptTag);return id;};

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

if(Sarissa._SARISSA_HAS_DOM_FEATURE&&document.implementation.hasFeature("XPath","3.0")){SarissaNodeList=function(i){this.length=i;};SarissaNodeList.prototype=[];SarissaNodeList.prototype.constructor=Array;SarissaNodeList.prototype.item=function(i){return(i<0||i>=this.length)?null:this[i];};SarissaNodeList.prototype.expr="";if(window.XMLDocument&&(!XMLDocument.prototype.setProperty)){XMLDocument.prototype.setProperty=function(x,y){};}
Sarissa.setXpathNamespaces=function(oDoc,sNsSet){oDoc._sarissa_useCustomResolver=true;var namespaces=sNsSet.indexOf(" ")>-1?sNsSet.split(" "):[sNsSet];oDoc._sarissa_xpathNamespaces=[];for(var i=0;i<namespaces.length;i++){var ns=namespaces[i];var colonPos=ns.indexOf(":");var assignPos=ns.indexOf("=");if(colonPos>0&&assignPos>colonPos+1){var prefix=ns.substring(colonPos+1,assignPos);var uri=ns.substring(assignPos+2,ns.length-1);oDoc._sarissa_xpathNamespaces[prefix]=uri;}else{throw"Bad format on namespace declaration(s) given";}}};XMLDocument.prototype._sarissa_useCustomResolver=false;XMLDocument.prototype._sarissa_xpathNamespaces=[];XMLDocument.prototype.selectNodes=function(sExpr,contextNode,returnSingle){var nsDoc=this;var nsresolver;if(this._sarissa_useCustomResolver){nsresolver=function(prefix){var s=nsDoc._sarissa_xpathNamespaces[prefix];if(s){return s;}
else{throw"No namespace URI found for prefix: '"+prefix+"'";}};}
else{nsresolver=this.createNSResolver(this.documentElement);}
var result=null;if(!returnSingle){var oResult=this.evaluate(sExpr,(contextNode?contextNode:this),nsresolver,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);var nodeList=new SarissaNodeList(oResult.snapshotLength);nodeList.expr=sExpr;for(var i=0;i<nodeList.length;i++){nodeList[i]=oResult.snapshotItem(i);}
result=nodeList;}
else{result=this.evaluate(sExpr,(contextNode?contextNode:this),nsresolver,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue;}
return result;};Element.prototype.selectNodes=function(sExpr){var doc=this.ownerDocument;if(doc.selectNodes){return doc.selectNodes(sExpr,this);}
else{throw"Method selectNodes is only supported by XML Elements";}};XMLDocument.prototype.selectSingleNode=function(sExpr,contextNode){var ctx=contextNode?contextNode:null;return this.selectNodes(sExpr,ctx,true);};Element.prototype.selectSingleNode=function(sExpr){var doc=this.ownerDocument;if(doc.selectSingleNode){return doc.selectSingleNode(sExpr,this);}
else{throw"Method selectNodes is only supported by XML Elements";}};Sarissa.IS_ENABLED_SELECT_NODES=true;}
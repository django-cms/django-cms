/**
 * xslTransform
 * Tools for XSLT transformations; jQuery wrapper for Sarissa <http://sarissa.sourceforge.net/>.
 * See jQuery.fn.log below for documentation on $.log().
 * See jQuery.fn.getTransform below for documention on the $.getTransform().
 * See var DEBUG below for turning debugging/logging on and off.
 *
 * @version   20071203
 * @since     2006-07-05
 * @copyright Copyright (c) 2006 Glyphix Studio, Inc. http://www.glyphix.com
 * @author    Brad Brizendine <brizbane@gmail.com>, Matt Antone <antone@glyphix.com>
 * @license   MIT http://www.opensource.org/licenses/mit-license.php
 * @requires  >= jQuery 1.0.3			http://jquery.com/
 * @requires  jquery.debug.js			http://jquery.glyphix.com/
 * @requires  >= sarissa.js 0.9.7.6		http://sarissa.sourceforge.net/
 *
 * @example
 * var r = xslTransform.transform('path-to-xsl.xsl','path-to-xml.xml');
 * @desc Perform a transformation and place the results in var r
 *
 * @example
 * var r = xslTransform.transform('path-to-xsl.xsl','path-to-xml.xml');
 * var str = xslTransform.serialize( r );
 * @desc Perform a transformation, then turn the result into a string
 *
 * @example
 * var doc = xslTransform.load('path-to-xml.xml');
 * @desc Load an xml file and return a parsed xml object
 *
 * @example
 * var xml = '<xmldoc><foo>bar</foo></xmldoc>';
 * var doc = xslTransform.load(xml);
 * @desc Load an xml string and return a parsed xml object
 */
var xslTransform = {

	version: 20071203,
	debug: false,

	// init ... test for requirements
	init: function(){
		// check for v1.0.4 / v1.1 or later of jQuery
		try{
			parseFloat(jQuery.fn.jquery) >= 1;
		}catch(e){
			alert('xslTransform requires jQuery 1.0.4 or greater ... please load it prior to xslTransform');
		}
		// check for Sarissa
		try{
			Sarissa;
		}catch(e){
			alert('Missing Sarissa ... please load it prior to xslTransform');
		}
		// if no log function, create a blank one
		if( !jQuery.log ){
			jQuery.log = function(){};
			jQuery.fn.debug = function(){};
		}
		// log the version
		if(this.debug) jQuery.log( 'xslTransform:init(): version ' + xslTransform.version );
	},

	// initialize Sarissa's serializer
	XMLSerializer: new XMLSerializer(),

	/*
	 * serialize
	 * Turns the provided object into a string and returns it.
	 *
	 * @param data Mixed
	 * @returns String
	 */
	serialize: function( data ){
		if(this.debug) jQuery.log( 'serialize(): received ' + typeof(data) );
		// if it's already a string, no further processing required
		if( typeof(data) == 'string' ){
			return data;
		}

		return this.XMLSerializer.serializeToString( data );
	},

	/*
	 * load
	 * Attempts to load xml data by automatically sensing the type of the provided data.
	 *
	 * @param xml Mixed the xml data
	 * @returns Object
	 */
	load: function( xml, meth ){
		if(this.debug) jQuery.log( 'load(): received ' + typeof(xml) );
		// the result
		var r;

		// if it's an object, assume it's already an XML object, so just return it
		if( typeof(xml) == 'object' ){
			return xml;
		}

		// if it's a string, determine if it's xml data or a path
		// assume that the first character is an opening caret if it's XML data
		if( xml.substring(0,1) == '<' ){
			r = this.loadString( xml );
		}else{
			r = this.loadFile( xml , meth );
		}

		if( r ){
			// the following two lines are needed to get IE (msxml3) to run xpath ... set it on all xml data
			r.setProperty( 'SelectionNamespaces', 'xmlns:xsl="http://www.w3.org/1999/XSL/Transform"' );
			r.setProperty( 'SelectionLanguage', 'XPath' );
			return r;
		}else{
			if(this.debug) $.log( 'Unable to load ' + xml );
			return false;
		}
	},

	/*
	 * loadString
	 * Parses an XML string and returns the result.
	 *
	 * @param str String the xml string to turn into a parsed XML object
	 * @returns Object
	 */
	loadString: function( str ){
		if(this.debug) jQuery.log( 'loadString(): ' + str + '::' + typeof(str) );

		// use Sarissa to generate an XML doc
		var p = new DOMParser();
		var xml = p.parseFromString( str, 'text/xml' );
		if( !xml ){
			if(this.debug) jQuery.log( 'loadString(): parseFromString() failed' );
			return false;
		}
		return xml;
	},

	/*
	 * loadFile
	 * Attempts to retrieve the requested path, specified by url.
	 * If url is an object, it's assumed it's already loaded, and just returns it.
	 *
	 * @param url Mixed
	 * @returns Object
	 */
	loadFile: function( url, meth ){
		if(this.debug) jQuery.log( 'loadFile(): ' + url + '::' + typeof(url) );

		if( !url ){
			if(this.debug) jQuery.log( 'ERROR: loadFile() missing url' );
			return false;
		}

		// variable to hold ajax results
		var doc;
		// function to receive data on successful download ... semicolon after brace is necessary for packing
		this.xhrsuccess = function(data,str){
			if(this.debug) jQuery.log( 'loadFile() completed successfully (' + str + ')' );
			doc = data;
			return true;
		};
		// function to handle downloading error ... semicolon after brace is necessary for packing
		this.xhrerror = function(xhr,err){
			// set debugging to true in order to force the display of this error
			window.DEBUG = true;
			if(this.debug) jQuery.log( 'loadFile() failed to load the requested file: (' + err + ') - xml: ' + xhr.responseXML + ' - text: ' + xhr.responseText );
			doc = null;
			return false;
		};

		// make asynchronous ajax call and call functions defined above on success/error
		if(!meth) meth = "GET";
		$.ajax({
			type:		meth,
			url:		url,
			async:		false,
			success:	this.xhrsuccess,
			error:		this.xhrerror
		});

		// check for total failure
		if( !doc ){
			if(this.debug) jQuery.log( 'ERROR: document ' + url + ' not found (404), or unable to load' );
			return false;
		}
		// check for success but no data
		if( doc.length == 0 ){
			if(this.debug) jQuery.log( 'ERROR: document ' + url + ' loaded in loadFile() has no data' );
			return false;
		}
		return doc;
	},

	/*
	 * transform
	 * Central transformation function: takes an xml doc and an xsl doc.
	 *
	 * @param xsl Mixed the xsl transformation document
	 * @param xml Mixed the xml document to be transformed
	 * @param options Object various switches you can send to this function
	 * 		+ params: an object of key/value pairs to be sent to xsl as parameters
	 * 		+ xpath: defines the root node within the provided xml file
	 * @returns Object the results of the transformation
	 * 		+ xsl: the raw xsl doc
	 * 		+ doc: the raw results of the transform
	 * 		+ string: the serialized doc
	 */
	transform: function( xsl, xml, options ){
		var log = { 'xsl':xsl, 'xml':xml, 'options':options };
		if(this.debug) jQuery.log( 'transform(): ' + xsl + '::' + xml + '::' + options.toString() );

		// initialize options hash
		options = options || {};

		// initialize the xml object and store it in xml.doc
		var xml = { 'request':xml, 'doc':this.load(xml, options.meth) };
		// if we have an xpath, replace xml.doc with the results of running it
		// as of 2007-12-03, IE throws a "msxml6: the parameter is incorrect" error, so removing this
		if( options.xpath && xml.doc && !jQuery.browser.msie ){
			// run the xpath
			xml.doc = xml.doc.selectSingleNode( options.xpath.toString() );
			if(this.debug) $.log( 'transform(): xpath has been run...resulting doc: ' + (this.serialize(xml.doc)) );
		}

		// initialize the result object ... store the primary steps of the transform in result
		var result = { 'xsl':this.load(xsl, options.meth) };

		result.json = false;
		if( options.json && xml.doc ) {
			result.json = xml.doc.selectSingleNode( options.json.toString() );
		}

		var processor = new XSLTProcessor();
		// stylesheet must be imported before parameters can be added
		processor.importStylesheet( result.xsl );
		// add parameters to the processor
		if( options.params && processor ){
			if(this.debug) jQuery.log( 'transform(): received xsl params: ' + options.params.toString() );
			for( key in options.params ){
				// name and value must be strings
				// first parameter is namespace
				processor.setParameter( null, key.toString(), options.params[key].toString() );
			}
		}

		// perform the transformation
		result.doc = processor.transformToDocument( xml.doc );
		// handle transform error
		var errorTxt = Sarissa.getParseErrorText(result.doc);
		if(this.debug) jQuery.log( 'transform(): Sarissa parse text: ' + errorTxt );
		if( errorTxt != Sarissa.PARSED_OK ){
			// return the error text as the string
			result.string = Sarissa.getParseErrorText(result.doc) + ' :: using ' + xsl + ' => ' + xml.request;
			if(this.debug) jQuery.log( 'transform(): error in transformation: ' + Sarissa.getParseErrorText(result.doc) );
			return result;
		}

		// if we made it this far, the transformation was successful
		result.string = this.serialize( result.doc );
		// store reference to all scripts found in the doc (not result.string)
		result.scripts = jQuery('script',result.doc).text();

		return result;
	}

};

// create the xslTransform object
// this creates a single object for the page, allowing re-use of the XSL processor
xslTransform.init();

/*
 * JQuery XSLT transformation plugin.
 * Replaces all matched elements with the results of an XSLT transformation.
 * See xslTransform above for more documentation.
 *
 * @example
 * @desc See the xslTransform-example/index.html
 *
 * @param xsl String the url to the xsl file
 * @param xml String the url to the xml file
 * @param options Object various switches you can send to this function
 * 		+ params: an object of key/value pairs to be sent to xsl as parameters
 * 		+ xpath: defines the root node within the provided xml file
 * 		+ eval: if true, will attempt to eval javascript found in the transformed result
 *		+ callback: if a Function, evaluate it when transformation is complete
 * @returns
 */
jQuery.fn.getTransform = function( xsl, xml, options ){
	var settings = {
		append: false,
		params: {},		// object of key/value pairs ... parameters to send to the XSL stylesheet
		xpath: '',		// xpath, used to send only a portion of the XML file to the XSL stylesheet
		eval: true,		// evaluate <script> blocks found in the transformed result
		callback: '',	// callback function, to be run on completion of the transformation
		json: false,
		meth : "GET"
	};
	// initialize options hash; override the defaults with supplied options
	jQuery.extend( settings, options );
	if(xslTransform.debug) jQuery.log( 'getTransform: ' + xsl + '::' + xml + '::' + settings.toString() );

	// must have both xsl and xml
	if( !xsl || !xml ){
		if(xslTransform.debug) jQuery.log( 'getTransform: missing xsl or xml' );
		return;
	}

	// run the jquery magic on all matched elements
	return this.each( function(){
		// perform the transformation
		var trans = xslTransform.transform( xsl, xml, settings );

		// ie can fail if there's an xml declaration line in the returned result
		var re = trans.string.match(/<\?xml.*?\?>/);
		if( re ){
			trans.string = trans.string.replace( re, '' );
			if(xslTransform.debug) jQuery.log( 'getTransform(): found an xml declaration and removed it' );
		}

		// place the result in the element
		// 20070202: jquery 1.1.1 can get a "a.appendChild is not a function" error using html() sometimes ...
		//		no idea why yet, so adding a fallback to innerHTML
		//		::warning:: ie6 has trouble with javascript events such as onclick assigned statically within the html when using innerHTML
		try {
			if(settings.append)			$(this).append( trans.string );
			else if(settings.repl)		$(this).replaceWith( trans.string );
			else						$(this).html( trans.string );
		} catch(e) {
			if(xslTransform.debug) $.log( 'getTransform: error placing results of transform into element, falling back to innerHTML: ' + e.toString() );
			$(this)[0].innerHTML = trans.string;
		}

		// there might not be a scripts property
		if( settings.eval && trans.scripts ){
			if( trans.scripts.length > 0 ){
				if(xslTransform.debug) jQuery.log( 'Found text/javascript in transformed result' );
				eval.call( window, trans.scripts );
			}
		}

		// run the callback if it's a native function
		if( settings.callback && jQuery.isFunction(settings.callback) ){
			var json = false;
			if(settings.json && trans.json) eval("json = " + trans.json.firstChild.data);
			settings.callback.apply(window, [trans.string, json]);
		}

	});

};
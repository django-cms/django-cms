/**
 * @framework	CFF - Classy Frontend Framework
 * @author		Angelo Dini | original by Armin Ronacher.
 * @copyright	http://www.divio.ch under the BSD Licence
 */

/* create a global log object */
var log = function(msg){return alert(msg);};
// check if console.log is available and register log(msg) or $(el).log(msg)
if(window['console'] === undefined) {
	window.console = { log: function(msg){return alert(msg);}, debug: function(msg){return alert(msg);} };
} else {
	log = console.debug || console.log || alert;
}

/* initialize classy */
(function() {
	var CLASSY_VERSION = '1.3.1',
		ROOT = this,
		DISABLE_CONSTRUCTOR = false;
		_Class = window.Class;

	/* we check if $super is in use by a class if we can.  But first we have to
	   check if the JavaScript interpreter supports that.  This also matches
	   to false positives later, but that does not do any harm besides slightly
	   slowing calls down. */
	var probe_super = (function(){$super();}).toString().indexOf('$super') > 0;
	function usesSuper(obj) {
		return !probe_super || /\B\$super\b/.test(obj.toString());
	}

	/* helper function to set the attribute of something to a value or
	   removes it if the value is undefined. */
	function setOrUnset(obj, key, value) {
		(value === undefined) ? delete obj[key] : obj[key] = value;
	}

	/* gets the own property of an object */
	function getOwnProperty(obj, name) {
		return Object.prototype.hasOwnProperty.call(obj, name) ? obj[name] : undefined;
	}

	/* instanciate a class without calling the constructor */
	function cheapNew(cls) {
		DISABLE_CONSTRUCTOR = true;
		var rv = new cls;
		DISABLE_CONSTRUCTOR = false;
		return rv;
	}

	/* the base class we export */
	var Class = function(){};

	/* restore the global Class name and pass it to a function.  This allows
	   different versions of the classy library to be used side by side and
	   in combination with other libraries. */
	Class.$noConflict = function(deep) {
		if(window.Class === Class) {
			window.Class = _Class;
		}

		if(deep && window.Class === Class) {
			window.Class = _Class;
		}

		return Class;
	};

	/* what version of classy are we using? */
	Class.$classyVersion = CLASSY_VERSION;

	/* extend functionality */
	Class.$extend = function(properties) {
		var super_prototype = this.prototype;

		/* disable constructors and instanciate prototype.  Because the
		   prototype can't raise an exception when created, we are safe
		   without a try/finally here. */
		var prototype = cheapNew(this);

		/* copy all properties of the includes over if there are any */
		if(properties.implement) {
			for (var i = 0, n = properties.implement.length; i != n; ++i) {
				var mixin = properties.implement[i];
				for (var name in mixin) {
					value = getOwnProperty(mixin, name);
					if (value !== undefined) prototype[name] = mixin[name];
				}
			}
		}

		/* copy class vars from the superclass */
		properties.options = properties.options || {};
		if(prototype.options) {
			for(key in prototype.options) {
				if(!properties.options[key]) {
					value = getOwnProperty(prototype.options, key);
					properties.options[key] = value;
				}
			}
		}

		/* copy all properties over to the new prototype */
		for(name in properties) {
			value = getOwnProperty(properties, name);
			if (name === 'implements' || value === undefined) continue;

			prototype[name] = typeof value === 'function' && usesSuper(value) ? (function(meth, name) {
				return function() {
					var old_super = getOwnProperty(this, '$super');
					this.$super = super_prototype[name];
					try {
						return meth.apply(this, arguments);
					} finally {
						setOrUnset(this, '$super', old_super);
					}
				};
			})(value, name) : value
		}

		/* dummy constructor */
		var rv = function () {
			if (DISABLE_CONSTRUCTOR) return;
			var proper_this = ROOT === this ? cheapNew(arguments.callee) : this;
			if (proper_this.initialize) proper_this.initialize.apply(proper_this, arguments);
			proper_this.$options = rv;
			return proper_this;
		};

		/* copy all class vars over of any */
		for(var key in properties.options) {
			var value = getOwnProperty(properties.options, key);
			if (value !== undefined) rv[key] = value;
		}

		/* copy prototype and constructor over, reattach $extend and
		   return the class */
		rv.prototype = prototype;
		rv.constructor = rv;
		rv.$extend = Class.$extend;
		rv.$withData = Class.$withData;
		return rv;
	};

	/* instanciate with data functionality */
	Class.$withData = function (data) {
		var rv = cheapNew(this);
		for (var key in data) {
			var value = getOwnProperty(data, key);
			if (value !== undefined) rv[key] = value;
		}
		return rv;
	};

	/* export the class */
	ROOT.Class = Class;

})();
(function($){
	$.curry = function(fn) {
		if (arguments.length < 2) return fn;
		args = $.makeArray(arguments).slice(1, arguments.length);
		return function() {
			return fn.apply(this, args.concat($.makeArray(arguments)));
		}
	}  
	
	$.__callbackPool = {}; 
	
	$.callbackRegister = function(name, fn /*, arg0, arg1, ..*/){
		if (arguments.length > 2) {
			// create curried function
			fn = $.curry.apply(this, $.makeArray(arguments).slice(1, arguments.length));
		}
		$.__callbackPool[name] = fn;
		return name;	
	}
	
	$.callbackCall = function(name/*, extra arg0, extra arg1, ..*/){
		if (!name || !name in $.__callbackPool) {
			throw "No callback registered with name: " + name;
		}
		$.__callbackPool[name].apply(this, $.makeArray(arguments).slice(1, arguments.length));
		$.callbackRemove(name);	
		return name;
	}
	
	$.callbackRemove = function(name) {
		delete $.__callbackPool[name];
	}
	
})(jQuery);
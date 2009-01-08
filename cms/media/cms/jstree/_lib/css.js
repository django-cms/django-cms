function get_css(rule_name, stylesheet, delete_flag) {
	if (!document.styleSheets) return false;
	rule_name = rule_name.toLowerCase(); stylesheet = stylesheet || 0;
	for (var i = stylesheet; i < document.styleSheets.length; i++) { 
		var styleSheet = document.styleSheets[i]; css_rules = document.styleSheets[i].cssRules || document.styleSheets[i].rules;
		if(!css_rules) continue;
		var j = 0;
		do {
			if(css_rules[j].selectorText.toLowerCase() == rule_name) {
				if(delete_flag == true) {
					if(document.styleSheets[i].removeRule) document.styleSheets[i].removeRule(j);
					if(document.styleSheets[i].deleteRule) document.styleSheets[i].deleteRule(j);
					return true;
				}
				else return css_rules[j];
			}
		}
		while (css_rules[++j]);
	}
	return false;
}
function add_css(rule_name, stylesheet) {
	rule_name = rule_name.toLowerCase(); stylesheet = stylesheet || 0;
	if (!document.styleSheets || get_css(rule_name, stylesheet)) return false;
	(document.styleSheets[stylesheet].addRule) ? document.styleSheets[stylesheet].addRule(rule_name, null, 0) : document.styleSheets[stylesheet].insertRule(rule_name+' { }', 0);
	return get_css(rule_name);
}
function get_sheet_num (href_name) {
	if (!document.styleSheets) return false;
	for (var i = 0; i < document.styleSheets.length; i++) { if(document.styleSheets[i].href && document.styleSheets[i].href.toString().match(href_name)) return i; } 
	return false;
}
function remove_css(rule_name, stylesheet) { return get_css(rule_name, stylesheet, true); }

function add_sheet(url) {
	if(document.createStyleSheet) {
		document.createStyleSheet(url);
	}
	else {
		var styles	= "@import url(' " + url + " ');";
		var newSS	= document.createElement('link');
		newSS.rel	='stylesheet';
		newSS.href	='data:text/css,'+escape(styles);
		document.getElementsByTagName("head")[0].appendChild(newSS);
	}
}
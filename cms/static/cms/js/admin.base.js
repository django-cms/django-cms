// polyfills
require('./polyfills/function.prototype.bind.js');
require('./libs/pep');
var CMS = require('./modules/cms.base');

// in case some data is already attached to the CMS global
// we shoud not override it
window.CMS = CMS.$.extend(window.CMS || {}, CMS);

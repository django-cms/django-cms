// polyfills
require('./polyfills/function.prototype.bind.js');
require('./libs/pep');

var CMS = require('./modules/cms.base').default;

window.CMS = CMS;

CMS.PageTree = require('./modules/cms.pagetree').default;

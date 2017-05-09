// polyfills
require('./polyfills/function.prototype.bind');
import initHelpShortcuts from './modules/shortcuts';

// jquery plugins
require('./libs/pep');

var _plugins;

if (window.CMS && window.CMS._plugins) {
    _plugins = window.CMS._plugins;
}

// CMS Core
var CMS = require('./modules/cms.base');

CMS._plugins = _plugins;

// exposing globals for backwards compatibility
CMS.Messages = require('./modules/cms.messages').default;
CMS.ChangeTracker = require('./modules/cms.changetracker').default;
CMS.Modal = require('./modules/cms.modal').default;
CMS.Sideframe = require('./modules/cms.sideframe').default;
CMS.Clipboard = require('./modules/cms.clipboard').default;
CMS.Plugin = require('./modules/cms.plugins').default;
CMS.StructureBoard = require('./modules/cms.structureboard').default;
CMS.Navigation = require('./modules/cms.navigation').default;
CMS.Toolbar = require('./modules/cms.toolbar').default;
CMS.Tooltip = require('./modules/cms.tooltip').default;
CMS.API = CMS.default.API;
CMS.$ = CMS.default.$;
CMS.KEYS = CMS.default.KEYS;
require('./modules/dropdown');

initHelpShortcuts();

window.CMS = CMS;

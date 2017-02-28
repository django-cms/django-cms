// polyfills
require('./polyfills/function.prototype.bind');

// jquery plugins
require('./libs/pep');

// CMS Core
var CMS = require('./modules/cms.base');

// exposing globals for backwards compatibility
CMS.Messages = require('./modules/cms.messages');
CMS.ChangeTracker = require('./modules/cms.changetracker');
CMS.Modal = require('./modules/cms.modal');
CMS.Sideframe = require('./modules/cms.sideframe');
CMS.Clipboard = require('./modules/cms.clipboard');
CMS.Plugin = require('./modules/cms.plugins');
CMS.StructureBoard = require('./modules/cms.structureboard');
CMS.Navigation = require('./modules/cms.navigation');
CMS.Toolbar = require('./modules/cms.toolbar');
CMS.Tooltip = require('./modules/cms.tooltip');
require('./modules/shortcuts')();

window.CMS = CMS;

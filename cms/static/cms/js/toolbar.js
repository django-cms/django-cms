// polyfills
import './polyfills/function.prototype.bind';
import initHelpShortcuts from './modules/shortcuts';

// jquery plugins
import './libs/pep';

import './modules/dropdown';

// CMS Core
import CMS, { Helpers, KEYS } from './modules/cms.base';
import $ from 'jquery';
import Class from 'classjs';

// exposing globals for backwards compatibility
import Messages from './modules/cms.messages';
import ChangeTracker from './modules/cms.changetracker';
import Modal from './modules/cms.modal';
import Sideframe from './modules/cms.sideframe';
import Clipboard from './modules/cms.clipboard';
import Plugin from './modules/cms.plugins';
import StructureBoard from './modules/cms.structureboard';
import Toolbar from './modules/cms.toolbar';
import Tooltip from './modules/cms.tooltip';

CMS._plugins = CMS._plugins || [];

CMS.Messages = Messages;
CMS.ChangeTracker = ChangeTracker;
CMS.Modal = Modal;
CMS.Sideframe = Sideframe;
CMS.Clipboard = Clipboard;
CMS.Plugin = Plugin;
CMS.StructureBoard = StructureBoard;
CMS.Toolbar = Toolbar;
CMS.Tooltip = Tooltip;

CMS.API = {
    Helpers
};
CMS.KEYS = KEYS;
CMS.$ = $;
CMS.Class = Class;

// The DOM probably isn't finished loading, but the config should nevertheless be available
CMS.config = JSON.parse(document.getElementById('cms-config').text);

initHelpShortcuts();

window.CMS = CMS;

$(function () {
    $('.cms-plugin-data').each(function(i, plugin_elements) {
        CMS._plugins = CMS._plugins.concat(JSON.parse(plugin_elements.text));
    });

    $('.cms-placeholder-data').each(function(i, placeholder_element) {
        CMS._plugins.push(JSON.parse(placeholder_element.text));
    });

    CMS.settings = CMS.API.Helpers.getSettings();

    // extends API
    CMS.API.Toolbar = new CMS.Toolbar();
    CMS.API.Clipboard = new CMS.Clipboard();
    CMS.API.StructureBoard = new CMS.StructureBoard();
    CMS.API.Messages = new CMS.Messages();
    CMS.API.Tooltip = new CMS.Tooltip();

    CMS.Plugin._initializeTree();
});

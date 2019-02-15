'use strict';
var initShortcuts = require('../../../static/cms/js/modules/shortcuts').default;
var initHelpModal = require('../../../static/cms/js/modules/shortcuts/help').default;
var initCreateModal = require('../../../static/cms/js/modules/shortcuts/create-modal').default;
var $ = require('jquery');
var keyboard = require('../../../static/cms/js/modules/keyboard').default;
var Modal = require('../../../static/cms/js/modules/cms.modal').default;

var CMS = window.CMS || {};

CMS.config = CMS.config || {};
CMS.config.lang = CMS.config.lang || {};
var shortcutAreas = [
    {
        title: 'CMS Wide Shortcuts',
        shortcuts: {
            help: {
                shortcut: '?',
                desc: 'Bring up this help dialog'
            },
            esc: {
                shortcut: 'ESC',
                desc: 'Close / cancel'
            },
            'toggle-structure-board': {
                shortcut: 'space',
                desc: 'Toggle structure mode'
            },
            'toggle-structure-board-using-hovered-plugin': {
                shortcut: 'shift+space',
                desc: 'Toggle structure mode and highlight hovered plugin'
            },
            'create-dialog': {
                shortcut: 'alt+c',
                desc: 'Open \u0022Create\u0022 dialog'
            },
            toolbar: {
                shortcut: 'f > t / alt+t'
            }
        }
    },
    {
        title: 'Structure Board',
        shortcuts: {
            placeholders: {
                shortcut: 'f > p',
                desc: 'Focus placeholders'
            },
            traversing: {
                shortcut: 'tab / shift+tab',
                desc: 'Move to next / previous element'
            },
            enter: {
                shortcut: 'enter',
                desc: 'Focus on plugins of placeholder'
            },
            edit: {
                shortcut: 'e',
                desc: 'Edit plugin'
            },
            add: {
                shortcut: '+ / a',
                desc: 'Add plugin'
            },
            settings: {
                shortcut: 's',
                desc: 'Open settings dropdown'
            },
            collapse: {
                shortcut: 'x',
                desc: 'Expand / collapse'
            }
        }
    }
];
CMS.config.lang.shortcutAreas = shortcutAreas;

window.CMS = CMS;

describe('shortcuts', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    beforeEach(function(done) {
        spyOn(keyboard, 'bind');
        spyOn(keyboard, 'setContext');
        fixture.load('plugins.html');

        $(function() {
            CMS.config.lang.shortcutAreas = shortcutAreas;
            done();
        });
    });

    afterEach(function() {
        fixture.cleanup();
    });

    it('does not explode', function() {
        expect(initShortcuts).not.toThrow();
    });

    describe('help', function() {
        it('binds the shortcut', function() {
            initHelpModal();
            expect(keyboard.setContext).toHaveBeenCalledWith('cms');
            expect(keyboard.bind).toHaveBeenCalledWith('?', jasmine.any(Function));
        });

        it('shortcut opens modal', function() {
            spyOn(Modal.prototype, 'open');
            initHelpModal();
            keyboard.bind.calls.mostRecent().args[1]({ preventDefault() {} });
            expect(Modal.prototype.open).toHaveBeenCalledTimes(1);
            expect(Modal.prototype.open).toHaveBeenCalledWith({
                width: jasmine.any(Number),
                height: jasmine.any(Number),
                title: CMS.config.lang.shortcuts,
                html: jasmine.any(String)
            });
        });
    });

    describe('create-modal', function() {
        it('binds the shortcut', function() {
            initCreateModal();
            expect(keyboard.setContext).toHaveBeenCalledWith('cms');
            expect(keyboard.bind).toHaveBeenCalledWith('alt+c', jasmine.any(Function));
        });

        it('shortcut triggers click on create button', function(done) {
            $(fixture.el).append('<div class="cms-btn" href="wizard"></div>');
            initCreateModal();
            $('.cms-btn').on('click', function() {
                done();
            });
            keyboard.bind.calls.mostRecent().args[1]();
        });
    });
});

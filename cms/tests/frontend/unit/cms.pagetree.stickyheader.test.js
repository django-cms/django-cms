/* global document, window */
'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var PageTreeStickyHeader = require('../../../static/cms/js/modules/cms.pagetree.stickyheader').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.PageTreeStickyHeader = PageTreeStickyHeader;
CMS.$ = $;

describe('CMS.PageTreeStickyHeader', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a PageTreeStickyHeader class', function() {
        expect(CMS.PageTreeStickyHeader).toBeDefined();
    });

    var sticky;
    var header1;
    var col1;
    var header2;
    var col2;

    beforeEach(function(done) {
        fixture.load('pagetree.html');

        $(function() {
            var container = $('.cms-pagetree');
            header1 = $('<div class="jstree-grid-header"></div>');
            col1 = $('<div class="jstree-grid-column" style="width: 100px"></div>');
            header2 = $('<div class="jstree-grid-header"></div>');
            col2 = $('<div class="jstree-grid-column" style="width: 200px"></div>');
            container.append(col1);
            container.append(col2);
            col1.append(header1);
            col2.append(header2);

            spyOn(CMS.API.Helpers, '_getWindow').and.returnValue({
                CMS: CMS
            });

            sticky = new CMS.PageTreeStickyHeader({
                container: container
            });
            done();
        });
    });

    afterEach(function() {
        $(window).off(sticky.resize);
        $(window).off(sticky.scroll);
        fixture.cleanup();
    });

    describe('instance', function() {
        it('has default state', function() {
            expect(sticky.areClonesInDOM).toEqual(false);
            expect(sticky.resize).toEqual('resize.cms.pagetree.header');
            expect(sticky.scroll).toEqual('scroll.cms.pagetree.header');
            expect(sticky.options).toEqual({
                container: $('.cms-pagetree')
            });
        });

        it('has ui', function() {
            expect(sticky.ui).toEqual({
                container: $('.cms-pagetree'),
                window: $(window),
                headers: $('.cms-pagetree').find('.jstree-grid-header'),
                columns: [col1, col2],
                clones: jasmine.any(Array)
            });
        });
    });

    describe('_saveSizes()', function() {
        it('saves headers top offset', function() {
            expect(sticky.headersTopOffset).toEqual(jasmine.any(Number));
            spyOn($.fn, 'offset').and.returnValue({ top: 'MOCK' });
            sticky._saveSizes();
            expect(sticky.headersTopOffset).toEqual('MOCK');
        });

        it('saves toolbar height if in admin', function() {
            spyOn(sticky, '_isInSideframe').and.returnValue(false);
            $('<div id="branding" style="height: 200px"></div>').prependTo(sticky.ui.container);
            expect(sticky.toolbarHeight).toEqual(null);
            sticky._saveSizes();
            expect(sticky.toolbarHeight).toEqual(200);
        });

        it('saves toolbar height if in sideframe', function() {
            spyOn(sticky, '_isInSideframe').and.returnValue(true);
            CMS.API.Helpers._getWindow.and.returnValue({
                parent: {
                    CMS: CMS
                }
            });
            $('<div class="cms-toolbar" style="height: 250px"></div>').prependTo(sticky.ui.container);
            expect(sticky.toolbarHeight).toEqual(null);
            sticky._saveSizes();
            expect(sticky.toolbarHeight).toEqual(250);
        });
    });

    describe('_isInSideframe()', function() {
        it('returns true if we are in the sideframe', function() {
            CMS.API.Helpers._getWindow.and.returnValue({
                parent: {
                    CMS: CMS
                }
            });
            expect(sticky._isInSideframe()).toEqual(true);
        });

        it('returns false if not', function() {
            expect(sticky._isInSideframe()).toEqual(false);
        });
    });

    describe('_events()', function() {
        it('attaches events', function() {
            sticky.ui.window.off('resize scroll');
            spyOn(sticky, '_handleResizeOrScroll');
            expect(sticky.ui.window).not.toHandle(sticky.resize);
            expect(sticky.ui.window).not.toHandle(sticky.scroll);
            sticky._events();
            expect(sticky.ui.window).toHandle(sticky.resize);
            expect(sticky.ui.window).toHandle(sticky.scroll);

            sticky.ui.window.trigger(sticky.resize);
            expect(sticky._handleResizeOrScroll).toHaveBeenCalledTimes(1);
            sticky.ui.window.trigger(sticky.scroll);
            expect(sticky._handleResizeOrScroll).toHaveBeenCalledTimes(2);
        });
    });

    describe('_handleResizeOrScroll()', function() {
        beforeEach(function() {
            spyOn(sticky, '_stickHeader');
            spyOn(sticky, '_unstickHeader');
        });

        it('sticks headers based on scroll position', function() {
            spyOn(sticky, '_shouldStick').and.returnValue(true);

            sticky._handleResizeOrScroll();
            expect(sticky._stickHeader).toHaveBeenCalledTimes(1);
            expect(sticky._stickHeader).toHaveBeenCalledWith(jasmine.any(Number), 0);
            expect(sticky._unstickHeader).not.toHaveBeenCalled();
        });

        it('unsticks headers based on scroll position', function() {
            spyOn(sticky, '_shouldStick').and.returnValue(false);

            sticky._handleResizeOrScroll();
            expect(sticky._unstickHeader).toHaveBeenCalledTimes(1);
            expect(sticky._unstickHeader).toHaveBeenCalledWith();
            expect(sticky._stickHeader).not.toHaveBeenCalled();
        });
    });

    describe('_shouldStick()', function() {
        it('returns true/false if headers should stick or not', function() {
            sticky.toolbarHeight = 10;
            sticky.headersTopOffset = 100;
            expect(sticky._shouldStick(90)).toEqual(true);
            expect(sticky._shouldStick(91)).toEqual(true);
            expect(sticky._shouldStick(9000)).toEqual(true);
            expect(sticky._shouldStick(89)).toEqual(false);
            expect(sticky._shouldStick(0)).toEqual(false);
        });
    });

    describe('_stickHeader()', function() {
        it('inserts clones', function() {
            spyOn(sticky, '_insertClones');
            expect(sticky._insertClones).not.toHaveBeenCalled();
            sticky._stickHeader();
            expect(sticky._insertClones).toHaveBeenCalledTimes(1);
        });

        it('updates widths/left/top for the headers', function() {
            sticky.toolbarHeight = 218;
            spyOn($.fn, 'css').and.callThrough();
            spyOn($.fn, 'offset').and.returnValue({
                left: 0
            });
            sticky._stickHeader(10, -10);

            expect($.fn.css).toHaveBeenCalledTimes(2 * 2 + 1);
            expect($.fn.css).toHaveBeenCalledWith('width'); // gets
            expect($.fn.css).toHaveBeenCalledWith({
                width: '100px',
                left: 10
            });
            expect($.fn.css).toHaveBeenCalledWith({
                width: '200px',
                left: 10
            });
            expect($.fn.css).toHaveBeenCalledWith({
                width: '200px',
                left: 10
            });
            expect($.fn.css).toHaveBeenCalledWith({
                top: 218
            });
        });

        it('adds a class to the headers', function() {
            expect(header1).not.toHaveClass('jstree-grid-header-fixed');
            expect(header2).not.toHaveClass('jstree-grid-header-fixed');
            sticky._stickHeader(10, -10);
            expect(header1).toHaveClass('jstree-grid-header-fixed');
            expect(header2).toHaveClass('jstree-grid-header-fixed');
        });
    });

    describe('_unstickHeader()', function() {
        it('detaches clones', function() {
            spyOn(sticky, '_detachClones');
            sticky._unstickHeader();
            expect(sticky._detachClones).toHaveBeenCalledTimes(1);
        });

        it('resets top, left and width', function() {
            spyOn($.fn, 'css');
            sticky._unstickHeader();
            expect($.fn.css).toHaveBeenCalledTimes(1);
            expect($.fn.css).toHaveBeenCalledWith({
                top: 0,
                width: 'auto',
                left: 'auto'
            });
        });

        it('removes a class', function() {
            sticky._stickHeader(0, 0);
            expect(header1).toHaveClass('jstree-grid-header-fixed');
            expect(header2).toHaveClass('jstree-grid-header-fixed');
            sticky._unstickHeader();
            expect(header1).not.toHaveClass('jstree-grid-header-fixed');
            expect(header2).not.toHaveClass('jstree-grid-header-fixed');
        });
    });

    describe('_insertClones()', function() {
        it('inserts clones in DOM', function() {
            expect(col1.children().length).toEqual(1);
            expect(col2.children().length).toEqual(1);
            sticky._insertClones();
            expect(col1.children().length).toEqual(2);
            expect(col2.children().length).toEqual(2);
        });

        it('sets the flag that nodes are inserted', function() {
            expect(sticky.areClonesInDOM).toEqual(false);
            sticky._insertClones();
            expect(sticky.areClonesInDOM).toEqual(true);
        });

        it('noop if flag is already set', function() {
            sticky._insertClones();
            sticky._insertClones();
            expect(col1.children().length).toEqual(2);
            expect(col2.children().length).toEqual(2);
        });
    });

    describe('_detachClones()', function() {
        beforeEach(function() {
            sticky._insertClones();
        });

        it('removes clones from DOM', function() {
            expect(col1.children().length).toEqual(2);
            expect(col2.children().length).toEqual(2);
            sticky._detachClones();
            expect(col1.children().length).toEqual(1);
            expect(col2.children().length).toEqual(1);
        });

        it('sets the flag that nodes are not inserted', function() {
            expect(sticky.areClonesInDOM).toEqual(true);
            sticky._detachClones();
            expect(sticky.areClonesInDOM).toEqual(false);
        });

        it('noop if flag is already set', function() {
            sticky._detachClones();
            sticky._detachClones();
            expect(col1.children().length).toEqual(1);
            expect(col2.children().length).toEqual(1);
        });
    });
});

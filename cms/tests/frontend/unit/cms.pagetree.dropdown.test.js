/* global document */
'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var PageTreeDropdowns = require('../../../static/cms/js/modules/cms.pagetree.dropdown').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.PageTreeDropdowns = PageTreeDropdowns;


describe('CMS.PageTreeDropdowns', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a PageTreeDropdown class', function () {
        expect(CMS.PageTreeDropdowns).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.PageTreeDropdowns.prototype.closeAllDropdowns).toEqual(jasmine.any(Function));
    });

    it('has default options', function () {
        expect(CMS.PageTreeDropdowns.prototype.options).toEqual({
            dropdownSelector: '.js-cms-pagetree-dropdown',
            triggerSelector: '.js-cms-pagetree-dropdown-trigger',
            menuSelector: '.js-cms-pagetree-dropdown-menu',
            openCls: 'cms-pagetree-dropdown-menu-open'
        });
    });

    describe('instance', function () {
        var dropdowns;

        beforeEach(function (done) {
            fixture.load('pagetree.html');

            $(function () {
                dropdowns = new CMS.PageTreeDropdowns({
                    container: $('.cms-pagetree')
                });
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('has ui', function () {
            expect(dropdowns.ui).toEqual({
                container: $('.cms-pagetree'),
                document: $(document)
            });
        });
    });

    describe('_events()', function () {
        var dropdowns;

        beforeEach(function (done) {
            fixture.load('pagetree.html');

            $(function () {
                dropdowns = new CMS.PageTreeDropdowns({
                    container: $('.cms-pagetree')
                });
                spyOn(dropdowns, '_toggleDropdown');
                spyOn(dropdowns, 'closeAllDropdowns');
                spyOn($.Event.prototype, 'preventDefault').and.callThrough();
                spyOn($.Event.prototype, 'stopImmediatePropagation').and.callThrough();
                done();
            });
        });

        afterEach(function () {
            dropdowns.ui.document.off(dropdowns.click);
            fixture.cleanup();
        });

        it('adds event handlers necessary to toggle dropdowns', function () {
            dropdowns.ui.container.off(dropdowns.click);
            expect(dropdowns.ui.container).not.toHandle(dropdowns.click);
            dropdowns._events();
            expect(dropdowns.ui.container).toHandle(dropdowns.click);
        });

        it('adds event handlers necessary to close dropdowns', function () {
            dropdowns.ui.document.off(dropdowns.click);
            expect(dropdowns.ui.document).not.toHandle(dropdowns.click);
            dropdowns._events();
            expect(dropdowns.ui.document).toHandle(dropdowns.click);
        });

        it('sets events on triggers that toggle dropdown', function () {
            var trigger = $('<div class="js-cms-pagetree-dropdown-trigger"></div>');
            dropdowns.ui.container.append(trigger);

            trigger.trigger(dropdowns.click);

            expect($.Event.prototype.preventDefault).toHaveBeenCalledTimes(1);
            expect($.Event.prototype.stopImmediatePropagation).toHaveBeenCalledTimes(1);
            expect(dropdowns._toggleDropdown).toHaveBeenCalledTimes(1);
            expect(dropdowns._toggleDropdown).toHaveBeenCalledWith(trigger[0]);
            expect(dropdowns.closeAllDropdowns).not.toHaveBeenCalled();
        });

        it('sets events on menus that stop propagation', function () {
            var menu = $('<div class="js-cms-pagetree-dropdown-menu"></div>');
            dropdowns.ui.container.append(menu);

            menu.trigger(dropdowns.click);

            expect($.Event.prototype.preventDefault).not.toHaveBeenCalled();
            expect($.Event.prototype.stopImmediatePropagation).toHaveBeenCalledTimes(1);
            expect(dropdowns._toggleDropdown).not.toHaveBeenCalled();
            expect(dropdowns.closeAllDropdowns).not.toHaveBeenCalled();
        });

        it('sets events on menus item links that close all dropdowns', function () {
            var menu = $('<div class="js-cms-pagetree-dropdown-menu"><a></a></div>');
            var link = menu.find('a');
            dropdowns.ui.container.append(menu);

            link.trigger(dropdowns.click);

            expect($.Event.prototype.preventDefault).not.toHaveBeenCalled();
            expect($.Event.prototype.stopImmediatePropagation).toHaveBeenCalledTimes(1);
            expect(dropdowns._toggleDropdown).not.toHaveBeenCalled();
            expect(dropdowns.closeAllDropdowns).toHaveBeenCalledTimes(1);
        });

        it('sets event on document that closes all dropdowns', function () {
            dropdowns.ui.document.trigger(dropdowns.click);

            expect($.Event.prototype.preventDefault).not.toHaveBeenCalled();
            expect($.Event.prototype.stopImmediatePropagation).not.toHaveBeenCalled();
            expect(dropdowns._toggleDropdown).not.toHaveBeenCalled();
            expect(dropdowns.closeAllDropdowns).toHaveBeenCalledTimes(1);
        });
    });

    describe('_toggleDropdown()', function () {
        var dropdowns;
        var trigger1;
        var trigger2;
        var menu1;
        var menu2;

        beforeEach(function (done) {
            fixture.load('pagetree.html');

            $(function () {
                trigger1 = $('<div class="js-cms-pagetree-dropdown-trigger"></div>');
                trigger2 = $('<div class="js-cms-pagetree-dropdown-trigger"></div>');
                menu1 = $('<div class="js-cms-pagetree-dropdown"></div>');
                menu2 = $('<div class="js-cms-pagetree-dropdown"></div>');

                dropdowns = new CMS.PageTreeDropdowns({
                    container: $('.cms-pagetree')
                });
                dropdowns.ui.container.append(menu1);
                dropdowns.ui.container.append(menu2);
                menu1.append(trigger1);
                menu2.append(trigger2);
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('closes the dropdown if it is already open', function () {
            spyOn($.fn, 'is').and.returnValue(true);
            menu1.addClass(dropdowns.options.openCls);
            menu2.addClass(dropdowns.options.openCls);

            expect(dropdowns._toggleDropdown(trigger1)).toEqual(false);
            expect(menu1).not.toHaveClass(dropdowns.options.openCls);
            expect(menu2).not.toHaveClass(dropdowns.options.openCls);
        });

        it('closes all other dropdowns if not already open', function () {
            spyOn($.fn, 'is').and.returnValue(false);
            menu2.addClass(dropdowns.options.openCls);

            expect(dropdowns._toggleDropdown(trigger1)).toEqual(undefined);
            expect(menu2).not.toHaveClass(dropdowns.options.openCls);
        });
        it('opens the dropdown', function () {
            spyOn($.fn, 'is').and.returnValue(false);

            expect(dropdowns._toggleDropdown(trigger1)).toEqual(undefined);
            expect(menu1).toHaveClass(dropdowns.options.openCls);
        });
    });

    describe('closeAllDropdowns()', function () {
        var dropdowns;

        beforeEach(function (done) {
            fixture.load('pagetree.html');

            $(function () {
                dropdowns = new CMS.PageTreeDropdowns({
                    container: $('.cms-pagetree')
                });
                dropdowns.ui.container.append(
                    '<div ' +
                        'class="js-cms-pagetree-dropdown cms-pagetree-dropdown ' +
                        dropdowns.options.openCls + '"></div>'
                );
                done();
            });
        });

        afterEach(function () {
            fixture.cleanup();
        });

        it('closes all dropdowns', function () {
            expect(dropdowns.ui.container.find(dropdowns.options.dropdownSelector))
                .toHaveClass(dropdowns.options.openCls);
            dropdowns.closeAllDropdowns();
            expect(dropdowns.ui.container.find(dropdowns.options.dropdownSelector))
                .not.toHaveClass(dropdowns.options.openCls);
        });
    });
});

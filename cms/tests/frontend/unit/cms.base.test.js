'use strict';

import CMS, { Helpers, KEYS, uid } from '../../../static/cms/js/modules/cms.base';
var jQuery = require('jquery');
var $ = jQuery;
var Class = require('classjs');
var showLoader;
var hideLoader;

CMS.API.Helpers = Helpers;
CMS.KEYS = KEYS;
CMS.Class = Class;

window.CMS = window.CMS || CMS;

describe('cms.base.js', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    // same implementation as in CMS.API.Helpers._isStorageSupported
    var _isLocalStorageSupported = (function() {
        var mod = 'modernizr';
        try {
            localStorage.setItem(mod, mod);
            localStorage.removeItem(mod);
            return true;
        } catch (e) {
            // istanbul ignore next
            return false;
        }
    })();

    beforeEach(() => {
        showLoader = jasmine.createSpy();
        hideLoader = jasmine.createSpy();
        CMS.__Rewire__('showLoader', showLoader);
        CMS.__Rewire__('hideLoader', hideLoader);
    });

    afterEach(() => {
        CMS.__ResetDependency__('showLoader');
        CMS.__ResetDependency__('hideLoader');
    });

    it('creates CMS namespace', function() {
        expect(CMS).toBeDefined();
        expect(CMS).toEqual(jasmine.any(Object));
        expect(CMS.API).toEqual(jasmine.any(Object));
        expect(KEYS).toEqual(jasmine.any(Object));
    });

    describe('CMS.API', function() {
        it('exists', function() {
            expect(CMS.API.Helpers).toEqual(jasmine.any(Object));
            // this expectation is here so no one ever forgets to add a test
            expect(Object.keys(CMS.API.Helpers).length).toEqual(26);
        });

        describe('.reloadBrowser()', function() {
            /**
             * @function createFakeWindow
             * @returns {Object}
             */
            function createFakeWindow() {
                return {
                    parent: {
                        location: {
                            href: '',
                            reload: jasmine.createSpy()
                        },
                        CMS: {
                            config: {
                                request: {
                                    model: 'model',
                                    pk: 'pk'
                                }
                            },
                            API: {}
                        },
                        setTimeout: jasmine.createSpy().and.callFake(function(cb, timeout) {
                            expect(timeout).toEqual(0);
                            cb();
                        })
                    }
                };
            }
            /**
             * @function createWindowSpy
             * @param {Object} win
             */
            function createWindowSpy(win) {
                spyOn(CMS.API.Helpers, '_getWindow').and.callFake(function() {
                    return win;
                });
            }

            it('reloads the browser if no `ajax` and `url` was passed', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                CMS.API.Helpers.reloadBrowser(false, false, false);

                expect(win.parent.location.reload).toHaveBeenCalled();
            });

            it('redirects the browser to an url if no `ajax`, but `url` was passed', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                CMS.API.Helpers.reloadBrowser('/url', false, false);

                expect(win.parent.location.href).toEqual('/url');
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('makes a request when `ajax` and `url` is passed', function() {
                var win = createFakeWindow();
                $.extend(true, win, {
                    parent: {
                        CMS: {
                            config: {
                                request: {
                                    url: '/my-url'
                                }
                            }
                        }
                    }
                });
                createWindowSpy(win);
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('');
                });

                expect(CMS.API.Helpers.reloadBrowser('/url', false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                // console.log(JSON.stringify(win.parent, null, 4));
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('calls itself with the url if `ajax` and `url` is passed', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('');
                });

                expect(CMS.API.Helpers.reloadBrowser('/url', false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(2);
                expect(CMS.API.Helpers.reloadBrowser.calls.mostRecent().args).toEqual(['/url']);
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('does nothing if `ajax` is passed but `url` is not and response from server is empty', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('');
                });

                expect(CMS.API.Helpers.reloadBrowser(false, false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(1);
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('calls itself with the url that comes from server if `ajax` and `url` is passed', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('/url-from-server');
                });

                expect(CMS.API.Helpers.reloadBrowser('/url', false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(2);
                expect(CMS.API.Helpers.reloadBrowser.calls.mostRecent().args).toEqual(['/url-from-server']);
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('calls itself with the url that comes from server if `ajax` is passed and `url` is not', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('/url-from-server');
                });

                expect(CMS.API.Helpers.reloadBrowser(false, false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(2);
                expect(CMS.API.Helpers.reloadBrowser.calls.mostRecent().args).toEqual(['/url-from-server']);
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).not.toHaveBeenCalled();
            });

            it('calls itself if url is REFRESH_PAGE and there is no response from server', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('');
                });

                expect(CMS.API.Helpers.reloadBrowser('REFRESH_PAGE', false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(2);
                expect(CMS.API.Helpers.reloadBrowser.calls.mostRecent().args).toEqual([]);
                expect(win.parent.CMS.API.locked).toEqual(false);
                expect(win.parent.location.reload).toHaveBeenCalled();
            });

            it('does not call itself if there is no url and response matches current location', function() {
                var win = createFakeWindow();
                win = $.extend(true, {}, win, win.parent);
                win.parent = false;
                createWindowSpy(win);
                win.CMS.config.request.url = '/my-url';
                win.location.pathname = '/something';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('/something');
                });

                expect(CMS.API.Helpers.reloadBrowser(false, false, true)).toEqual(false);
                expect($.ajax).toHaveBeenCalledWith(
                    jasmine.objectContaining({
                        type: 'GET',
                        async: false,
                        url: '/my-url',
                        data: {
                            model: 'model',
                            pk: 'pk'
                        }
                    })
                );

                expect(CMS.API.Helpers.reloadBrowser.calls.count()).toEqual(1);
                expect(CMS.API.Helpers.reloadBrowser.calls.mostRecent().args).toEqual([false, false, true]);
                expect(win.CMS.API.locked).toEqual(false);
                expect(win.location.reload).not.toHaveBeenCalled();
            });

            it('uses correct timeout', function() {
                var win = createFakeWindow();
                createWindowSpy(win);
                win.parent.CMS.config.request.url = '/my-url';
                spyOn(CMS.API.Helpers, 'reloadBrowser').and.callThrough();
                win.parent.setTimeout = jasmine.createSpy().and.callFake(function(cb, timeout) {
                    expect(timeout).toEqual(50);
                    cb();
                });
                // for some reason jasmine.Ajax.install() didn't work here
                // presumably because of window.parent shenanigans.
                spyOn($, 'ajax').and.callFake(function(opts) {
                    opts.success('');
                });

                expect(CMS.API.Helpers.reloadBrowser('/new-url', 50, false)).toEqual(undefined);
                expect($.ajax).not.toHaveBeenCalled();
                expect(win.parent.location.href).toEqual('/new-url');
            });
        });

        describe('onPluginSave()', function() {
            beforeEach(() => {
                CMS.API.StructureBoard = {
                    invalidateState: jasmine.createSpy()
                };
            });
            afterEach(() => {
                CMS.API.Helpers.dataBridge = null;
            });

            it('invalidates state if the plugin was edited', () => {
                CMS._instances = [{ options: { plugin_id: 1, type: 'plugin' } }];

                CMS.API.Helpers.dataBridge = { plugin_id: '1' };
                CMS.API.Helpers.onPluginSave();
                expect(CMS.API.StructureBoard.invalidateState).toHaveBeenCalledWith('EDIT', { plugin_id: '1' });
            });

            it('invalidates state if the plugin was added', () => {
                CMS._instances = [];

                CMS.API.Helpers.dataBridge = { plugin_id: '1' };
                CMS.API.Helpers.onPluginSave();
                expect(CMS.API.StructureBoard.invalidateState).toHaveBeenCalledWith('ADD', { plugin_id: '1' });
            });

            it('invalidates state if the plugin was added', () => {
                CMS._instances = [{ options: { plugin_id: 1, type: 'generic' } }];

                CMS.API.Helpers.dataBridge = { plugin_id: '1' };
                CMS.API.Helpers.onPluginSave();
                expect(CMS.API.StructureBoard.invalidateState).toHaveBeenCalledWith('ADD', { plugin_id: '1' });
            });

            it('proxies to reloadBrowser', function() {
                spyOn(CMS.API.Helpers, 'reloadBrowser');

                CMS.API.Helpers._isReloading = false;

                CMS.API.Helpers.onPluginSave();
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledTimes(1);
                expect(CMS.API.Helpers.reloadBrowser).toHaveBeenCalledWith(null, 300);
            });
        });

        describe('.preventSubmit()', function() {
            beforeEach(function(done) {
                fixture.load('toolbar_form.html');
                $(function() {
                    done();
                });
            });

            afterEach(function() {
                fixture.cleanup();
            });

            it('should prevent forms from being submitted when one form is submitted', function() {
                var submitCallback = jasmine.createSpy().and.returnValue(false);

                CMS.API.Helpers.preventSubmit();
                var form = $('.cms-toolbar #form1');
                var input1 = $('input[type=submit]').eq(0);
                var input2 = $('input[type=submit]').eq(1);
                form.submit(submitCallback);
                form.find('input').trigger('click');

                expect(input1).toHaveCss({ opacity: '0.5' });
                expect(input2).toHaveCss({ opacity: '0.5' });

                spyOnEvent(input1, 'click');
                spyOnEvent(input2, 'click');

                input1.trigger('click');
                input2.trigger('click');

                expect('click').toHaveBeenPreventedOn(input1);
                expect('click').toHaveBeenPreventedOn(input2);
                expect(showLoader).toHaveBeenCalled();
                expect(submitCallback).toHaveBeenCalled();
            });
        });

        describe('.csrf()', function() {
            it('should set csrf token on ajax requests', function() {
                var token = 'csrf';
                var request;

                jasmine.Ajax.install();
                $.ajax('/test');
                request = jasmine.Ajax.requests.mostRecent();
                expect(request.requestHeaders['X-CSRFToken']).toEqual(undefined);

                spyOn($, 'ajaxSetup').and.callThrough();
                CMS.API.Helpers.csrf(token);
                expect($.ajaxSetup).toHaveBeenCalled();
                expect($.ajaxSetup.calls.count()).toEqual(1);

                $.ajax('/test');
                request = jasmine.Ajax.requests.mostRecent();
                expect(request.requestHeaders['X-CSRFToken']).toEqual(token);
                jasmine.Ajax.uninstall();
            });
        });

        describe('.setSettings()', function() {
            beforeEach(function() {
                CMS.API.Helpers._isStorageSupported = true;
                if (_isLocalStorageSupported) {
                    localStorage.clear();
                }
                jasmine.Ajax.install();

                jasmine.Ajax.stubRequest('/my-settings-url').andReturn({
                    status: 200,
                    contentType: 'text/plain',
                    responseText: '{"serverSetting":true,"version":"same"}'
                });

                jasmine.Ajax.stubRequest('/my-settings-url-with-empty-response').andReturn({
                    status: 200,
                    contentType: 'text/plain',
                    responseText: ''
                });

                jasmine.Ajax.stubRequest('/my-settings-url').andReturn({
                    status: 200,
                    contentType: 'text/plain',
                    responseText: '{"serverSetting":true}'
                });

                jasmine.Ajax.stubRequest('/my-broken-settings-url').andReturn({
                    status: 500,
                    responseText: 'Fail'
                });
            });

            afterEach(function() {
                jasmine.Ajax.uninstall();
            });

            it('should put settings in localStorage if it is available', function() {
                if (!_isLocalStorageSupported) {
                    pending('Localstorage is not supported, skipping');
                }

                CMS.config = {
                    settings: {}
                };

                expect(CMS.API.Helpers.setSettings({ mySetting: true })).toEqual({ mySetting: true });
                expect(localStorage.getItem('cms_cookie')).toEqual('{"mySetting":true}');

                CMS.config.settings = { mySetting: false };
                expect(CMS.API.Helpers.setSettings({ anotherSetting: true })).toEqual({
                    mySetting: false,
                    anotherSetting: true
                });
                expect(localStorage.getItem('cms_cookie')).toEqual('{"mySetting":false,"anotherSetting":true}');

                expect(CMS.API.Helpers.setSettings({ mySetting: true })).toEqual({
                    mySetting: true
                });
                expect(localStorage.getItem('cms_cookie')).toEqual('{"mySetting":true}');
            });

            it('makes a synchronous request to the session url if localStorage is not available', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    urls: {
                        settings: '/my-settings-url'
                    }
                };
                expect(CMS.API.Helpers.setSettings({ mySetting: true })).toEqual({ serverSetting: true });

                expect(showLoader.calls.count()).toEqual(1);
                expect(hideLoader.calls.count()).toEqual(1);
            });

            it('uses default settings if response is empty', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    settings: {
                        defaultSetting: true
                    },
                    urls: {
                        settings: '/my-settings-url-with-empty-response'
                    }
                };

                expect(CMS.API.Helpers.setSettings({ mySetting: true })).toEqual({ defaultSetting: true });

                expect(showLoader.calls.count()).toEqual(1);
                expect(hideLoader.calls.count()).toEqual(1);
            });

            it('makes a synchronous request which can fail', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    urls: {
                        settings: '/my-broken-settings-url'
                    }
                };
                CMS.API.Messages = {
                    open: jasmine.createSpy()
                };

                expect(CMS.API.Helpers.setSettings({ mySetting: true })).toEqual({ mySetting: true });

                expect(showLoader).toHaveBeenCalled();
                expect(hideLoader).not.toHaveBeenCalled();
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                    message: 'Fail | 500 error',
                    error: true
                });
            });
        });

        describe('.getSettings()', function() {
            beforeEach(function() {
                CMS.API.Helpers._isStorageSupported = true;
                if (_isLocalStorageSupported) {
                    localStorage.clear();
                }
                jasmine.Ajax.install();

                jasmine.Ajax.stubRequest('/my-settings-url-with-empty-response').andReturn({
                    status: 200,
                    contentType: 'text/plain',
                    responseText: ''
                });

                jasmine.Ajax.stubRequest('/my-settings-url').andReturn({
                    status: 200,
                    contentType: 'text/plain',
                    responseText: `{"serverSetting":true,"version":"${__CMS_VERSION__}","edit_off":1}`
                });

                jasmine.Ajax.stubRequest('/my-broken-settings-url').andReturn({
                    status: 500,
                    responseText: 'Fail'
                });
            });

            afterEach(function() {
                jasmine.Ajax.uninstall();
            });

            it('should get settings from localStorage', function() {
                if (!_isLocalStorageSupported) {
                    pending('Localstorage is not supported, skipping');
                }

                localStorage.setItem(
                    'cms_cookie',
                    JSON.stringify({ version: __CMS_VERSION__, presetSetting: true, edit_off: 1 })
                );
                CMS.settings = {};
                CMS.config = {
                    settings: {
                        version: __CMS_VERSION__
                    }
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({
                    presetSetting: true,
                    version: __CMS_VERSION__,
                    edit_off: 1
                });

                expect(showLoader.calls.count()).toEqual(0);
                expect(hideLoader.calls.count()).toEqual(0);
            });

            it('should get settings from config if there is a version mismatch', function() {
                if (!_isLocalStorageSupported) {
                    pending('Localstorage is not supported, skipping');
                }

                localStorage.setItem(
                    'cms_cookie',
                    JSON.stringify({ version: 'old', presetSetting: true, edit_off: 1 })
                );
                CMS.settings = {};
                CMS.config = {
                    settings: {
                        version: 'new',
                        other_stuff: true
                    }
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({ version: 'new', other_stuff: true });

                expect(showLoader.calls.count()).toEqual(0);
                expect(hideLoader.calls.count()).toEqual(0);
            });

            it('should get settings from localStorage and cms.config if required settings are not there', function() {
                if (!_isLocalStorageSupported) {
                    pending('Localstorage is not supported, skipping');
                }

                localStorage.setItem('cms_cookie', JSON.stringify({ presetSetting: true }));
                CMS.settings = {};
                CMS.config = {
                    settings: {
                        fromConfig: true
                    }
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({ fromConfig: true });

                expect(showLoader.calls.count()).toEqual(0);
                expect(hideLoader.calls.count()).toEqual(0);
            });

            it('should first set settings from CMS.config is there are no settings in localstorage', function() {
                if (!_isLocalStorageSupported) {
                    pending('Localstorage is not supported, skipping');
                }

                CMS.settings = {};
                CMS.config = {
                    settings: {
                        configSetting: true
                    }
                };
                spyOn(CMS.API.Helpers, 'setSettings').and.callThrough();

                expect(CMS.API.Helpers.getSettings()).toEqual({ configSetting: true });

                expect(showLoader.calls.count()).toEqual(0);
                expect(hideLoader.calls.count()).toEqual(0);
                expect(CMS.API.Helpers.setSettings).toHaveBeenCalled();
            });

            it('makes a synchronous request to the session url if localStorage is not available', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    settings: {
                        version: __CMS_VERSION__
                    },
                    urls: {
                        settings: '/my-settings-url'
                    }
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({
                    version: __CMS_VERSION__,
                    serverSetting: true,
                    edit_off: 1
                });

                expect(showLoader.calls.count()).toEqual(1);
                expect(hideLoader.calls.count()).toEqual(1);
            });

            it('uses default settings if response is empty', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    settings: {
                        defaultSetting: true
                    },
                    urls: {
                        settings: '/my-settings-url-with-empty-response'
                    }
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({ defaultSetting: true });

                expect(showLoader.calls.count()).toEqual(2);
                expect(hideLoader.calls.count()).toEqual(2);
            });

            it('makes a synchronous request which can fail', function() {
                CMS.API.Helpers._isStorageSupported = false;
                CMS.config = {
                    settings: { test: false },
                    urls: {
                        settings: '/my-broken-settings-url'
                    }
                };
                CMS.API.Messages = {
                    open: jasmine.createSpy()
                };

                expect(CMS.API.Helpers.getSettings()).toEqual({ test: false });

                expect(showLoader).toHaveBeenCalled();
                expect(hideLoader).not.toHaveBeenCalled();
                expect(CMS.API.Messages.open).toHaveBeenCalledWith({
                    message: 'Fail | 500 error',
                    error: true
                });
            });
        });

        describe('.makeURL()', function() {
            it('outputs the same url when no additional params passed', function() {
                var url;
                url = CMS.API.Helpers.makeURL('test');
                expect(url).toEqual('test');

                url = CMS.API.Helpers.makeURL('https://google.com/');
                expect(url).toEqual('https://google.com/');
            });

            it('outputs new url when additional params passed', function() {
                var url;

                url = CMS.API.Helpers.makeURL('test', [['param', '1']]);
                expect(url).toEqual('test?param=1');
            });

            it('outputs new url when there are multiple additional params', function() {
                var url;

                url = CMS.API.Helpers.makeURL('test', [['param', '1'], ['another', '2']]);
                expect(url).toEqual('test?param=1&another=2');

                url = CMS.API.Helpers.makeURL('test?param=1', [['another', '2']]);
                expect(url).toEqual('test?param=1&another=2');

                url = CMS.API.Helpers.makeURL('test?param=1&another=2', [['different', '3']]);
                expect(url).toEqual('test?param=1&another=2&different=3');

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', [['different', '3']]);
                expect(url).toEqual('test?param=1&another=2&different=3');

                url = CMS.API.Helpers.makeURL('test?param=1&another=2&amp;again=3', [['different', '3']]);
                expect(url).toEqual('test?param=1&another=2&again=3&different=3');
            });

            it('replaces param values with new ones if they match', function() {
                var url;

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', [['another', '3']]);
                expect(url).toEqual('test?param=1&another=3');

                url = CMS.API.Helpers.makeURL('test?param=1&amp;another=2', [['another', '3'], ['param', '4']]);
                expect(url).toEqual('test?another=3&param=4');
            });

            it('understands hashes in the url', function() {
                var url;

                url = CMS.API.Helpers.makeURL('test#hash', [['param', '1'], ['another', '2']]);
                expect(url).toEqual('test?param=1&another=2#hash');

                url = CMS.API.Helpers.makeURL('test#hash#with#hash', [['param', '1'], ['another', '2']]);
                expect(url).toEqual('test?param=1&another=2#hash#with#hash');

                url = CMS.API.Helpers.makeURL('test#', [['param', '1'], ['another', '2']]);
                expect(url).toEqual('test?param=1&another=2');

                url = CMS.API.Helpers.makeURL('test#hash&stuff', [['param', '1'], ['another', '2']]);
                expect(url).toEqual('test?param=1&another=2#hash&stuff');

                url = CMS.API.Helpers.makeURL('test#hash&stuff', []);
                expect(url).toEqual('test#hash&stuff');
            });
        });

        describe('.secureConfirm()', function() {
            it('returns true if confirm is prevented', function() {
                spyOn(window, 'confirm').and.callFake(function(message) {
                    expect(message).toEqual('message');
                    return false;
                });
                expect(CMS.API.Helpers.secureConfirm('message')).toEqual(true);
            });

            it('returns actual value if confirm is not prevented', function() {
                jasmine.clock().install();
                jasmine.clock().mockDate();
                spyOn(window, 'confirm').and.callFake(function() {
                    jasmine.clock().tick(15);
                    return false;
                });

                expect(CMS.API.Helpers.secureConfirm('cms')).toEqual(false);

                window.confirm.and.callFake(function() {
                    jasmine.clock().tick(15);
                    return true;
                });

                expect(CMS.API.Helpers.secureConfirm('cms')).toEqual(true);

                jasmine.clock().uninstall();
            });
        });

        describe('.addEventListener()', function() {
            beforeEach(function(done) {
                fixture.load('cms_root.html');
                $(function() {
                    done();
                });
            });

            afterEach(function() {
                fixture.cleanup();
            });

            it('adds an event', function() {
                CMS._eventRoot = $('#cms-top');
                CMS.API.Helpers.addEventListener('my-event', $.noop);

                expect($('#cms-top')).toHandle('cms-my-event');
            });
            it('adds multiple events', function() {
                CMS._eventRoot = $('#cms-top');
                CMS.API.Helpers.addEventListener('my-event my-other-event', $.noop);

                expect($('#cms-top')).toHandle('cms-my-event');
                expect($('#cms-top')).toHandle('cms-my-other-event');
            });
        });

        describe('.removeEventListener()', function() {
            beforeEach(function(done) {
                fixture.load('cms_root.html');
                $(function() {
                    done();
                });
            });

            afterEach(function() {
                fixture.cleanup();
            });
            it('removes an event', function() {
                CMS._eventRoot = $('#cms-top');

                CMS.API.Helpers.addEventListener('my-event', $.noop);
                CMS.API.Helpers.removeEventListener('my-event');

                expect($('#cms-top')).not.toHandle('cms-my-event');
            });

            it('removes an event with correct handler', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = function() {
                    expect(true).toEqual(true);
                };

                CMS.API.Helpers.addEventListener('my-event', $.noop);
                CMS.API.Helpers.addEventListener('my-event', fn);
                CMS.API.Helpers.removeEventListener('my-event', $.noop);

                expect($('#cms-top')).toHandleWith('cms-my-event', fn);
                expect($('#cms-top')).not.toHandleWith('cms-my-event', $.noop);
            });

            it('removes multiple events', function() {
                CMS._eventRoot = $('#cms-top');

                CMS.API.Helpers.addEventListener('my-event my-other-event', $.noop);
                CMS.API.Helpers.removeEventListener('my-event my-other-event');

                expect($('#cms-top')).not.toHandle('cms-my-event');
                expect($('#cms-top')).not.toHandle('cms-my-other-event');
            });
        });

        describe('.dispatchEvent()', function() {
            beforeEach(function(done) {
                fixture.load('cms_root.html');
                $(function() {
                    done();
                });
            });

            afterEach(function() {
                fixture.cleanup();
            });
            it('dispatches an event', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = jasmine.createSpy();
                CMS.API.Helpers.addEventListener('my-event', fn);
                CMS.API.Helpers.dispatchEvent('my-event');
                expect(fn).toHaveBeenCalled();
            });

            it('does not dispatch multiple events', function() {
                CMS._eventRoot = $('#cms-top');
                var fn1 = jasmine.createSpy();
                var fn2 = jasmine.createSpy();

                CMS.API.Helpers.addEventListener('my-event', fn1);
                CMS.API.Helpers.addEventListener('my-another-event', fn2);
                CMS.API.Helpers.dispatchEvent('my-event my-another-event');
                expect(fn1).not.toHaveBeenCalled();
                expect(fn2).not.toHaveBeenCalled();
            });

            it('can attach payload to event', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = jasmine.createSpy();

                CMS.API.Helpers.addEventListener('my-event', fn);
                CMS.API.Helpers.dispatchEvent('my-event', {
                    payload: 'djangoCMS'
                });
                expect(fn).toHaveBeenCalledWith(jasmine.any(Object), {
                    payload: 'djangoCMS'
                });
            });

            it('returns dispatched event', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = jasmine.createSpy();

                CMS.API.Helpers.addEventListener('my-event', fn);
                expect(CMS.API.Helpers.dispatchEvent('my-event') instanceof $.Event).toEqual(true);
            });

            it('can has namespaces', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = jasmine.createSpy();

                CMS.API.Helpers.addEventListener('my-event.namespace', fn);
                CMS.API.Helpers.dispatchEvent('my-event', {
                    payload: 'djangoCMS'
                });
                expect(fn).toHaveBeenCalledWith(jasmine.any(Object), {
                    payload: 'djangoCMS'
                });
            });

            it('can has namespaces the other way', function() {
                CMS._eventRoot = $('#cms-top');
                var fn = jasmine.createSpy();

                CMS.API.Helpers.addEventListener('my-event', fn);
                CMS.API.Helpers.dispatchEvent('my-event.namespace', {
                    payload: 'djangoCMS'
                });
                expect(fn).not.toHaveBeenCalled();
            });
        });

        describe('.preventTouchScrolling()', function() {
            it('prevents touch move on an element', function() {
                CMS.API.Helpers.preventTouchScrolling($(document), 'tests');
                expect($(document)).toHandle('touchmove');
                expect($(document)).toHandle('touchmove.cms.preventscroll.tests');
                var event = spyOnEvent(document, 'touchmove');
                $(document).trigger('touchmove');
                expect(event).toHaveBeenPrevented();
            });
        });

        // depends on the previous one
        describe('.allowTouchScrolling()', function() {
            it('allows touch move on an element', function() {
                expect($(document)).toHandle('touchmove');
                expect($(document)).toHandle('touchmove.cms.preventscroll.tests');
                CMS.API.Helpers.allowTouchScrolling($(document), 'tests');
                var event = spyOnEvent(document, 'touchmove');
                $(document).trigger('touchmove');
                expect(event).not.toHaveBeenPrevented();
            });
        });

        describe('._getWindow()', function() {
            it('returns window', function() {
                expect(CMS.API.Helpers._getWindow()).toEqual(window);
            });
        });

        describe('.uid()', function() {
            it('returns a number', function() {
                expect(uid()).toEqual(jasmine.any(Number));
            });

            it('returns always different ids', function() {
                expect(uid()).not.toBe(uid());
            });
        });

        describe('.updateUrlWithPath()', function() {
            it('supports query strings', function() {
                spyOn(CMS.API.Helpers, '_getWindow').and.returnValue({
                    location: {
                        pathname: '/de/',
                        search: '?language=en'
                    }
                });

                expect(CMS.API.Helpers.updateUrlWithPath('/')).toEqual('/?cms_path=%2Fde%2F%3Flanguage%3Den');
            });
        });

        describe('.setColorScheme() and .getColorScheme()', function() {
            it('allows setting of dark color scheme', function() {
                CMS.API.Helpers.setColorScheme('dark');
                expect(CMS.API.Helpers.getColorScheme()).toEqual('dark');
            });
            it('allows setting of light color scheme', function() {
                CMS.API.Helpers.setColorScheme('light');
                expect(CMS.API.Helpers.getColorScheme()).toEqual('light');
            });
            it('allows setting of system color scheme', function() {
                CMS.API.Helpers.setColorScheme('auto');
                expect(CMS.API.Helpers.getColorScheme()).toEqual('auto');
            });
        });
    });
});

'use strict';
var CMS = require('../../../static/cms/js/modules/cms.base').default;
var Messages = require('../../../static/cms/js/modules/cms.messages').default;
var $ = require('jquery');

window.CMS = window.CMS || CMS;
CMS.Messages = Messages;

describe('CMS.Messages', function() {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Messages class', function() {
        expect(CMS.Messages).toBeDefined();
    });

    it('has public api', function() {
        expect(CMS.Messages.prototype.open).toEqual(jasmine.any(Function));
        expect(CMS.Messages.prototype.close).toEqual(jasmine.any(Function));
    });

    describe('instance', function() {
        var messages;
        beforeEach(function(done) {
            $(function() {
                messages = new CMS.Messages();
                done();
            });
        });

        it('has ui', function() {
            expect(messages.ui).toEqual(jasmine.any(Object));
            var keys = Object.keys(messages.ui);
            expect(keys).toContain('container');
            expect(keys).toContain('body');
            expect(keys).toContain('toolbar');
            expect(keys).toContain('messages');
            expect(keys.length).toEqual(4);
        });

        it('has options', function() {
            expect(messages.options).toEqual({
                messageDuration: 300,
                messageDelay: 3000
            });
            messages = new CMS.Messages({
                messageDuration: 100,
                messageDelay: 0
            });
            expect(messages.options).toEqual({
                messageDuration: 100,
                messageDelay: 0
            });
        });
    });

    describe('.open()', function() {
        var messages;
        beforeEach(function(done) {
            fixture.load('messages.html');
            CMS.config = {
                debug: false
            };
            CMS.settings = {
                toolbar: 'expanded'
            };
            $(function() {
                $('.cms-toolbar').css({ 'margin-top': 0 });
                messages = new CMS.Messages();
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });

        it('throws an error if message is not specified', function() {
            expect(messages.open).toThrowError(Error, 'The arguments passed to "open" were invalid.');
            expect(messages.open.bind(messages, { message: 'something' })).not.toThrow();
        });

        it('opens a message', function() {
            messages.open({ message: 'test message' });
            expect(messages.ui.messages.find('.cms-messages-inner')).toHaveText('test message');
            expect(messages.ui.messages).toBeVisible();

            messages.open({ message: '<strong>html</strong> message' });
            expect(messages.ui.messages.find('.cms-messages-inner')).toHaveText('html message');
            expect(messages.ui.messages.find('.cms-messages-inner')).toContainHtml('<strong>html</strong> message');
            expect(messages.ui.messages).toBeVisible();
        });

        it('adds correct styling if it is an error message', function() {
            messages.open({ message: 'error message', error: true });
            expect(messages.ui.messages.find('.cms-messages-inner')).toHaveText('error message');
            expect(messages.ui.messages).toBeVisible();
            expect(messages.ui.messages).toHaveClass('cms-messages-error');
        });

        it('positions message correctly', function() {
            // here we opt not to wait till the actual animation ends
            // simply to speed things up. otherwise for each test we would
            // need to wait ~650ms, since jQuery uses requestAnimationFrame
            // and it's problematic to mock it up
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                expect(opts).toEqual({
                    top: 46
                });
            });

            messages.open({ message: 'test message' });

            expect(messages.ui.messages).toHaveCss({
                'margin-left': '-160px'
            });
        });

        it('positions message correctly if debug toolbar is present', function() {
            CMS.config.debug = true;
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                // it uses same value, because toolbar itself
                // if using margin-top: 5px to move when debug is true
                expect(opts).toEqual({
                    top: 46
                });
            });

            messages.open({ message: 'test message' });

            expect(messages.ui.messages).toHaveCss({
                'margin-left': '-160px'
            });
        });

        it('positions message correctly if toolbar is collapsed', function() {
            $('.cms-toolbar').css('margin-top', '-56px');
            CMS.settings.toolbar = 'collapsed';
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                expect(opts).toEqual({
                    top: 0
                });
            });

            messages.open({ message: 'test message' });

            expect(messages.ui.messages).toHaveCss({
                'margin-left': '-160px'
            });
        });

        it('positions message correctly if direction is center', function() {
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                expect(opts).toEqual({
                    top: 46
                });
            });

            messages.open({ message: 'test message', dir: 'center' });

            expect(messages.ui.messages).toHaveCss({
                'margin-left': '-160px'
            });
        });

        it('positions message correctly if direction is left', function(done) {
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                expect(opts).toEqual({
                    left: 0
                });
            });

            messages.open({ message: 'test message', dir: 'left' });

            // setTimeout here is required because in some browsers
            // $.fn.css is not synchronous apparently
            setTimeout(function() {
                expect(messages.ui.messages).toHaveCss({
                    top: '46px',
                    'margin-left': '0px',
                    left: '-320px'
                });
                done();
            }, 300);
        });

        it('positions message correctly if direction is right', function(done) {
            spyOn($.fn, 'animate').and.callFake(function(opts) {
                expect(opts).toEqual({
                    right: 0
                });
            });

            messages.open({ message: 'test message', dir: 'right' });

            setTimeout(function() {
                expect(messages.ui.messages).toHaveCss({
                    top: '46px',
                    'margin-left': '0px',
                    right: '-320px',
                    left: 'auto'
                });
                done();
            }, 300);
        });

        it('hides a message automatically with a given delay', function() {
            jasmine.clock().install();
            spyOn(messages, 'close').and.callFake(function() {});

            messages.open({ message: 'test message' });

            jasmine.clock().tick(200);
            expect(messages.close).not.toHaveBeenCalled();

            jasmine.clock().tick(2801);
            expect(messages.close).toHaveBeenCalled();

            messages.close.calls.reset();

            messages.open({ message: 'slow message', delay: 10000 });
            jasmine.clock().tick(3000);
            expect(messages.close).not.toHaveBeenCalled();

            jasmine.clock().tick(7001);
            expect(messages.close).toHaveBeenCalled();

            jasmine.clock().uninstall();
        });

        it('hides a message automatically with a given delay', function() {
            jasmine.clock().install();
            messages = new CMS.Messages({ messageDelay: 200 });
            spyOn(messages, 'close').and.callFake(function() {});

            messages.open({ message: 'test message' });

            jasmine.clock().tick(100);
            expect(messages.close).not.toHaveBeenCalled();

            jasmine.clock().tick(101);
            expect(messages.close).toHaveBeenCalled();

            jasmine.clock().uninstall();
        });

        it('does not hide a message automatically if delay is 0', function() {
            jasmine.clock().install();
            messages = new CMS.Messages({ messageDelay: 0 });
            spyOn(messages, 'close').and.callFake(function() {});
            messages.open({ message: 'test message' });
            jasmine.clock().tick(10000);
            expect(messages.close).not.toHaveBeenCalled();
            jasmine.clock().uninstall();
        });

        it('shows close button if delay is 0', function() {
            jasmine.clock().install();
            messages = new CMS.Messages({ messageDelay: 0 });
            spyOn(messages, 'close').and.callFake(function() {});
            messages.open({ message: 'test message' });
            jasmine.clock().tick(10000);
            expect(messages.close).not.toHaveBeenCalled();
            expect(messages.ui.messages.find('.cms-messages-close')).toBeVisible();
            jasmine.clock().uninstall();
        });

        it('adds event listener to the close button', function() {
            messages = new CMS.Messages();
            var close = messages.ui.messages.find('.cms-messages-close');
            spyOn(messages, 'close').and.callFake(function() {});
            messages.open({ message: 'test message' });
            expect(close).toHandle('click');
            close.trigger('click');
            expect(messages.close).toHaveBeenCalled();
        });
    });

    describe('.close()', function() {
        var messages;
        beforeEach(function(done) {
            fixture.load('messages.html');
            CMS.config = {
                debug: false
            };
            CMS.settings = {
                toolbar: 'expanded'
            };
            $(function() {
                messages = new CMS.Messages();
                done();
            });
        });

        afterEach(function() {
            fixture.cleanup();
        });
        it('closes a message', function() {
            messages.open({ message: 'test message' });
            spyOn($.fn, 'fadeOut');
            messages.close();
            expect($.fn.fadeOut).toHaveBeenCalledWith(300);

            messages = new CMS.Messages({ messageDuration: 10 });
            messages.open({ message: 'test message' });
            messages.close();
            expect($.fn.fadeOut).toHaveBeenCalledWith(10);
        });
    });
});

'use strict';

describe('CMS.Toolbar', function () {
    it('creates a Toolbar class when document is ready', function () {
        expect(CMS.Toolbar).toBeDefined();
    });

    describe('instance', function () {
        var toolbar;
        beforeEach(function (done) {
            $(function () {
                toolbar = new CMS.Toolbar();
                done();
            });
        });

        it('has ui');

        it('has options');

        it('initializes the states');
    });

    describe('.toggle()', function () {
        it('delegates to `open()`');

        it('delegates to `close()`');
    });

    describe('.open', function () {
        it('opens toolbar');

        it('animates toolbar to correct position if debug is true');

        it('turns the disclosure triangle into correct position');

        it('remembers toolbar state');
    });

    describe('.close()', function () {
        it('closes toolbar');

        it('does not close toolbar if it is locked');

        it('animates toolbar to correct position if debug is true');

        it('turns the disclosure triangle into correct position');

        it('remembers toolbar state');
    });

    describe('.showLoader()', function () {
        it('shows the loader');
    });

    describe('.hideLoader()', function () {
        it('hides the loader');
    });

    describe('.openAjax()', function () {
        it('makes the request');

        it('does not make the request if there is a confirmation that is not succeeded');
    });
});

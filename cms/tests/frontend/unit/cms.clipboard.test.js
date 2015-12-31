'use strict';

describe('CMS.Clipboard', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Clipboard class', function () {
        expect(CMS.Clipboard).toBeDefined();
    });

    it('has public API');

    describe('instance', function () {
        it('has options');
        it('has ui');
        it('has its own private modal instance');
        it('sets up events to open the modal');
        it('sets up events to clear the clipboard');
    });

    describe('.clear()', function () {
        it('makes a request to the API');
    });
});

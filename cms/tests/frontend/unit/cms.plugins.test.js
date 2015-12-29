'use strict';

describe('CMS.Plugin', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');

    it('creates a Plugin class', function () {
        expect(CMS.Plugin).toBeDefined();
    });

    it('has public API');

    describe('instance', function () {
        it('has ui');
        it('has options');
        it('can be of different types');
        it('sets its options to the dom node');
    });

    describe('.addPlugin()', function () {
        it('makes a request to the API');
        it('does not make a request if CMS.API is locked');
        it('edits newly created plugin if request succeeded');
        it('sets newPlugin option if request succeeded');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('shows the error message if request failed');
    });

    describe('.editPlugin()', function () {
        it('creates and opens a modal to edit a plugin');
        it('creates and opens a modal to edit freshly created plugin');
        it('adds events to remove the "add plugin" placeholder');
    });

    describe('.copyPlugin()', function () {
        it('makes a request to the API');
        it('does not make a request if CMS.API is locked');
        it('shows the success message if request succeeds');
        it('reloads the browser if request succeeds');
        it('shows the error message if request failed');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('clears the clipboard first if custom options were passed');
        it('clears the clipboard first if source language was passed');
    });

    describe('.cutPlugin()', function () {
        it('makes a request to the API');
        it('clears the clipboard before making the request');
        it('shows the success message if request succeeds');
        it('reloads the browser if request succeeds');
        it('shows the error message if request failed');
        it('does not make a request if CMS.API is locked');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
    });

    describe('.pastePlugin()', function () {
        it('moves the clipboard draggable dom node plugins child list');
        it('moves the clipboard draggable dom node placeholders child list');
        it('triggers correct events afterwards');
    });

    describe('.movePlugin()', function () {
        it('makes the request to the API');
        it('does not make a request if CMS.API is locked');
        it('does not make a request if there is no placeholder in chain of parents');
        it('reloads browser if response requires it');
        it('updates the plugin urls if response requires it');
        it('shows success animation');
        it('shows error message if request fails');
        it('locks the CMS.API before making the request');
        it('unlocks the CMS.API if request is successful');
        it('unlocks the CMS.API if request is not successful');
        it('triggers window resize');
        it('shows publish page button optimistically');
        it('enables "revert to live" button optimistically');
    });

    describe('.deletePlugin()', function () {
        it('creates and opens a modal for plugin deletion');
        it('adds events to remove any existing "add plugin" placeholders');
    });

    describe('.editPluginPostAjax()', function () {
        it('delegates to editPlugin with url coming from response');
    });
});

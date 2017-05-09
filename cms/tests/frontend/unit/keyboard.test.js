'use strict';
var keyboard = require('../../../static/cms/js/modules/keyboard').default;
var $ = require('jquery');

describe('keyboard', function () {
    it('works as usual', function () {
        var callback = jasmine.createSpy();

        keyboard.bind('1', callback);

        keyboard.pressKey('1');
        expect(callback).toHaveBeenCalledTimes(1);
    });

    it('modifies callback execution to stop when inputs are focused', function () {
        var callback = jasmine.createSpy();

        keyboard.bind('1', callback);

        spyOn($.fn, 'is').and.returnValue(true);

        keyboard.pressKey('1');
        expect(callback).not.toHaveBeenCalled();
        expect($.fn.is).toHaveBeenCalledTimes(1);
        expect($.fn.is).toHaveBeenCalledWith('input, textarea, select, [contenteditable]');
    });
});

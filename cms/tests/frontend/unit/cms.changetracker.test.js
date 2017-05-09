'use strict';

var CMS = require('../../../static/cms/js/modules/cms.base').default;
var ChangeTracker = require('../../../static/cms/js/modules/cms.changetracker').default;
var jQuery = require('jquery');
var $ = jQuery;

window.CMS = window.CMS || CMS;
CMS.ChangeTracker = ChangeTracker;

describe('CMS.ChangeTracker', function () {
    fixture.setBase('cms/tests/frontend/unit/fixtures');
    var tracker;

    beforeEach(function (done) {
        fixture.load('iframe_form.html');

        $(function () {
            // since _trackChange is being bound in the constructor
            // we cannot spy on it normally
            spyOn(CMS.ChangeTracker.prototype, '_trackChange');
            tracker = new CMS.ChangeTracker($('.js-test-iframe'));
            done();
        });
    });

    afterEach(function () {
        fixture.cleanup();
    });

    it('creates a ChangeTracker class', function () {
        expect(CMS.ChangeTracker).toBeDefined();
    });

    it('has public API', function () {
        expect(CMS.ChangeTracker.prototype.isFormChanged).toEqual(jasmine.any(Function));
    });

    describe('instance', function () {
        it('has ui', function () {
            expect(tracker.ui).toEqual({
                iframe: jasmine.any(Object)
            });
        });

        it('has initial state', function () {
            expect(tracker.state).toEqual({
                fields: jasmine.any(Object),
                formChanged: false
            });
        });
    });

    describe('_setupEvents()', function () {
        it('adds event handlers', function () {
            expect($(fixture.el).find('input, select, textarea')).toHandle('change.cms.tracker');
            expect($(fixture.el).find('input, select, textarea')).toHandle('keydown.cms.tracker');
        });

        it('adds correct event handlers', function () {
            $(fixture.el).find('input:first').trigger('change');
            expect(tracker._trackChange).toHaveBeenCalledTimes(1);
        });
    });

    describe('_getValue() / _getOriginalValue()', function () {
        it('handles text inputs', function () {
            expect(tracker._getValue($('input[type="text"]')[0])).toEqual('original');
            expect(tracker._getOriginalValue($('input[type="text"]')[0])).toEqual('original');
            $('input[type="text"]').val('new');
            expect(tracker._getValue($('input[type="text"]')[0])).toEqual('new');
            expect(tracker._getOriginalValue($('input[type="text"]')[0])).toEqual('original');
        });

        it('handles textarea', function () {
            expect(tracker._getValue($('textarea')[0])).toEqual('');
            expect(tracker._getOriginalValue($('textarea')[0])).toEqual('');
            $('textarea').val('new');
            expect(tracker._getValue($('textarea')[0])).toEqual('new');
            expect(tracker._getOriginalValue($('textarea')[0])).toEqual('');
        });

        it('handles select', function () {
            expect(tracker._getValue($('select:first')[0])).toEqual('1');
            expect(tracker._getOriginalValue($('select:first')[0])).toEqual('1');
            $('select:first').val(2);
            expect(tracker._getValue($('select:first')[0])).toEqual('2');
            expect(tracker._getOriginalValue($('select:first')[0])).toEqual('1');
        });

        it('handles select multiple', function () {
            expect(tracker._getValue($('select:last')[0])).toEqual(['1', '2']);
            expect(tracker._getOriginalValue($('select:last')[0])).toEqual(['1', '2']);
            $('select:last').val(['2', '3']);
            expect(tracker._getValue($('select:last')[0])).toEqual(['2', '3']);
            expect(tracker._getOriginalValue($('select:last')[0])).toEqual(['1', '2']);
        });

        it('handles checkboxes', function () {
            expect(tracker._getValue($(':checkbox')[0])).toEqual(false);
            expect(tracker._getOriginalValue($(':checkbox')[0])).toEqual(false);
            $(':checkbox').prop('checked', true);
            expect(tracker._getValue($(':checkbox')[0])).toEqual(true);
            expect(tracker._getOriginalValue($(':checkbox')[0])).toEqual(false);
        });

        it('handles radio buttons', function () {
            expect(tracker._getValue($(':radio')[0])).toEqual(true);
            expect(tracker._getOriginalValue($(':radio')[0])).toEqual(true);
            expect(tracker._getValue($(':radio')[1])).toEqual(false);
            expect(tracker._getOriginalValue($(':radio')[1])).toEqual(false);
            $(':radio:last').prop('checked', true);
            expect(tracker._getValue($(':radio')[0])).toEqual(false);
            expect(tracker._getOriginalValue($(':radio')[0])).toEqual(true);
            expect(tracker._getValue($(':radio')[1])).toEqual(true);
            expect(tracker._getOriginalValue($(':radio')[1])).toEqual(false);
        });
    });

    describe('isFormChanged', function () {
        beforeEach(function () {
            spyOn(tracker, '_isEditorChanged').and.returnValue(false);
        });

        it('returns true if form changed', function () {
            tracker.state.formChanged = true;
            expect(tracker.isFormChanged()).toEqual(true);
        });

        it('returns true if ckeditor values changed', function () {
            tracker._isEditorChanged.and.returnValue(true);
            tracker.state.formChanged = true;
            expect(tracker.isFormChanged()).toEqual(true);
            tracker.state.formChanged = false;
            expect(tracker.isFormChanged()).toEqual(true);
        });

        it('returns false if nothing changed', function () {
            tracker.state.formChanged = false;
            expect(tracker.isFormChanged()).toEqual(false);
        });
    });

    describe('_isEditorChanged()', function () {
        beforeEach(function () {
            tracker.ui.iframe = [{
                contentWindow: {}
            }];
        });

        it('returns false if there are no ckeditor instances', function () {
            expect(tracker._isEditorChanged()).toEqual(false);
            tracker.ui.iframe[0].contentWindow.CKEDITOR = {};
            expect(tracker._isEditorChanged()).toEqual(false);
        });

        it('returns false if there none of ckeditor instances changed', function () {
            tracker.ui.iframe[0].contentWindow.CKEDITOR = {
                instances: {
                    a: {
                        checkDirty: function () {
                            return false;
                        }
                    },
                    b: {
                        checkDirty: function () {
                            return false;
                        }
                    }
                }
            };

            expect(tracker._isEditorChanged()).toEqual(false);
        });

        it('returns true if any of the ckeditor instances changed', function () {
            tracker.ui.iframe[0].contentWindow.CKEDITOR = {
                instances: {
                    a: {
                        checkDirty: function () {
                            return false;
                        }
                    },
                    b: {
                        checkDirty: function () {
                            return true;
                        }
                    }
                }
            };

            expect(tracker._isEditorChanged()).toEqual(true);
        });
    });

    describe('_trackChange()', function () {
        beforeEach(function () {
            CMS.ChangeTracker.prototype._trackChange.and.callThrough();
        });

        it('tracks changes in the fields', function () {
            var element = $(fixture.el).find('input[type="text"]');

            expect(tracker.state.formChanged).toEqual(false);

            element.val('new!').trigger('change');

            expect(tracker.state.formChanged).toEqual(true);
            expect(tracker.state.fields.get(element[0])).toEqual({
                editedValue: 'new!',
                originalValue: 'original'
            });

            element.val('newer!').trigger('change');

            expect(tracker.state.formChanged).toEqual(true);
            expect(tracker.state.fields.get(element[0])).toEqual({
                editedValue: 'newer!',
                originalValue: 'original'
            });

            element.val('original').trigger('change');

            expect(tracker.state.formChanged).toEqual(false);
            expect(tracker.state.fields.get(element[0])).toEqual({
                editedValue: 'original',
                originalValue: 'original'
            });
        });

        it('handles the case where original value is the same as edited one', function () {
            var element = $(fixture.el).find('input[type="text"]');

            expect(tracker.state.formChanged).toEqual(false);

            element.trigger('change');

            expect(tracker.state.formChanged).toEqual(false);
        });
    });
});

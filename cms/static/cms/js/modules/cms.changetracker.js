/*
 * Copyright https://github.com/divio/django-cms
 */

var $ = require('jquery');
var Class = require('classjs');
var SimpleMap = require('./simplemap');

/**
 * Tracks the changes done inside the modal form.
 * The reason there's an implementation of actual tracking is because
 * checking value vs defaultValue at the time of the actual reload is
 * very unreliable.
 *
 * @class ChangeTracker
 * @namespace CMS
 * @uses CMS.API.Helpers
 */
var ChangeTracker = new Class({
    initialize: function initialize(iframe) {
        var that = this;

        that.state = {
            fields: new SimpleMap(),
            formChanged: false
        };

        that._setupUI(iframe);
        that._setupEvents();
    },

    _setupUI: function _setupUI(iframe) {
        this.ui = {
            iframe: iframe
        };
    },

    _setupEvents: function _setupEvents() {
        this.ui.iframe.contents()
            .find('.change-form form')
            .find('input, textarea, select')
            .on('change.cms.tracker keydown.cms.tracker', this._trackChange.bind(this));
    },

    /**
     * Tracks the change made on the field
     *
     * @method _trackChange
     * @private
     * @param {$.Event} e
     */
    _trackChange: function _trackChange(e) {
        var that = this;

        if (that.state.fields.has(e.target)) {
            var current = that.state.fields.get(e.target);
            var newValue = that._getValue(e.target);

            if (current.originalValue === newValue) {
                that.state.formChanged = false;
            }
            that.state.fields.set(
                e.target,
                $.extend(current, {
                    editedValue: newValue
                })
            );
        } else {
            var defaultValue = that._getOriginalValue(e.target);
            var editedValue = that._getValue(e.target);

            that.state.fields.set(e.target, {
                originalValue: defaultValue,
                editedValue: editedValue
            });

            if (defaultValue !== editedValue) {
                that.state.formChanged = true;
            }
        }
    },

    /**
     * @function _getValue
     * @private
     * @param {Element} target
     * @returns {String|Boolean|void}
     */
    _getValue: function _getValue(target) {
        var el = $(target);

        if (el.is(':checkbox') || el.is(':radio')) {
            return target.checked;
        }
        if (el.is('select')) {
            return el.val();
        }
        return target.value;
    },

    /**
     * @function _getOriginalValue
     * @private
     * @param {Element} target
     * @returns {String|Boolean|void}
     */
    _getOriginalValue: function _getOriginalValue(target) {
        var el = $(target);

        if (el.is(':checkbox') || el.is(':radio')) {
            return target.defaultChecked;
        }

        if (el.is('select')) {
            var options = el.find('option');
            var value;

            if (el.is('[multiple]')) {
                value = [];
                options.each(function () {
                    if (this.defaultSelected) {
                        value.push($(this).val());
                    }
                });
            } else {
                options.each(function () {
                    if (this.defaultSelected) {
                        value = $(this).val();
                    }
                });
            }
            return value;
        }

        return target.defaultValue;
    },

    /**
     * @method isFormChanged
     * @public
     * @returns {Boolean}
     */
    isFormChanged: function isFormChanged() {
        return this.state.formChanged || this._isEditorChanged();
    },

    /**
     * Checks if any of the CKEditor instances have been changed.
     *
     * @method _isEditorChanged
     * @private
     * @returns {Boolean}
     */
    _isEditorChanged: function _isEditorChanged() {
        var win = this.ui.iframe[0].contentWindow;
        var isEditorChanged = false;

        if (win && win.CKEDITOR && win.CKEDITOR.instances) {
            isEditorChanged = Object.keys(win.CKEDITOR.instances).some(function (key) {
                return win.CKEDITOR.instances[key].checkDirty();
            });
        }

        return isEditorChanged;
    }
});

module.exports = ChangeTracker;

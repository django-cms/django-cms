/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';

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
class ChangeTracker {
    constructor(iframe) {
        this.state = {
            fields: new Map(),
            formChanged: false
        };

        this._setupUI(iframe);
        this._setupEvents();
    }

    _setupUI(iframe) {
        this.ui = {
            iframe: iframe
        };
    }

    _setupEvents() {
        try {
            this.ui.iframe
                .contents()
                .find('.change-form form')
                .find('input, textarea, select')
                .on('change.cms.tracker keydown.cms.tracker', this._trackChange.bind(this));
        } catch {
            // there can be cases when the iframe contents don't exist
        }
    }

    /**
     * Tracks the change made on the field
     *
     * @method _trackChange
     * @private
     * @param {$.Event} e
     */
    _trackChange(e) {
        if (this.state.fields.has(e.target)) {
            var current = this.state.fields.get(e.target);
            var newValue = this._getValue(e.target);

            if (current.originalValue === newValue) {
                this.state.formChanged = false;
            }
            this.state.fields.set(
                e.target,
                $.extend(current, {
                    editedValue: newValue
                })
            );
        } else {
            var defaultValue = this._getOriginalValue(e.target);
            var editedValue = this._getValue(e.target);

            this.state.fields.set(e.target, {
                originalValue: defaultValue,
                editedValue: editedValue
            });

            if (defaultValue !== editedValue) {
                this.state.formChanged = true;
            }
        }
    }

    /**
     * @function _getValue
     * @private
     * @param {Element} target
     * @returns {String|Boolean|void}
     */
    _getValue(target) {
        var el = $(target);

        if (el.is(':checkbox') || el.is(':radio')) {
            return target.checked;
        }
        if (el.is('select')) {
            return el.val();
        }
        return target.value;
    }

    /**
     * @function _getOriginalValue
     * @private
     * @param {Element} target
     * @returns {String|Boolean|void}
     */
    _getOriginalValue(target) {
        var el = $(target);

        if (el.is(':checkbox') || el.is(':radio')) {
            return target.defaultChecked;
        }

        if (el.is('select')) {
            var options = el.find('option');
            var value;

            if (el.is('[multiple]')) {
                value = [];
                options.each(function() {
                    if (this.defaultSelected) {
                        value.push($(this).val());
                    }
                });
            } else {
                options.each(function() {
                    if (this.defaultSelected) {
                        value = $(this).val();
                    }
                });
            }
            return value;
        }

        return target.defaultValue;
    }

    /**
     * @method isFormChanged
     * @public
     * @returns {Boolean}
     */
    isFormChanged() {
        return this.state.formChanged || this._isEditorChanged();
    }

    /**
     * Checks if any of the CKEditor instances have been changed.
     *
     * @method _isEditorChanged
     * @private
     * @returns {Boolean}
     */
    _isEditorChanged() {
        var win = this.ui.iframe[0].contentWindow;
        var isEditorChanged = false;

        if (win && win.CKEDITOR && win.CKEDITOR.instances) {
            isEditorChanged = Object.keys(win.CKEDITOR.instances).some(function(key) {
                return win.CKEDITOR.instances[key].checkDirty();
            });
        }

        return isEditorChanged;
    }
}

export default ChangeTracker;

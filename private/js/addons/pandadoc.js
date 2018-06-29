import $ from 'jquery';

class Pandadoc {
    constructor(options) {
        this.options = $.extend({}, Pandadoc.options, options);

        this._bindEvents();
    }

    _bindEvents() {
        var that = this;

        $(document).on('submit', this.options.formClass, function(e) {
            e.preventDefault();
            that._sendForm($(this));
        });
    }

    _sendForm(form) {
        $.ajax({
            type: 'POST',
            url: form.attr('action'),
            data: form.serialize(),
        })
            .success(function(data) {
                if (data.success) {
                    $('.js-success-message', form).show();
                    $('.js-form-wrapper', form).hide();
                } else {
                    alert(data.message);
                }
            })
            .fail(function() {
                alert('An unknown error has occurred. Please try again later.');
            });
    }
}
Pandadoc.options = {
    formClass: '.js-pandadoc-form',
};

export function initPandadocForms() {
    new Pandadoc();
}

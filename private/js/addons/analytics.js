import $ from 'jquery';

const Analytics = {
    linksClass: '.js-analytics-link',
    formsClass: '.js-analytics-form',
    links: null,
    forms: null,

    init: function() {
        this.links = $(this.linksClass);
        this.forms = $(this.formsClass);

        this._bindEvents();
    },

    _bindEvents: function() {
        this.links.each(function() {
            var link = $(this);
            var params = $.extend(
                {
                    proccess: link.data('process'),
                    page: link.data('page'),
                },
                link.data('params')
            );

            if (window.analytics) {
                window.analytics.trackLink(link, link.data('event'), params);
            }
        });

        this.forms.each(function() {
            var form = $(this);
            var params = $.extend(
                {
                    proccess: form.data('process'),
                    page: form.data('page'),
                },
                form.data('params')
            );

            if (window.analytics) {
                window.analytics.trackForm(form, form.data('event'), params);
            }
        });
    },
};

export function initAnalytics() {
    Analytics.init();
}

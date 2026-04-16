/*
 * Copyright https://github.com/django-cms/django-cms
 *
 * PageSmartLinkWidget — used in admin/cms/page/advanced-settings for the redirect
 * field. Initialises Django admin's bundled Select2 (v4) on a <select> element,
 * allowing users to either pick a matching page via AJAX autocomplete or type an
 * arbitrary URL (captured via Select2 `tags`).
 */
(function () {
    'use strict';

    var $ = (window.django && window.django.jQuery) || window.jQuery;

    function init(options) {
        $('#' + options.id).select2({
            placeholder: options.text,
            allowClear: true,
            minimumInputLength: 0,
            tags: true,
            createTag: function (params) {
                var term = $.trim(params.term);

                if (term === '') {
                    return null;
                }
                return { id: term, text: term, newTag: true };
            },
            ajax: {
                url: options.url,
                dataType: 'json',
                delay: 200,
                data: function (params) {
                    return { q: params.term, language_code: options.lang };
                },
                processResults: function (data) {
                    return {
                        results: $.map(data, function (item) {
                            return {
                                id: item.redirect_url,
                                text: item.title + ' (/' + item.path + ')'
                            };
                        })
                    };
                }
            }
        });
    }

    $(function () {
        document.querySelectorAll('[data-cms-widget-pagesmartlinkwidget]').forEach(function (el) {
            var widget = JSON.parse(el.querySelector('script').textContent);

            init(widget);
        });
    });
})();

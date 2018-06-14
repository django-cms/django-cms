/*!
 * @author:    Divio AG
 * @copyright: http://www.divio.ch
 */

var Cl = window.Cl || {};

(function ($) {
    'use strict';

    Cl.newsBlog = {

        init: function () {
            var that = this;

            // there might be more addons available within one page
            $('.js-aldryn-newsblog-article-search').each(function () {
                that._search($(this));
            });
        },

        _handler: function (e) {
            e.preventDefault();

            var form = $(this);

            $.ajax({
                type: 'GET',
                url: form.attr('action'),
                data: form.serialize()
            }).always(function (data) {
                form.siblings('.js-search-results').html(data);
            }).fail(function () {
                alert('REQUEST TIMEOUT'); // eslint-disable-line
            });
        },

        // container should be a jQuery object
        _search: function (container) {
            var form = container.find('form');

            form.on('submit', this._handler);
        }

    };

    // autoload
    $(function () {
        if ($('.js-aldryn-newsblog-article-search').length) {
            Cl.newsBlog.init();
        }
    });

})(jQuery);

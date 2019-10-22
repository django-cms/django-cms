import $ from 'jquery';
import { template } from 'lodash';
import moment from 'moment';
import 'moment/locale/se';

$(() => {
    moment.locale($('html').attr('lang'));
    var match = window.location.search.match(/page=(\d+)/) || [null, 1];
    var pageIndex = match[1];
    var listUrl = 'https://publish.ne.cision.com/papi/NewsFeed/' + window.Cision.allReleases + '?format=json&pageIndex=' + pageIndex;

    var loadPage = function (url) {
        return $.get(url).then(function (r) {
            $('.press-releases-list').html(template($('#press-releases-list-tmpl').html(), {
                imports: {
                    moment,
                },
            })(r));
        });
    }

    loadPage(listUrl);

    if (window.location.search.match('subscription_success') && window.history && window.history.pushState) {
        window.history.pushState(null, null, window.location.pathname);
    }
});

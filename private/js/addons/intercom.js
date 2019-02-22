import $ from 'jquery';

export function initIntercom() {
    $(window).on('load hashchange', function() {
        var intercomMessage = '';
        var hash = window.location.hash;

        if (hash && hash === '#intercom') {
            window.Intercom && window.Intercom('show');
        }
        if (hash && hash.indexOf('#intercom?') !== -1) {
            intercomMessage = hash.split('?')[1];
            window.Intercom && window.Intercom('showNewMessage', decodeURI(intercomMessage));
        }
    });

    // Intercom tracking
    // https://www.intercom.com/help/configure-intercom-for-your-product-or-site/customize-intercom-to-be-about-your-users/set-up-event-tracking-in-intercom
    // data-intercom='{
    //     "trigger": "click",
    //     "timeout": 1000,
    //     "track": "business-content",
    //     "meta": ""
    // }'
    let timeout = function () {};

    $('[data-intercom]').each((index, item) => {
        let el = $(item);
        let data = el.data('intercom');

        // event and Intercom are required
        if (data.event === '') return;

        el.on(data.trigger || 'click', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // console.log('trackEvent', data.track, data.meta || {});
                window.Intercom && window.Intercom('trackEvent', data.track, data.meta || {});
            }, data.timeout || 0);
        });
    });
}

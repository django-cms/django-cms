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
}

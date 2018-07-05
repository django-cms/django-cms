import $ from 'jquery';
import Cookies from 'js-cookie';
import django_privacy_mgmt, { baseHost } from 'addons/privacy-management';

function initCookieBar() {
    var COOKIE_NAME = 'django-privacy-mgmt-banner-state';
    var cookie_banner_state = Cookies.getJSON(COOKIE_NAME) || { hidden: false };

    if (!cookie_banner_state.hidden) {
        $('.js-cookie-bar').show();
    }

    // accepting
    $('.js-cookie-accept').on('click', function(e) {
        e.preventDefault();
        e.stopImmediatePropagation();

        django_privacy_mgmt.setPreference('STATISTICS', true);
        django_privacy_mgmt.setPreference('MARKETING', true);

        closeBar();
    });

    $('.js-modal-accept').on('click', closeBar);

    function closeBar() {
        Cookies.set(
            COOKIE_NAME,
            { hidden: true },
            {
                // in FF this is required so that the cookie is not deleted after ending the browser session
                // we set it to a very high number of dates so that this cookie 'never' expires.
                expires: 2000,
                domain: baseHost,
            }
        );
        $('.js-cookie-bar').hide();
    }
}

function initPrivacyPopup() {
    var inputs = $('.js-gdpr-optin');
    var privacyModal = $('#privacysettings');

    $('.js-modal-accept').on('click', function(e) {
        e.preventDefault();

        privacyModal.modal('hide');

        inputs.each(function() {
            var el = $(this);
            var name = el.data('gdpr-category-name');

            django_privacy_mgmt.setPreference(name, el.prop('checked'));
        });
    });

    $('.js-cookie-settings').on('click', function(e) {
        e.preventDefault();
        privacyModal.modal('show');
    });

    inputs.each(function() {
        // initialize on modal load
        var el = $(this);
        var name = el.data('gdpr-category-name');
        var preference = django_privacy_mgmt.getPreference(name);
        el.prop('checked', preference);
    });
}

export function initAnalyticsIntegrations() {
    window.analyticsIntegrations = null;

    if (!django_privacy_mgmt.getPreference('STATISTICS')) {
        window.analyticsIntegrations = {
            integrations: {
                'Segment.io': false,
                'Google Analytics': false,
            },
        };
    }
}

export function initPrivacySettings() {
    initCookieBar();
    initPrivacyPopup();
}

import 'libs/bootstrap';
import $ from 'jquery';
import outdatedBrowser from 'outdatedbrowser';
import { noscript } from 'addons/utils';
import { initFileInputs } from 'addons/file';
import svg4everybody from 'svg4everybody';
import { initLocalScroll } from 'addons/localscroll';
import { initHeader } from 'addons/header';
import { initBlogCarousel } from 'addons/carousel';
import { initWaypoints } from 'addons/waypoints';
import { initFixedHeaderTables, initTableCrossHover } from 'addons/tables';
import { initPrivacySettings, initAnalyticsIntegrations } from 'addons/privacy';
// import { initPartnerMap } from 'addons/map';
import { initIntercom } from 'addons/intercom';
import { initAnalytics } from 'addons/analytics';
import { initPandadocForms } from 'addons/pandadoc';
import { initMessages } from 'addons/messages';
import 'addons/flying-focus';
import { initLazyLoad } from 'addons/lazyload';
import { initPriceSlider } from 'addons/price-slider';
import { initSupportLink } from 'addons/support';

svg4everybody();

window.$ = window.jQuery = $;

// patch bootstrap 4 modal
$.fn.modal.Constructor.prototype._checkScrollbar = function () {
    // taken from bootstrap 3
    // https://github.com/twbs/bootstrap-sass/blob/51486a8bd836d32b9f413e911ed83b433ef4ad39/assets/javascripts/bootstrap/modal.js#L259-L267
    var fullWindowWidth = window.innerWidth
    if (!fullWindowWidth) { // workaround for missing window.innerWidth in IE8
        var documentElementRect = document.documentElement.getBoundingClientRect()
        fullWindowWidth = documentElementRect.right - Math.abs(documentElementRect.left)
    }
    this._isBodyOverflowing = document.body.clientWidth < fullWindowWidth;
    this._scrollbarWidth = this._getScrollbarWidth()
};

initAnalyticsIntegrations(); // required for the segment snippet

$(() => {
    noscript();
    initLazyLoad();
    initFileInputs();
    initLocalScroll();
    initHeader();
    initBlogCarousel();
    initWaypoints();
    initFixedHeaderTables();
    initTableCrossHover();
    outdatedBrowser({
        languagePath: '',
        lowerThan: 'boxShadow',
    });
    initPrivacySettings();
    // initPartnerMap();
    initIntercom();
    initAnalytics();
    initPandadocForms();
    initMessages();
    initPriceSlider();
    initSupportLink();
});

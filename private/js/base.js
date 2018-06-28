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
import { initPrivacySettings } from 'addons/privacy';
import { initPartnerMap } from 'addons/map';
import 'addons/flying-focus';

svg4everybody({
    polyfill: true,
});

window.$ = window.jQuery = $;

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
}

$(() => {
    noscript();
    initFileInputs();
    initLocalScroll();
    initHeader();
    initBlogCarousel();
    initWaypoints();
    // TODO load this on demand
    initFixedHeaderTables();
    initTableCrossHover();
    outdatedBrowser({
        languagePath: '',
        lowerThan: 'boxShadow',
    });
    initPrivacySettings();
    initPartnerMap();
});

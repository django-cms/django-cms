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
import 'addons/flying-focus';

svg4everybody({
    polyfill: true,
});

window.$ = window.jQuery = $;


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
});

/* global CMS */
import $ from 'jquery';
import { initWaypoints } from 'addons/waypoints';
import { initBlogCarousel } from 'addons/carousel';

CMS.$(window).on('cms-content-refresh', () => {
    // SVGs for some reason don't like DOM diffing, probably related to creation of elements
    // with incorrect namespace, but no time to look into it now ¯\_(ツ)_/¯
    CMS.$('svg').each((i, el) => {
        CMS.$(el).replaceWith(CMS.$(el).clone().wrap('<div></div>').parent().html());
    });

    $(window).trigger('scroll');

    initWaypoints();
    initBlogCarousel();
});

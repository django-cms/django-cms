/* global CMS */
import $ from 'jquery';
import { initWaypoints } from 'addons/waypoints';
import { initBlogCarousel } from 'addons/carousel';
import Breakpoint from 'addons/breakpoint';
import { lazyloadInstance } from 'addons/lazyload';

const showBreakpoint = () => {
    const breakpoint = $('<div />', {
        class: 'breakpoint bg-white is-fixed',
        css: {
            fontSize: '16px',
            lineHeight: '18px',
            fontFamily: 'monospace',
            display: 'inline-block',
            padding: '3px 6px',
            position: 'fixed',
            left: 0,
            bottom: 0,
        },
        title: 'i am only shown for cms users',
    }).appendTo('body');
    $(window)
        .on('change:breakpoint', () => {
            breakpoint.text(Breakpoint.current());
        })
        .trigger('change:breakpoint');
};

$(showBreakpoint);

CMS.$(window).on('cms-content-refresh', () => {
    // SVGs for some reason don't like DOM diffing, probably related to creation of elements
    // with incorrect namespace, but no time to look into it now ¯\_(ツ)_/¯
    CMS.$('svg').each((i, el) => {
        CMS.$(el).replaceWith(
            CMS.$(el)
                .clone()
                .wrap('<div></div>')
                .parent()
                .html()
        );
    });

    $(window).trigger('scroll');

    initWaypoints();
    initBlogCarousel();
    showBreakpoint();
    lazyloadInstance.update();
});

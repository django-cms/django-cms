/* global CMS */
const $ = CMS.$;

$(window).on('cms-content-refresh', () => {
    // SVGs for some reason don't like DOM diffing, probably related to creation of elements
    // with incorrect namespace, but no time to look into it now ¯\_(ツ)_/¯
    $('svg').each((i, el) => {
        $(el).replaceWith($(el).clone().wrap('<div></div>').parent().html());
    });
});

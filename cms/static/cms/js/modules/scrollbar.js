import memoize from 'lodash-es/memoize.js';

/*
 * Measures the width of the browser's vertical scrollbar.
 * Creates an invisible div, calculates the difference between offsetWidth and clientWidth
 * (which equals the scrollbar width), removes the div and returns the width.
 * The result is cached using lodash-es/memoize, so the measurement is only performed once per session.
 *
 * @returns {number} The width of the browser's vertical scrollbar in pixels.
 */
export default memoize(function measure() {
    const scrollDiv = document.createElement('div');
    const body = document.body;

    scrollDiv.className = 'cms-scrollbar-measure';
    body.appendChild(scrollDiv);

    const scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;

    body.removeChild(scrollDiv);

    return scrollbarWidth;
});

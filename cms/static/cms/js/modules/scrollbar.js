import $ from 'jquery';
import { memoize } from 'lodash';

export default memoize(function measure() {
    var scrollDiv = document.createElement('div');
    var body = $('body');

    scrollDiv.className = 'cms-scrollbar-measure';
    body.append(scrollDiv);

    var scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;

    body[0].removeChild(scrollDiv);

    return scrollbarWidth;
});

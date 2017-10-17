import 'libs/bootstrap';
import $ from 'jquery';
import outdatedBrowser from 'outdatedbrowser';
import { noscript } from 'addons/utils';
import { initFileInputs } from 'addons/file';
import svg4everybody from 'svg4everybody';
import { initLocalScroll } from 'addons/localscroll';

svg4everybody();

window.$ = window.jQuery = $;

$(() => {
    noscript();
    initFileInputs();
    initLocalScroll();
    outdatedBrowser({
        languagePath: '',
        lowerThan: 'boxShadow',
    });
});

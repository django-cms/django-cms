import 'libs/bootstrap';
import $ from 'jquery';
import outdatedBrowser from 'outdatedbrowser';
import { noscript } from 'addons/utils';
import svg4everybody from 'svg4everybody';

svg4everybody();

window.$ = window.jQuery = $;

$(() => {
    noscript();
    outdatedBrowser({
        languagePath: '',
        lowerThan: 'boxShadow',
    });
});

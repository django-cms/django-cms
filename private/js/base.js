import 'libs/bootstrap';
import $ from 'jquery';
import outdatedBrowser from 'outdatedbrowser';
import { noscript } from 'addons/utils';

window.$ = window.jQuery = $;

noscript();
outdatedBrowser({
    languagePath: '',
    lowerThan: 'boxShadow',
});

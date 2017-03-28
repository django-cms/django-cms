/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/divio/djangocms-boilerplate-webpack
 */

import $ from 'jquery';
import outdatedBrowser from 'outdatedbrowser';
import 'bootstrap-sass';
import { noscript } from './addons/utils';

// this should usually be disabled, but sometimes
// we rely on jQuery global being available :/
window.$ = window.jQuery = $;

// istanbul ignore next
// shorthand for invoking jQuery(document).ready
$(function () {
    // removes noscript form body
    noscript();

    // DOCS: https://github.com/burocratik/outdated-browser
    outdatedBrowser({
        languagePath: '',
        lowerThan: 'boxShadow'
    });
});

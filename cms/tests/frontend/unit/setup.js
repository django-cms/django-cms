/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 *
 * Runs before every unit test file and recreates the environment karma used to
 * provide: jQuery and jasmine globals, the html fixtures, the base stylesheet
 * (a lot of assertions depend on real layout) and the vendored jasmine-jquery
 * and jasmine-ajax helpers.
 */

import $ from 'jquery';
import Fixture from './helpers/fixture';
import { resetRewireRegistry } from './helpers/rewire';
import { installJasmineGlobals, jasmine } from './helpers/jasmine-compat';

// the specs and both vendored helpers expect these on window
// the local-storage package (and webpack's shim) expect a node-style `global`
window.global = window.global || window;

window.jQuery = $;
window.$ = $;
window.jasmine = jasmine;
installJasmineGlobals();
resetRewireRegistry();

// karma evaluated the bundles before the document was ready, so the modules'
// jQuery ready handlers ran after the specs had set up CMS. jQuery fires them
// synchronously on an already loaded document, so hold them back until the spec
// file has been imported.
$.holdReady(true);
beforeAll(() => $.holdReady(false));

// Several modules use `CMS` as a bare global and touch it from a jQuery ready
// handler, which jQuery runs synchronously once the document is loaded - so the
// global has to exist while cms.base is being imported. Importing cms.base here
// to provide it would evaluate it, and everything it imports (loader, ...),
// before vitest installs the per-file mocks, so a placeholder stands in until a
// spec publishes the module it imported, and whatever the ready handlers wrote
// is carried over.
let cmsNamespace = {};

Object.defineProperty(window, 'CMS', {
    configurable: true,
    get: () => cmsNamespace,
    set: value => {
        if (value && value !== cmsNamespace) {
            Object.keys(cmsNamespace).forEach(key => {
                if (!(key in value)) {
                    value[key] = cmsNamespace[key];
                }
            });
        }
        cmsNamespace = value;
        if (cmsNamespace) {
            // in production the page template seeds these
            cmsNamespace._plugins = cmsNamespace._plugins || [];
            cmsNamespace._instances = cmsNamespace._instances || [];
        }
    }
});

// karma served the compiled stylesheet as a file; :visible and toHaveCss need it
import.meta.glob('../../../static/cms/css/*/cms.base.css', { eager: true });

// karma's html2js preprocessor turned every fixture into window.__html__
const fixtures = {
    ...import.meta.glob('./fixtures/*.html', { eager: true }),
    ...import.meta.glob('./html/*.html', { eager: true })
};

window.__html__ = Object.keys(fixtures).reduce((html, key) => {
    html[key.replace('./', 'cms/tests/frontend/unit/')] = fixtures[key].default;
    return html;
}, {});

// karma served the specs from /context.html and several of them hardcode the
// resulting cms_path query parameter; vitest's page url differs per run
window.CMS_PATH = encodeURIComponent(window.location.pathname + window.location.search);

// CMS.API.Helpers routes its events through `CMS._eventRoot`, which cms.base
// sets to $('#cms-top') when the document is ready. karma had one page for the
// whole suite and whatever element the first spec file left behind; each vitest
// file gets a fresh document, so provide the element the toolbar markup has.
if (!document.getElementById('cms-top')) {
    const eventRoot = document.createElement('div');

    eventRoot.setAttribute('id', 'cms-top');
    document.body.appendChild(eventRoot);
}

window.fixture = new Fixture('cms/tests/frontend/unit/fixtures', 'fixture_container');

// jasmine-ajax registers itself through this hook
window.getJasmineRequireObj = function () {
    window.jasmineRequire = window.jasmineRequire || {};
    return window.jasmineRequire;
};

// both are plain scripts that read the globals set above, so they load last
await import('./helpers/jasmine-jquery.js');
await import('./helpers/mock-ajax.js');

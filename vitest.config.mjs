/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 */

import { defineConfig } from 'vitest/config';
import { playwright } from '@vitest/browser-playwright';
import fs from 'fs';
import path from 'path';

const PROJECT_JS = path.join(import.meta.dirname, 'cms/static/cms/js');
const CMS_VERSION = fs.readFileSync('cms/__init__.py', { encoding: 'utf-8' }).match(/__version__ = '(.*?)'/)[1];

/**
 * The legacy jQuery plugins in modules/ expect a global `jQuery`, which webpack
 * provides through imports-loader. Prepend the import instead.
 */
function injectJQuery() {
    return {
        name: 'cms-inject-jquery',
        enforce: 'pre',
        transform(code, id) {
            if (!/modules[\\/]jquery|select2[\\/]select2/.test(id)) {
                return null;
            }
            return { code: "import jQuery from 'jquery';\n" + code, map: null };
        }
    };
}

/**
 * webpack loads .html as `asset/source`, i.e. a module exporting the markup as a
 * string. Vite would parse it as an entry point, so hand back a module instead.
 */
function htmlAsString() {
    return {
        name: 'cms-html-as-string',
        enforce: 'pre',
        transform(code, id) {
            if (!id.endsWith('.html') || id.includes('?')) {
                return null;
            }
            return { code: `export default ${JSON.stringify(code)};`, map: null };
        }
    };
}

/**
 * The vendored jasmine helpers are sloppy-mode UMD bundles that grab the global
 * object with `function () { return this }()`. That is `undefined` in an ES
 * module, so hand them the real global instead.
 */
function vendorGlobals() {
    return {
        name: 'cms-vendor-globals',
        enforce: 'pre',
        transform(code, id) {
            if (!/unit[\\/]helpers[\\/](jasmine-jquery|mock-ajax)\.js/.test(id)) {
                return null;
            }
            return { code: code.replace(/function\s*\(\)\s*\{\s*return this\s*\}\s*\(\)/g, 'globalThis'), map: null };
        }
    };
}

export default defineConfig({
    plugins: [injectJQuery(), htmlAsString(), vendorGlobals()],
    resolve: {
        alias: {
            jquery: path.join(import.meta.dirname, 'cms/tests/frontend/unit/helpers/jquery-global.js'),
            jstree: path.join(PROJECT_JS, 'libs/jstree/jstree.min.js')
        }
    },
    define: {
        __DEV__: 'false',
        __TEST__: 'true',
        __CMS_VERSION__: JSON.stringify(CMS_VERSION)
    },
    test: {
        globals: true,
        // the specs share window state (CMS, jQuery, fixtures), so they must not
        // run concurrently in sibling browser frames
        fileParallelism: false,
        include: ['cms/tests/frontend/unit/**/*.test.js'],
        setupFiles: ['cms/tests/frontend/unit/setup.js'],
        browser: {
            enabled: true,
            provider: playwright(),
            headless: true,
            screenshotFailures: false,
            instances: [{ browser: 'chromium' }]
        },
        coverage: {
            provider: 'v8',
            reportsDirectory: 'cms/tests/frontend/coverage',
            include: ['cms/static/cms/js/modules/**/*.js', 'cms/static/cms/js/widgets/**/*.js'],
            exclude: ['**/libs/**', '**/jquery.*.js']
        }
    }
});

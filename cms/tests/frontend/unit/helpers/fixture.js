/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 *
 * Replacement for the karma-fixture global. Same API - setBase/load/set/cleanup
 * and an `el` container - reading the markup from `window.__html__`, which the
 * setup module fills from the fixture directories.
 */

'use strict';

var SCRIPT_TYPES = [
    '',
    'application/ecmascript',
    'application/javascript',
    'application/x-ecmascript',
    'application/x-javascript',
    'text/ecmascript',
    'text/javascript',
    'text/x-ecmascript',
    'text/x-javascript'
];

function Fixture(base, id) {
    this.base = base || 'spec/fixtures';
    this.id = id || 'fixture_container';
    this.json = [];
    this.el = document.getElementById(this.id);

    if (!this.el) {
        this.el = document.createElement('div');
        this.el.setAttribute('id', this.id);
        document.body.appendChild(this.el);
    }
}

Fixture.prototype.setBase = function (base) {
    this.base = base;
};

Fixture.prototype.load = function () {
    var args = Array.prototype.slice.call(arguments);
    var append = typeof args[args.length - 1] === 'boolean' ? args.pop() : false;
    var html = window.__html__ || {};
    var that = this;
    var results;

    if (!append) {
        this.cleanup();
    }
    results = args.map(function (filename) {
        var fixturePath = filename[0] === '/' ? filename.substr(1) : that.base + '/' + filename;

        if (!(fixturePath in html)) {
            throw new ReferenceError("Cannot find fixture '" + fixturePath + "'");
        }
        return that._appendFixture(html[fixturePath]);
    });
    return results.length === 1 ? results[0] : results;
};

Fixture.prototype.set = function () {
    var args = Array.prototype.slice.call(arguments);
    var append = typeof args[args.length - 1] === 'boolean' ? args.pop() : false;
    var that = this;
    var results;

    if (!append) {
        this.cleanup();
    }
    results = args.map(function (markup) {
        return that._appendFixture(markup);
    });
    return results.length === 1 ? results[0] : results;
};

Fixture.prototype.cleanup = function () {
    this.json = [];
    this.el.innerHTML = '';
};

Fixture.prototype._appendFixture = function (markup) {
    var temp = document.createElement('div');
    var results = [];
    var node;

    temp.innerHTML = markup;
    while ((node = temp.firstChild)) {
        if (node.nodeType === 1) {
            this.el.appendChild(node);
            results.push(node);
            if (node.nodeName === 'SCRIPT' && SCRIPT_TYPES.indexOf(node.type || '') !== -1) {
                // eslint-disable-next-line no-eval
                window.eval(node.innerText || node.textContent);
            }
        } else {
            temp.removeChild(node);
        }
    }
    return results;
};

export default Fixture;

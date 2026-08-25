/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 *
 * Jasmine compatibility layer for vitest.
 *
 * The unit suite was written for karma + jasmine 2. Rather than rewriting ~14k
 * lines of specs, this module recreates the slice of the jasmine API the suite
 * (and the vendored jasmine-jquery / jasmine-ajax helpers) actually uses on top
 * of vitest primitives: spies, the mock clock, done callbacks, asymmetric
 * matchers and `jasmine.addMatchers`.
 */

'use strict';

import { vi, expect, it, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';

// -------------------------------------------------------------------------- //
// spies
// -------------------------------------------------------------------------- //

var spiedMethods = [];

function callRecord(spy, index) {
    var mock = spy.mock;

    return {
        object: mock.contexts ? mock.contexts[index] : undefined,
        args: mock.calls[index],
        returnValue: mock.results[index] ? mock.results[index].value : undefined
    };
}

/**
 * Adds jasmine's `.and` / `.calls` facade to a vitest mock function.
 */
function decorate(spy, originalImplementation) {
    spy.and = {
        callFake: function (fn) {
            spy.mockImplementation(fn);
            return spy;
        },
        returnValue: function (value) {
            spy.mockImplementation(function () {
                return value;
            });
            return spy;
        },
        returnValues: function () {
            var values = Array.prototype.slice.call(arguments);
            var index = 0;

            spy.mockImplementation(function () {
                var value = values[index];

                index += 1;
                return value;
            });
            return spy;
        },
        callThrough: function () {
            spy.mockImplementation(originalImplementation || function () {});
            return spy;
        },
        throwError: function (error) {
            spy.mockImplementation(function () {
                throw typeof error === 'string' ? new Error(error) : error;
            });
            return spy;
        },
        stub: function () {
            spy.mockImplementation(function () {});
            return spy;
        }
    };

    spy.calls = {
        count: function () {
            return spy.mock.calls.length;
        },
        any: function () {
            return spy.mock.calls.length > 0;
        },
        reset: function () {
            spy.mockClear();
        },
        argsFor: function (index) {
            return spy.mock.calls[index];
        },
        allArgs: function () {
            return spy.mock.calls;
        },
        all: function () {
            return spy.mock.calls.map(function (args, index) {
                return callRecord(spy, index);
            });
        },
        first: function () {
            return spy.mock.calls.length ? callRecord(spy, 0) : undefined;
        },
        mostRecent: function () {
            return spy.mock.calls.length ? callRecord(spy, spy.mock.calls.length - 1) : undefined;
        }
    };

    return spy;
}

/**
 * jasmine's spyOn replaces the method with a stub that does *not* call through,
 * and restores the original after each spec.
 */
export function spyOn(object, method) {
    var original = object[method];
    var spy = vi.spyOn(object, method);

    spy.mockImplementation(function () {});
    spiedMethods.push(spy);
    // the original must stay unbound: jQuery prototype methods spied through
    // $.fn have to keep receiving the jQuery instance as `this`
    return decorate(spy, typeof original === 'function' ? original : undefined);
}

export function createSpy(name, implementation) {
    var spy = vi.fn(implementation);

    if (typeof name === 'string') {
        spy.mockName(name);
    }
    return decorate(spy, implementation);
}

export function createSpyObj(baseName, methodNames) {
    var names = Array.isArray(baseName) ? baseName : methodNames;
    var prefix = Array.isArray(baseName) ? 'unknown' : baseName;
    var object = {};

    (names || []).forEach(function (name) {
        object[name] = createSpy(prefix + '.' + name);
    });
    return object;
}

// -------------------------------------------------------------------------- //
// matchers registered through jasmine.addMatchers
// -------------------------------------------------------------------------- //

var equalityTesters = [];

function equals(a, b) {
    for (var i = 0; i < equalityTesters.length; i++) {
        var result = equalityTesters[i](a, b);

        if (result !== undefined) {
            return result;
        }
    }
    try {
        expect(a).toEqual(b);
        return true;
    } catch {
        return false;
    }
}

var matcherUtil = {
    equals: equals,
    isUndefined: function (value) {
        return value === undefined;
    },
    argsToArray: function (args) {
        return Array.prototype.slice.call(args);
    },
    contains: function (haystack, needle) {
        return Array.prototype.indexOf.call(haystack || [], needle) !== -1;
    },
    buildFailureMessage: function () {
        return 'Expectation failed';
    }
};

/**
 * jasmine 2 matchers are `function (util, customEqualityTesters) { return { compare } }`
 * while vitest expects `function (received, ...expected) { return { pass, message } }`.
 */
expect.extend({
    toMatch(received, expected) {
        const pattern = typeof expected === 'string' ? new RegExp(expected) : expected;
        const pass = pattern.test(received);

        return {
            pass: pass,
            message: () => 'expected ' + String(received) + (pass ? ' not' : '') + ' to match ' + String(pattern)
        };
    }
});

export function addMatchers(matchers) {
    var adapted = {};

    Object.keys(matchers).forEach(function (name) {
        adapted[name] = function (received) {
            var expected = Array.prototype.slice.call(arguments, 1);
            var matcher = matchers[name](matcherUtil, equalityTesters);
            var result = matcher.compare.apply(matcher, [received].concat(expected));

            return {
                pass: result.pass,
                message: function () {
                    return result.message || 'expected ' + String(received) + ' to pass ' + name;
                }
            };
        };
    });
    expect.extend(adapted);
}

// -------------------------------------------------------------------------- //
// clock
// -------------------------------------------------------------------------- //

var clockApi = {
    install: function () {
        vi.useFakeTimers({ shouldAdvanceTime: false });
        return clockApi;
    },
    uninstall: function () {
        vi.useRealTimers();
        return clockApi;
    },
    tick: function (ms) {
        vi.advanceTimersByTime(ms);
        return clockApi;
    },
    mockDate: function (date) {
        vi.setSystemTime(date || new Date());
        return clockApi;
    }
};

// -------------------------------------------------------------------------- //
// done callbacks - vitest dropped them, jasmine specs are full of them
// -------------------------------------------------------------------------- //

// captured before any spec installs fake timers
var realSetTimeout = globalThis.setTimeout.bind(globalThis);

function withDone(fn) {
    if (typeof fn !== 'function' || fn.length === 0) {
        return fn;
    }
    return function () {
        var that = this;

        return new Promise(function (resolve, reject) {
            var done = function (error) {
                if (error) {
                    reject(error);
                } else {
                    // karma resolved on a macrotask, so timeouts the code under
                    // test scheduled while setting itself up have run by the time
                    // the spec body executes
                    realSetTimeout(resolve, 0);
                }
            };

            done.fail = reject;

            var result = fn.call(that, done);

            if (result && typeof result.then === 'function') {
                result.then(resolve, reject);
            }
        });
    };
}

var RUNNER_MODIFIERS = ['skip', 'only', 'todo', 'fails', 'concurrent', 'sequential'];

function wrapRunner(runner) {
    var wrapped = function (name, fn, timeout) {
        return runner(name, withDone(fn), timeout);
    };

    RUNNER_MODIFIERS.forEach(function (key) {
        if (typeof runner[key] !== 'function') {
            return;
        }
        wrapped[key] = function (name, fn, timeout) {
            return runner[key](name, withDone(fn), timeout);
        };
    });
    wrapped.each = runner.each;
    return wrapped;
}

function wrapHook(hook) {
    return function (fn, timeout) {
        return hook(withDone(fn), timeout);
    };
}

// -------------------------------------------------------------------------- //
// the jasmine namespace
// -------------------------------------------------------------------------- //

export var jasmine = {
    createSpy: createSpy,
    createSpyObj: createSpyObj,
    addMatchers: addMatchers,
    clock: function () {
        return clockApi;
    },
    any: function (constructor) {
        return expect.any(constructor);
    },
    anything: function () {
        return expect.anything();
    },
    objectContaining: function (object) {
        return expect.objectContaining(object);
    },
    arrayContaining: function (array) {
        return expect.arrayContaining(array);
    },
    stringMatching: function (value) {
        return expect.stringMatching(value);
    },
    isDomNode: function (object) {
        return object && object.nodeType > 0;
    },
    pp: function (value) {
        try {
            return JSON.stringify(value);
        } catch {
            return String(value);
        }
    },
    util: matcherUtil,
    getEnv: function () {
        return {
            addCustomEqualityTester: function (tester) {
                equalityTesters.push(tester);
                if (expect.addEqualityTesters) {
                    expect.addEqualityTesters([tester]);
                }
            },
            addMatchers: addMatchers
        };
    }
};

/**
 * Installs the jasmine globals the specs rely on. Called once per test file by
 * the setup module.
 */
export function installJasmineGlobals() {
    globalThis.jasmine = jasmine;
    globalThis.spyOn = spyOn;
    globalThis.it = wrapRunner(it);
    globalThis.xit = function (name, fn, timeout) {
        return it.skip(name, withDone(fn), timeout);
    };
    globalThis.test = globalThis.it;
    globalThis.beforeEach = wrapHook(beforeEach);
    globalThis.afterEach = wrapHook(afterEach);
    globalThis.beforeAll = wrapHook(beforeAll);
    globalThis.afterAll = wrapHook(afterAll);

    // jasmine restores spied methods between specs
    afterEach(function () {
        spiedMethods.forEach(function (spy) {
            spy.mockRestore();
        });
        spiedMethods = [];

        // A spec that fails between clock().install() and clock().uninstall()
        // would otherwise leave fake timers behind, and every later spec that
        // waits for jQuery's ready callback hangs.
        vi.useRealTimers();
    });
}

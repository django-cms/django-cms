/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 *
 * Replacement for babel-plugin-rewire's `__Rewire__` / `__ResetDependency__`.
 *
 * A spec declares which dependency modules it wants to swap with `vi.mock` and
 * a getter per export (see `mockRewirable` below); the getter asks this
 * registry for an override and falls back to the real implementation. Because
 * ES module imports are live bindings, the consumer picks up the override on
 * its next access - which is what rewire used to do by rewriting the binding.
 */

'use strict';

// vi.mock factories are evaluated in their own module context, which can hand
// them a second instance of this module - so the registry lives on the global.
const state = globalThis.__cmsRewireState__ || { overrides: new Map(), actuals: new Map() };

globalThis.__cmsRewireState__ = state;

const overrides = state.overrides;

/**
 * Swaps a dependency for the rest of the spec.
 */
export function rewire(name, value) {
    overrides.set(name, value);
}

export function resetRewire(name) {
    overrides.delete(name);
}

export function resetAllRewires() {
    overrides.clear();
}

/**
 * The registry lives on the global object, so it survives a test file. Each file
 * installs its own mocks and must not inherit another file's overrides.
 */
export function resetRewireRegistry() {
    overrides.clear();
    state.actuals.clear();
}

/**
 * Used by the vi.mock factories: the override if one is set, the real thing
 * otherwise.
 */
export function rewired(name, actual) {
    return overrides.has(name) ? overrides.get(name) : actual;
}

/**
 * Builds the module namespace a `vi.mock` factory has to return: every export
 * of the original module, but rewirable by name.
 *
 *     vi.mock('.../modules/loader', async importOriginal =>
 *         mockRewirable(await importOriginal()));
 */
export function mockRewirable(actual, names) {
    const exported = names || Object.keys(actual);
    const namespace = {};

    exported.forEach(name => {
        Object.defineProperty(namespace, name, {
            enumerable: true,
            get() {
                return rewired(name === 'default' ? actual.__rewireName__ || name : name, actual[name]);
            }
        });
    });
    return namespace;
}

/**
 * Same as `mockRewirable`, but the default export is rewired under `name` -
 * specs say `rewire('Modal', FakeModal)`, not `rewire('default', ...)`.
 */
export function mockDefaultAs(name, actual) {
    const namespace = {};

    Object.keys(actual).forEach(key => {
        if (key === 'default') {
            return;
        }
        Object.defineProperty(namespace, key, {
            enumerable: true,
            get() {
                return rewired(key, actual[key]);
            }
        });
    });
    Object.defineProperty(namespace, 'default', {
        enumerable: true,
        get() {
            return rewired(name, actual.default);
        }
    });
    return namespace;
}

/**
 * Some of the modules under test import each other in a cycle (plugins ->
 * structureboard -> clipboard -> plugins). Calling `importOriginal()` from a
 * `vi.mock` factory re-enters that cycle and kills the browser page, so the
 * real module is registered later - once the graph has settled - and the mock
 * namespace only ever reads it through a getter.
 *
 *     vi.mock(PLUGINS, async () => {
 *         const { lazyMock } = await import('./helpers/rewire');
 *
 *         return lazyMock(PLUGINS, { default: 'Plugin' });
 *     });
 *
 *     beforeAll(async () => registerActual(PLUGINS, await vi.importActual(PLUGINS)));
 */
const actuals = state.actuals;

export function registerActual(id, namespace) {
    actuals.set(id, namespace);
}

export function lazyMock(id, names) {
    const namespace = {};

    Object.keys(names).forEach(exportName => {
        const rewireName = names[exportName];
        // Import bindings are read once, so handing out the current value would
        // freeze whatever was in place when the module under test was evaluated.
        // These stand-ins forward every access to the value that is current now.
        let standIn;
        const current = () => {
            const actual = actuals.get(id);
            const value = rewired(rewireName, actual ? actual[exportName] : undefined);

            // guard against a mocked namespace being registered as the original,
            // which would make the stand-in forward to itself
            return value === standIn ? undefined : value;
        };
        const forward = {
            apply: (target, thisArg, args) => Reflect.apply(current(), thisArg, args),
            construct: (target, args) => Reflect.construct(current(), args),
            get: (target, prop) => Reflect.get(Object(current()), prop),
            set: (target, prop, value) => Reflect.set(Object(current()), prop, value),
            has: (target, prop) => prop in Object(current()),
            // spyOn() defines the spy through defineProperty; without this trap it
            // would land on the stand-in instead of the module it forwards to
            defineProperty: (target, prop, descriptor) => Reflect.defineProperty(Object(current()), prop, descriptor),
            deleteProperty: (target, prop) => delete Object(current())[prop],
            ownKeys: () => Reflect.ownKeys(Object(current())),
            getPrototypeOf: () => Reflect.getPrototypeOf(Object(current())),
            getOwnPropertyDescriptor: (target, prop) => {
                const descriptor = Reflect.getOwnPropertyDescriptor(Object(current()), prop);

                return descriptor ? Object.assign(descriptor, { configurable: true }) : descriptor;
            }
        };

        standIn = new Proxy(function stub() {}, forward);
        namespace[exportName] = standIn;
    });
    return namespace;
}

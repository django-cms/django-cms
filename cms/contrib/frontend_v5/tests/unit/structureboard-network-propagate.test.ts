import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    STORAGE_KEY,
    _resetForTest,
    handleExternalUpdate,
    listenToExternalUpdates,
    propagateInvalidatedState,
} from '../../frontend/modules/structureboard/network/propagate';

describe('network/propagate — propagateInvalidatedState', () => {
    afterEach(() => {
        _resetForTest();
    });

    it('writes [action, data, pathname] JSON to localStorage', () => {
        propagateInvalidatedState('MOVE', { plugin_id: 1 });
        const raw = localStorage.getItem(STORAGE_KEY);
        expect(raw).not.toBeNull();
        const parsed = JSON.parse(raw!);
        expect(parsed[0]).toBe('MOVE');
        expect(parsed[1]).toEqual({ plugin_id: 1 });
        expect(parsed[2]).toBe(window.location.pathname);
    });

    it('does not throw when localStorage is unavailable', () => {
        const originalSetItem = Storage.prototype.setItem;
        Storage.prototype.setItem = vi.fn(() => {
            throw new Error('quota exceeded');
        });
        expect(() =>
            propagateInvalidatedState('MOVE', { plugin_id: 1 }),
        ).not.toThrow();
        Storage.prototype.setItem = originalSetItem;
    });
});

describe('network/propagate — listenToExternalUpdates', () => {
    let received: Array<[string, unknown]>;

    beforeEach(() => {
        received = [];
    });
    afterEach(() => {
        _resetForTest();
    });

    function fireStorageEvent(value: string | null): void {
        // jsdom's StorageEvent constructor accepts these props.
        const event = new StorageEvent('storage', {
            key: STORAGE_KEY,
            newValue: value,
            url: window.location.href,
        });
        window.dispatchEvent(event);
    }

    it('routes a matching storage event to the callback', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        const payload = JSON.stringify(['MOVE', { plugin_id: 1 }, window.location.pathname]);
        fireStorageEvent(payload);
        expect(received).toEqual([['MOVE', { plugin_id: 1 }]]);
    });

    it('ignores events with a different key', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        const event = new StorageEvent('storage', {
            key: 'unrelated',
            newValue: 'foo',
            url: window.location.href,
        });
        window.dispatchEvent(event);
        expect(received).toEqual([]);
    });

    it('skips events for a different pathname', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        const payload = JSON.stringify(['MOVE', { plugin_id: 1 }, '/other-path/']);
        fireStorageEvent(payload);
        expect(received).toEqual([]);
    });

    it('de-dups against the local latestAction', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        // Emulate "this tab just dispatched MOVE/{plugin_id:1}" — the
        // identical payload coming back via storage should be a no-op.
        propagateInvalidatedState('MOVE', { plugin_id: 1 });
        const payload = JSON.stringify(['MOVE', { plugin_id: 1 }, window.location.pathname]);
        fireStorageEvent(payload);
        expect(received).toEqual([]);
    });

    it('still dispatches when the action differs from latestAction', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        propagateInvalidatedState('MOVE', { plugin_id: 1 });
        const payload = JSON.stringify(['EDIT', { plugin_id: 2 }, window.location.pathname]);
        fireStorageEvent(payload);
        expect(received).toEqual([['EDIT', { plugin_id: 2 }]]);
    });

    it('handleExternalUpdate(null) is a no-op (storage cleared)', () => {
        listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        handleExternalUpdate(null);
        expect(received).toEqual([]);
    });

    it('listenToExternalUpdates returns a teardown that detaches', () => {
        const detach = listenToExternalUpdates((action, data) => {
            received.push([action, data]);
        });
        detach();
        const payload = JSON.stringify(['MOVE', { plugin_id: 1 }, window.location.pathname]);
        fireStorageEvent(payload);
        expect(received).toEqual([]);
    });
});

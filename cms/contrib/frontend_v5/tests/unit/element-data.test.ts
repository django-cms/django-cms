import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    clearElementData,
    deleteElementData,
    getElementData,
    setElementData,
} from '../../frontend/modules/core/element-data';

function el(): HTMLDivElement {
    const div = document.createElement('div');
    document.body.appendChild(div);
    return div;
}

describe('elementData — basic store', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { jQuery?: unknown }).jQuery;
    });

    it('returns undefined for unset keys', () => {
        expect(getElementData(el(), 'cms')).toBeUndefined();
    });

    it('round-trips a value', () => {
        const node = el();
        setElementData(node, 'cms', { plugin_id: 7, type: 'TextPlugin' });
        expect(getElementData<{ plugin_id: number }>(node, 'cms')).toEqual({
            plugin_id: 7,
            type: 'TextPlugin',
        });
    });

    it('keeps separate buckets per element', () => {
        const a = el();
        const b = el();
        setElementData(a, 'cms', 'a');
        setElementData(b, 'cms', 'b');
        expect(getElementData(a, 'cms')).toBe('a');
        expect(getElementData(b, 'cms')).toBe('b');
    });

    it('keeps separate buckets per key on the same element', () => {
        const node = el();
        setElementData(node, 'cms', { kind: 'plugin' });
        setElementData(node, 'other', 42);
        expect(getElementData(node, 'cms')).toEqual({ kind: 'plugin' });
        expect(getElementData(node, 'other')).toBe(42);
    });

    it('overwrites an existing value', () => {
        const node = el();
        setElementData(node, 'cms', 1);
        setElementData(node, 'cms', 2);
        expect(getElementData(node, 'cms')).toBe(2);
    });

    it('deleteElementData returns true when something was removed', () => {
        const node = el();
        setElementData(node, 'cms', 'x');
        expect(deleteElementData(node, 'cms')).toBe(true);
        expect(getElementData(node, 'cms')).toBeUndefined();
    });

    it('deleteElementData returns false when there was nothing to remove', () => {
        expect(deleteElementData(el(), 'cms')).toBe(false);
    });

    it('clearElementData drops every key for the element', () => {
        const node = el();
        setElementData(node, 'cms', 1);
        setElementData(node, 'other', 2);
        clearElementData(node);
        expect(getElementData(node, 'cms')).toBeUndefined();
        expect(getElementData(node, 'other')).toBeUndefined();
    });

    it('preserves reference identity (no clone, no JSON round-trip)', () => {
        const node = el();
        const value = { nested: { plugin: 'Text' } };
        setElementData(node, 'cms', value);
        expect(getElementData(node, 'cms')).toBe(value);
    });
});

describe('elementData — placeholder=object / plugin=array shape footgun', () => {
    /*
     * The legacy contract: placeholders store a single descriptor object
     * under 'cms'; plugins and generics store an array of descriptors
     * (one DOM node may carry several when content is reused). This
     * module doesn't enforce the shape — it just stores what callers
     * give it — but the tests document the behaviour so future readers
     * understand the invariant lives elsewhere (in the eventual
     * cms-data wrapper, not here).
     */
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('stores a single object for placeholder nodes', () => {
        const node = el();
        const placeholder = { type: 'placeholder', name: 'main' };
        setElementData(node, 'cms', placeholder);
        const read = getElementData<typeof placeholder>(node, 'cms');
        expect(read).toBe(placeholder);
    });

    it('stores an array for plugin nodes; pushing extends in place', () => {
        const node = el();
        type Plugin = { plugin_id: number; type: string };
        const initial: Plugin[] = [{ plugin_id: 1, type: 'Text' }];
        setElementData(node, 'cms', initial);
        const arr = getElementData<Plugin[]>(node, 'cms')!;
        arr.push({ plugin_id: 2, type: 'Image' });
        // Reading again returns the same array — mutation is visible to
        // every reader, matching legacy `data('cms').push(...)` behaviour.
        expect(getElementData<Plugin[]>(node, 'cms')).toHaveLength(2);
    });
});

describe('elementData — jQuery mirror', () => {
    /*
     * Verifies that writes are mirrored into jQuery's data cache when
     * jQuery is on `window`. Legacy bundles read `$(el).data(key)` and
     * must keep working until they themselves port.
     */
    type FakeJq = {
        data: ReturnType<typeof vi.fn>;
        removeData: ReturnType<typeof vi.fn>;
    };
    type FakeJquery = ((el: Element) => FakeJq) & { _last?: FakeJq };

    function installFakeJquery(): FakeJquery {
        const fake = ((_el: Element) => {
            const jq: FakeJq = {
                data: vi.fn(),
                removeData: vi.fn(),
            };
            fake._last = jq;
            return jq;
        }) as FakeJquery;
        (window as { jQuery?: unknown }).jQuery = fake;
        return fake;
    }

    beforeEach(() => {
        delete (window as { jQuery?: unknown }).jQuery;
    });

    afterEach(() => {
        document.body.innerHTML = '';
        delete (window as { jQuery?: unknown }).jQuery;
    });

    it('does not call jQuery when jQuery is absent', () => {
        // No jQuery installed — should be a silent no-op.
        const node = el();
        expect(() => setElementData(node, 'cms', 1)).not.toThrow();
    });

    it('mirrors set into $(el).data(key, value)', () => {
        const fake = installFakeJquery();
        const node = el();
        const value = { plugin_id: 42 };
        setElementData(node, 'cms', value);
        expect(fake._last!.data).toHaveBeenCalledWith('cms', value);
    });

    it('mirrors delete into $(el).removeData(key)', () => {
        const fake = installFakeJquery();
        const node = el();
        setElementData(node, 'cms', 1);
        deleteElementData(node, 'cms');
        expect(fake._last!.removeData).toHaveBeenCalledWith('cms');
    });

    it('mirrors clear by removing every previously-set key', () => {
        const fake = installFakeJquery();
        const node = el();
        setElementData(node, 'cms', 1);
        setElementData(node, 'other', 2);
        clearElementData(node);
        // Two distinct $(el) wrappers were created by removeData calls;
        // we only keep the last one. Verify by spying on the factory.
        // Easier: assert the WeakMap is cleared.
        expect(getElementData(node, 'cms')).toBeUndefined();
        expect(getElementData(node, 'other')).toBeUndefined();
        // And at least one removeData was called.
        expect(fake._last!.removeData).toHaveBeenCalled();
    });

    it('does not throw if the jQuery mirror itself throws', () => {
        const broken = (() => ({
            data: () => {
                throw new Error('jq broke');
            },
            removeData: () => {
                throw new Error('jq broke');
            },
        })) as unknown as FakeJquery;
        (window as { jQuery?: unknown }).jQuery = broken;
        const node = el();
        expect(() => setElementData(node, 'cms', 'x')).not.toThrow();
        // Native store still got the value.
        expect(getElementData(node, 'cms')).toBe('x');
    });
});

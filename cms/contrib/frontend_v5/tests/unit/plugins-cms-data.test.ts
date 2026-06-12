import { afterEach, describe, expect, it } from 'vitest';
import {
    clearCmsData,
    ensurePluginDataArray,
    getPlaceholderData,
    getPluginData,
    pushPluginData,
    setPlaceholderData,
    setPluginDataAt,
} from '../../frontend/modules/plugins/cms-data';
import type { PluginOptions } from '../../frontend/modules/plugins/types';

function el(): HTMLDivElement {
    const div = document.createElement('div');
    document.body.appendChild(div);
    return div;
}

describe('cms-data — placeholder shape (single object)', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('returns undefined when nothing is stored', () => {
        expect(getPlaceholderData(el())).toBeUndefined();
    });

    it('round-trips a placeholder descriptor', () => {
        const node = el();
        const opts: PluginOptions = { type: 'placeholder', placeholder_id: 7, name: 'main' };
        setPlaceholderData(node, opts);
        expect(getPlaceholderData(node)).toBe(opts);
    });

    it('overwriting replaces the descriptor (no merge)', () => {
        const node = el();
        setPlaceholderData(node, { type: 'placeholder', placeholder_id: 1 });
        setPlaceholderData(node, { type: 'placeholder', placeholder_id: 2 });
        expect(getPlaceholderData(node)?.placeholder_id).toBe(2);
    });

    it('placeholder reader resilient to plugin-shape data (returns first array entry)', () => {
        const node = el();
        // Write the wrong shape via the plugin path, then read via
        // the placeholder reader.
        pushPluginData(node, { type: 'plugin', plugin_id: 1 });
        pushPluginData(node, { type: 'plugin', plugin_id: 2 });
        const read = getPlaceholderData(node);
        expect(read?.plugin_id).toBe(1);
    });
});

describe('cms-data — plugin shape (array)', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('returns undefined when nothing is stored', () => {
        expect(getPluginData(el())).toBeUndefined();
    });

    it('ensurePluginDataArray creates an empty array on first call', () => {
        const node = el();
        const arr = ensurePluginDataArray(node);
        expect(arr).toEqual([]);
        expect(getPluginData(node)).toBe(arr);
    });

    it('ensurePluginDataArray is idempotent — same reference on repeat calls', () => {
        const node = el();
        const a = ensurePluginDataArray(node);
        const b = ensurePluginDataArray(node);
        expect(a).toBe(b);
    });

    it('pushPluginData appends and is visible to subsequent readers', () => {
        const node = el();
        pushPluginData(node, { type: 'plugin', plugin_id: 1 });
        pushPluginData(node, { type: 'plugin', plugin_id: 2 });
        const read = getPluginData(node);
        expect(read).toHaveLength(2);
        expect(read?.[0]?.plugin_id).toBe(1);
        expect(read?.[1]?.plugin_id).toBe(2);
    });

    it('mutating the returned array is visible (legacy push semantics)', () => {
        const node = el();
        const arr = ensurePluginDataArray(node);
        arr.push({ type: 'plugin', plugin_id: 99 });
        // Reader sees the mutation without re-setting.
        expect(getPluginData(node)).toHaveLength(1);
        expect(getPluginData(node)?.[0]?.plugin_id).toBe(99);
    });

    it('setPluginDataAt replaces an entry at the given index', () => {
        const node = el();
        pushPluginData(node, { type: 'plugin', plugin_id: 1, name: 'first' });
        pushPluginData(node, { type: 'plugin', plugin_id: 2, name: 'second' });
        setPluginDataAt(node, 1, { type: 'plugin', plugin_id: 2, name: 'updated' });
        const read = getPluginData(node)!;
        expect(read[0]?.name).toBe('first');
        expect(read[1]?.name).toBe('updated');
    });

    it('setPluginDataAt is a no-op when no array exists', () => {
        const node = el();
        expect(() => setPluginDataAt(node, 0, { type: 'plugin' })).not.toThrow();
        expect(getPluginData(node)).toBeUndefined();
    });

    it('setPluginDataAt is a no-op for out-of-range indices', () => {
        const node = el();
        pushPluginData(node, { type: 'plugin', plugin_id: 1 });
        setPluginDataAt(node, 5, { type: 'plugin', plugin_id: 99 });
        const read = getPluginData(node)!;
        expect(read).toHaveLength(1);
        expect(read[0]?.plugin_id).toBe(1);
    });

    it('plugin reader resilient to placeholder-shape data (wraps in single-entry array)', () => {
        const node = el();
        setPlaceholderData(node, { type: 'placeholder', placeholder_id: 5 });
        const read = getPluginData(node);
        expect(read).toHaveLength(1);
        expect(read?.[0]?.placeholder_id).toBe(5);
    });
});

describe('cms-data — clearCmsData', () => {
    afterEach(() => {
        document.body.innerHTML = '';
    });

    it('removes the descriptor entirely', () => {
        const node = el();
        pushPluginData(node, { type: 'plugin', plugin_id: 1 });
        clearCmsData(node);
        expect(getPluginData(node)).toBeUndefined();
        expect(getPlaceholderData(node)).toBeUndefined();
    });

    it('is safe to call when nothing is stored', () => {
        expect(() => clearCmsData(el())).not.toThrow();
    });
});

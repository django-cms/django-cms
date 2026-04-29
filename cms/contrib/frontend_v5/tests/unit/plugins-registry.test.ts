import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    _resetRegistryForTest,
    addDescriptor,
    addInstance,
    bumpUsageCount,
    clearDuplicateMarkers,
    findPluginById,
    getAllDescriptors,
    getAllInstances,
    getMostUsedPlugins,
    getUsageMap,
    isPlaceholderDuplicate,
    isPluginDuplicate,
    markPlaceholderDuplicate,
    markPluginDuplicate,
    recalculatePluginPositions,
    removeInstance,
    setDescriptors,
    setInstances,
    updatePluginPositions,
} from '../../frontend/modules/plugins/registry';
import type { PluginInstance } from '../../frontend/modules/plugins/types';

function makeInstance(opts: {
    type?: 'plugin' | 'placeholder' | 'generic';
    plugin_id?: number;
    placeholder_id?: number;
}): PluginInstance {
    return { options: { type: opts.type ?? 'plugin', ...opts } };
}

describe('registry — instance list', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
        _resetRegistryForTest();
    });

    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('starts empty', () => {
        expect(getAllInstances()).toEqual([]);
    });

    it('addInstance / removeInstance round-trip', () => {
        const a = makeInstance({ plugin_id: 1 });
        const b = makeInstance({ plugin_id: 2 });
        addInstance(a);
        addInstance(b);
        expect(getAllInstances()).toHaveLength(2);
        removeInstance(a);
        expect(getAllInstances()).toEqual([b]);
    });

    it('removeInstance is a no-op for unknown instances', () => {
        const a = makeInstance({ plugin_id: 1 });
        const stranger = makeInstance({ plugin_id: 99 });
        addInstance(a);
        expect(() => removeInstance(stranger)).not.toThrow();
        expect(getAllInstances()).toEqual([a]);
    });

    it('setInstances replaces the entire registry in place', () => {
        const a = makeInstance({ plugin_id: 1 });
        addInstance(a);
        const reg = getAllInstances();
        setInstances([makeInstance({ plugin_id: 2 }), makeInstance({ plugin_id: 3 })]);
        // Same array reference (legacy + structureboard hold this).
        expect(getAllInstances()).toBe(reg);
        expect(reg.map((i) => i.options.plugin_id)).toEqual([2, 3]);
    });
});

describe('registry — findPluginById', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
        _resetRegistryForTest();
    });

    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('returns the plugin instance with matching id', () => {
        const target = makeInstance({ plugin_id: 42 });
        addInstance(makeInstance({ plugin_id: 1 }));
        addInstance(target);
        expect(findPluginById(42)).toBe(target);
    });

    it('coerces string ids to numbers (legacy mixed types)', () => {
        const target = makeInstance({ plugin_id: 7 });
        addInstance(target);
        expect(findPluginById('7')).toBe(target);
    });

    it('skips placeholders and generics — only plugin entries match', () => {
        addInstance({ options: { type: 'placeholder', plugin_id: 5 } });
        addInstance({ options: { type: 'generic', plugin_id: 5 } });
        expect(findPluginById(5)).toBeUndefined();
        const real = makeInstance({ plugin_id: 5 });
        addInstance(real);
        expect(findPluginById(5)).toBe(real);
    });

    it('returns undefined for unknown ids', () => {
        expect(findPluginById(123)).toBeUndefined();
    });
});

describe('registry — descriptor list', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('addDescriptor / setDescriptors / getAllDescriptors', () => {
        addDescriptor(['cms-plugin-1', { type: 'plugin', plugin_id: 1 }]);
        expect(getAllDescriptors()).toHaveLength(1);
        const reg = getAllDescriptors();
        setDescriptors([['cms-plugin-2', { type: 'plugin', plugin_id: 2 }]]);
        // Same reference.
        expect(getAllDescriptors()).toBe(reg);
        expect(getAllDescriptors()[0]?.[1].plugin_id).toBe(2);
    });
});

describe('registry — duplicate guards', () => {
    beforeEach(() => {
        clearDuplicateMarkers();
    });

    afterEach(() => {
        clearDuplicateMarkers();
    });

    it('plugin duplicate flag', () => {
        expect(isPluginDuplicate(1)).toBe(false);
        markPluginDuplicate(1);
        expect(isPluginDuplicate(1)).toBe(true);
        // String/number coercion symmetric with marker.
        expect(isPluginDuplicate('1')).toBe(true);
    });

    it('placeholder duplicate flag', () => {
        expect(isPlaceholderDuplicate(7)).toBe(false);
        markPlaceholderDuplicate(7);
        expect(isPlaceholderDuplicate(7)).toBe(true);
    });

    it('plugin and placeholder maps are independent', () => {
        markPluginDuplicate(5);
        expect(isPlaceholderDuplicate(5)).toBe(false);
    });

    it('clearDuplicateMarkers wipes both maps', () => {
        markPluginDuplicate(1);
        markPlaceholderDuplicate(2);
        clearDuplicateMarkers();
        expect(isPluginDuplicate(1)).toBe(false);
        expect(isPlaceholderDuplicate(2)).toBe(false);
    });
});

describe('registry — position math', () => {
    beforeEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
        _resetRegistryForTest();
        document.body.innerHTML = '';
    });

    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
        document.body.innerHTML = '';
    });

    function setupPlaceholder(placeholderId: number, pluginIds: number[]): PluginInstance[] {
        const dragarea = document.createElement('div');
        dragarea.className = `cms-dragarea-${placeholderId}`;
        const instances: PluginInstance[] = [];
        for (const id of pluginIds) {
            const draggable = document.createElement('div');
            draggable.className = `cms-draggable cms-draggable-${id}`;
            dragarea.appendChild(draggable);
            const inst = makeInstance({ plugin_id: id });
            instances.push(inst);
            addInstance(inst);
        }
        document.body.appendChild(dragarea);
        return instances;
    }

    it('updatePluginPositions assigns 1-based positions in DOM order', () => {
        const [a, b, c] = setupPlaceholder(10, [1, 2, 3]);
        updatePluginPositions(10);
        expect(a!.options.position).toBe(1);
        expect(b!.options.position).toBe(2);
        expect(c!.options.position).toBe(3);
    });

    it('updatePluginPositions skips drag elements that have no instance', () => {
        // Add a draggable element with no matching registry entry.
        const dragarea = document.createElement('div');
        dragarea.className = 'cms-dragarea-20';
        const orphan = document.createElement('div');
        orphan.className = 'cms-draggable cms-draggable-99';
        dragarea.appendChild(orphan);
        document.body.appendChild(dragarea);
        expect(() => updatePluginPositions(20)).not.toThrow();
    });

    it('updatePluginPositions skips drag elements whose class lacks an id', () => {
        const dragarea = document.createElement('div');
        dragarea.className = 'cms-dragarea-30';
        const malformed = document.createElement('div');
        malformed.className = 'cms-draggable'; // no -<id>
        dragarea.appendChild(malformed);
        document.body.appendChild(dragarea);
        expect(() => updatePluginPositions(30)).not.toThrow();
    });

    it('recalculatePluginPositions on MOVE recalculates every placeholder', () => {
        // Two placeholders, with plugin instances under each.
        const [pA1, pA2] = setupPlaceholder(1, [10, 20]);
        const [pB1] = setupPlaceholder(2, [30]);
        // Register placeholder instances so MOVE finds them.
        addInstance({ options: { type: 'placeholder', placeholder_id: 1 } });
        addInstance({ options: { type: 'placeholder', placeholder_id: 2 } });
        recalculatePluginPositions('MOVE', {});
        expect(pA1!.options.position).toBe(1);
        expect(pA2!.options.position).toBe(2);
        expect(pB1!.options.position).toBe(1);
    });

    it('recalculatePluginPositions on non-MOVE only recalculates the named placeholder', () => {
        const [pA1, pA2] = setupPlaceholder(1, [10, 20]);
        const [pB1] = setupPlaceholder(2, [30]);
        addInstance({ options: { type: 'placeholder', placeholder_id: 1 } });
        addInstance({ options: { type: 'placeholder', placeholder_id: 2 } });
        recalculatePluginPositions('ADD', { placeholder_id: 2 });
        expect(pA1!.options.position).toBeUndefined();
        expect(pA2!.options.position).toBeUndefined();
        expect(pB1!.options.position).toBe(1);
    });

    it('recalculatePluginPositions on non-MOVE without placeholder_id is a no-op', () => {
        const [pA1] = setupPlaceholder(1, [10]);
        recalculatePluginPositions('ADD', {});
        expect(pA1!.options.position).toBeUndefined();
    });
});

describe('registry — usage counter', () => {
    beforeEach(() => {
        _resetRegistryForTest();
    });

    afterEach(() => {
        _resetRegistryForTest();
    });

    it('starts empty', () => {
        expect(getUsageMap()).toEqual({});
    });

    it('bumpUsageCount increments per type', () => {
        bumpUsageCount('TextPlugin');
        bumpUsageCount('TextPlugin');
        bumpUsageCount('ImagePlugin');
        expect(getUsageMap()).toEqual({ TextPlugin: 2, ImagePlugin: 1 });
    });

    it('persists to localStorage', () => {
        bumpUsageCount('TextPlugin');
        const raw = localStorage.getItem('cms-plugin-usage');
        expect(raw).toBeTruthy();
        expect(JSON.parse(raw!)).toEqual({ TextPlugin: 1 });
    });

    it('getMostUsedPlugins returns top-N by count', () => {
        bumpUsageCount('A');
        bumpUsageCount('B');
        bumpUsageCount('B');
        bumpUsageCount('C');
        bumpUsageCount('C');
        bumpUsageCount('C');
        expect(getMostUsedPlugins(2)).toEqual(['C', 'B']);
        expect(getMostUsedPlugins(10)).toEqual(['C', 'B', 'A']);
    });

    it('getMostUsedPlugins handles an empty map', () => {
        expect(getMostUsedPlugins(5)).toEqual([]);
    });

    it('getUsageMap returns a snapshot — mutating it does not affect storage', () => {
        bumpUsageCount('Foo');
        const snap = getUsageMap();
        snap.Foo = 999;
        expect(getUsageMap()).toEqual({ Foo: 1 });
    });
});

/*
 * Plugin registry — the bookkeeping side of the plugins module.
 *
 * What lives here
 * ───────────────
 *   - The shared instance/descriptor lists (`CMS._instances` /
 *     `CMS._plugins`), accessed through `cms-globals` so legacy +
 *     structureboard see the same objects during the strangler period.
 *   - Plugin-by-id lookup (the legacy `Plugin._getPluginById`).
 *   - Position recalculation after MOVE/ADD/DELETE actions
 *     (`Plugin._updatePluginPositions` / `_recalculatePluginPositions`).
 *   - Duplicate-element guards: when the same plugin is rendered more
 *     than once (cms-plugin-start / -end template wrapping), only the
 *     first wrapper creates a real instance; subsequent constructor
 *     calls early-out via these maps.
 *   - Per-type usage counter persisted in `localStorage` under
 *     `cms-plugin-usage`, used by the picker to surface "most used"
 *     plugins.
 *
 * Pure data/logic — no DOM event wiring, no jQuery, no UI side
 * effects. Vitest covers it without jsdom mocking beyond simple DOM
 * fixtures for the position-math helper.
 */

import {
    getInstancesRegistry,
    getPluginsRegistry,
} from './cms-globals';
import type { PluginDescriptor, PluginInstance, PluginMutationAction, PluginOptions } from './types';

// ────────────────────────────────────────────────────────────────────
// Instance registry
// ────────────────────────────────────────────────────────────────────

/** Append a plugin instance to the shared registry. */
export function addInstance(instance: PluginInstance): void {
    getInstancesRegistry().push(instance);
}

/** Remove a plugin instance from the shared registry. No-op if missing. */
export function removeInstance(instance: PluginInstance): void {
    const reg = getInstancesRegistry();
    const idx = reg.indexOf(instance);
    if (idx >= 0) reg.splice(idx, 1);
}

/** Replace the entire instance registry. Used by `_initializeTree`. */
export function setInstances(instances: PluginInstance[]): void {
    const reg = getInstancesRegistry();
    reg.length = 0;
    reg.push(...instances);
}

/** Live registry — mutations are visible to legacy + structureboard. */
export function getAllInstances(): PluginInstance[] {
    return getInstancesRegistry();
}

/**
 * Find the plugin instance with `options.type === 'plugin'` and the
 * given `plugin_id`. Matches the legacy `Plugin._getPluginById`
 * behaviour: placeholders and generics are intentionally excluded.
 *
 * Number coercion handles the legacy mix of string / number ids in
 * the rendered descriptor blobs.
 */
export function findPluginById(id: number | string): PluginInstance | undefined {
    const target = Number(id);
    return getInstancesRegistry().find(
        (i) => i.options.type === 'plugin' && Number(i.options.plugin_id) === target,
    );
}

// ────────────────────────────────────────────────────────────────────
// Descriptor registry (`CMS._plugins`)
// ────────────────────────────────────────────────────────────────────

/** Replace the entire descriptor list. Used by `_initializeTree`. */
export function setDescriptors(descriptors: PluginDescriptor[]): void {
    const reg = getPluginsRegistry();
    reg.length = 0;
    reg.push(...descriptors);
}

/** Live descriptor list — read by `_refreshPlugins` and the toolbar. */
export function getAllDescriptors(): PluginDescriptor[] {
    return getPluginsRegistry();
}

/** Append a descriptor tuple. Idempotent merging is the caller's job. */
export function addDescriptor(descriptor: PluginDescriptor): void {
    getPluginsRegistry().push(descriptor);
}

// ────────────────────────────────────────────────────────────────────
// Position recalculation
// ────────────────────────────────────────────────────────────────────

/**
 * Read the plugin id from a `.cms-draggable-<id>` element by parsing
 * its class list. Replaces the legacy `CMS.API.StructureBoard.getId(el)`
 * call so the registry doesn't depend on structureboard for this
 * narrow, mechanical task.
 */
function getDraggablePluginId(el: Element): number | undefined {
    for (const cls of el.classList) {
        const match = cls.match(/^cms-draggable-(\d+)$/);
        if (match?.[1]) return Number(match[1]);
    }
    return undefined;
}

/**
 * Recompute `instance.options.position` for every draggable inside
 * the placeholder identified by `placeholderId`. Legacy: `Plugin.
 * _updatePluginPositions`. Mutates the live options objects in place
 * so the next persistence round serialises the new order.
 */
export function updatePluginPositions(placeholderId: number | string): void {
    const elements = document.querySelectorAll(
        `.cms-dragarea-${placeholderId} .cms-draggable`,
    );
    elements.forEach((el, index) => {
        const pluginId = getDraggablePluginId(el);
        if (pluginId === undefined) return;
        const instance = findPluginById(pluginId);
        if (!instance) return;
        instance.options.position = index + 1;
    });
}

/**
 * Recalculate positions after a mutation. For MOVE we don't know the
 * source placeholder, so we recompute every placeholder; for the rest
 * we touch only the placeholder that received the change. Legacy:
 * `Plugin._recalculatePluginPositions`.
 */
export function recalculatePluginPositions(
    action: PluginMutationAction,
    data: { placeholder_id?: number | string },
): void {
    if (action === 'MOVE') {
        getInstancesRegistry()
            .filter((i) => i.options.type === 'placeholder')
            .map((i) => i.options.placeholder_id)
            .forEach((id) => {
                if (id !== undefined && id !== null) {
                    updatePluginPositions(id);
                }
            });
        return;
    }
    if (data.placeholder_id !== undefined && data.placeholder_id !== null) {
        updatePluginPositions(data.placeholder_id);
    }
}

// ────────────────────────────────────────────────────────────────────
// Duplicate-render guards
// ────────────────────────────────────────────────────────────────────

const aliasPluginDuplicates = new Set<number>();
const placeholderDuplicates = new Set<number>();

export function isPluginDuplicate(pluginId: number | string): boolean {
    return aliasPluginDuplicates.has(Number(pluginId));
}

export function markPluginDuplicate(pluginId: number | string): void {
    aliasPluginDuplicates.add(Number(pluginId));
}

export function isPlaceholderDuplicate(placeholderId: number | string): boolean {
    return placeholderDuplicates.has(Number(placeholderId));
}

export function markPlaceholderDuplicate(placeholderId: number | string): void {
    placeholderDuplicates.add(Number(placeholderId));
}

/**
 * Reset the duplicate guards. Called at the start of `_refreshPlugins`
 * so a re-rendered structureboard doesn't inherit stale duplicate
 * markers.
 */
export function clearDuplicateMarkers(): void {
    aliasPluginDuplicates.clear();
    placeholderDuplicates.clear();
}

// ────────────────────────────────────────────────────────────────────
// Usage counter
// ────────────────────────────────────────────────────────────────────

const USAGE_KEY = 'cms-plugin-usage';

/**
 * Whether localStorage works (private browsing, denied permission, …).
 * Cached at module load — a runtime flip is not supported by the
 * legacy code either.
 */
const isStorageSupported: boolean = (() => {
    const probe = 'cms_plugin_registry_probe';
    try {
        localStorage.setItem(probe, probe);
        localStorage.removeItem(probe);
        return true;
    } catch {
        return false;
    }
})();

function loadUsageMap(): Record<string, number> {
    if (!isStorageSupported) return {};
    try {
        const raw = localStorage.getItem(USAGE_KEY);
        if (!raw) return {};
        const parsed = JSON.parse(raw);
        return typeof parsed === 'object' && parsed !== null
            ? (parsed as Record<string, number>)
            : {};
    } catch {
        return {};
    }
}

const usageMap: Record<string, number> = loadUsageMap();

/**
 * Increment the usage counter for `pluginType`. Persists to
 * localStorage when available; the in-memory map is updated either
 * way so the picker still gets a session-scoped most-used list.
 */
export function bumpUsageCount(pluginType: string): void {
    usageMap[pluginType] = (usageMap[pluginType] ?? 0) + 1;
    if (!isStorageSupported) return;
    try {
        localStorage.setItem(USAGE_KEY, JSON.stringify(usageMap));
    } catch {
        /* persistence failed at runtime — keep the in-memory count */
    }
}

/** Snapshot the current usage map (read-only copy). */
export function getUsageMap(): Record<string, number> {
    return { ...usageMap };
}

/**
 * Top-N plugin types by usage count, descending. Ties broken by
 * insertion order in the underlying object.
 */
export function getMostUsedPlugins(limit: number): string[] {
    return Object.entries(usageMap)
        .sort(([, a], [, b]) => b - a)
        .slice(0, limit)
        .map(([type]) => type);
}

/**
 * Test/migration hook: wipe the usage map (memory + localStorage).
 * Not part of the public API.
 */
export function _resetUsageForTest(): void {
    for (const key of Object.keys(usageMap)) delete usageMap[key];
    if (isStorageSupported) {
        try {
            localStorage.removeItem(USAGE_KEY);
        } catch {
            /* nothing to do */
        }
    }
}

// ────────────────────────────────────────────────────────────────────
// Test/migration hook for resetting the in-memory state. Useful in
// vitest where the module's module-level Sets are shared across tests.
// ────────────────────────────────────────────────────────────────────

export function _resetRegistryForTest(): void {
    clearDuplicateMarkers();
    _resetUsageForTest();
}

// Helper exposed for tests that want to drive the position math
// directly without setting up a CMS namespace.
export const _internals = { getDraggablePluginId };

export type { PluginOptions };

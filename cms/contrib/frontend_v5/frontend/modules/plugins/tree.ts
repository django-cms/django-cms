/*
 * Tree initialisation + refresh — the entry points legacy
 * `cms.structureboard.js` and module-load code call into.
 *
 * Mirrors:
 *   - `Plugin._initializeTree`  — first-load scan of every
 *     `<script data-cms-plugin|placeholder|general>` and bulk Plugin
 *     instantiation.
 *   - `Plugin._refreshPlugins`  — re-run setup after structureboard
 *     swaps the DOM (clears duplicate guards + re-enumerates generics).
 *   - `Plugin._updateRegistry`  — incremental upsert from a mutation
 *     response.
 *
 * What's intentionally *not* here:
 *   - DOM event wiring (in `ui/global-handlers.ts`).
 *   - Per-instance event wiring (Plugin class `_set*` methods).
 *   - HTTP transport (in `api.ts`).
 *
 * The Plugin class is imported lazily so this module can be unit-
 * tested without paying the import cost of every `ui/` submodule.
 */

import { ensurePluginDataArray, setPlaceholderData } from './cms-data';
import { getInstancesRegistry, getPluginsRegistry } from './cms-globals';
import { Plugin } from './plugin';
import {
    addInstance,
    clearDuplicateMarkers,
    findPluginById,
    setDescriptors,
    setInstances,
} from './registry';
import type { PluginDescriptor, PluginOptions } from './types';
import { initializeGlobalHandlers } from './ui/global-handlers';

/**
 * Scan the document for plugin descriptor scripts and create one
 * Plugin instance per descriptor. Replaces the legacy
 * `Plugin._initializeTree`.
 *
 * Each script is `<script type="application/json" id="..."
 * data-cms-{plugin|placeholder|general}>{...}</script>`. The id is
 * the container class the Plugin class queries against (e.g.
 * `cms-plugin-42`); the JSON body is the descriptor.
 *
 * Returns the freshly-created instance array (also stored on
 * `CMS._instances` via the registry).
 */
export function initializeTree(): Plugin[] {
    // Idempotent — only the first call wires document-level listeners.
    initializeGlobalHandlers();

    const descriptorMap: Record<string, PluginOptions> = {};
    document.body
        .querySelectorAll<HTMLScriptElement>(
            'script[data-cms-plugin], ' +
                'script[data-cms-placeholder], ' +
                'script[data-cms-general]',
        )
        .forEach((script) => {
            try {
                descriptorMap[script.id] = JSON.parse(
                    script.textContent || '{}',
                ) as PluginOptions;
            } catch {
                /* malformed descriptor — skip */
            }
        });

    const descriptors: PluginDescriptor[] = Object.entries(descriptorMap);
    setDescriptors(descriptors);

    const instances = descriptors.map(
        ([id, options]) => new Plugin(id, options),
    );
    setInstances(instances);
    return instances;
}

/**
 * Re-run the per-instance UI setup after structureboard swaps the
 * DOM. Mirrors legacy `_refreshPlugins`. Three passes:
 *   1. Placeholders — `_setupUI`, mirror data, `_setPlaceholder`.
 *   2. Plugins — `_setupUI`, push descriptor, `_setPluginContentEvents`.
 *      Structure-mode wiring is the structureboard's responsibility.
 *   3. Generics — upsert the descriptor + `_setGeneric`.
 *
 * Pre-pass: clears the duplicate guards (so a re-rendered tree
 * doesn't keep stale `aliasPluginDuplicatesMap` markers) and
 * re-enumerates generic descriptor scripts (front-end editable
 * fields are added to the page by the toolbar after first load).
 */
export function refreshPlugins(): void {
    clearDuplicateMarkers();

    // Append every generic descriptor that's on the page right now.
    // Legacy de-duplicates with `uniqWith(_, isEqual)`. We dedupe by
    // id since two generics with the same id but different options
    // shouldn't exist on a sane page.
    const seen = new Set<string>(getPluginsRegistry().map(([k]) => k));
    document.body
        .querySelectorAll<HTMLScriptElement>('script[data-cms-general]')
        .forEach((script) => {
            if (seen.has(script.id)) return;
            try {
                const opts = JSON.parse(
                    script.textContent || '{}',
                ) as PluginOptions;
                getPluginsRegistry().push([script.id, opts]);
                seen.add(script.id);
            } catch {
                /* malformed — skip */
            }
        });

    const instances = getInstancesRegistry();

    // Pass 1: placeholders.
    for (const instance of instances) {
        if (instance.options.type !== 'placeholder') continue;
        const plugin = instance as Plugin;
        plugin._setupUI(`cms-placeholder-${plugin.options.placeholder_id}`);
        plugin._ensureData();
        if (plugin.ui.container?.[0]) {
            setPlaceholderData(plugin.ui.container[0], plugin.options);
        }
        plugin._setPlaceholder();
    }

    // Pass 2: plugins.
    for (const instance of instances) {
        if (instance.options.type !== 'plugin') continue;
        const plugin = instance as Plugin;
        plugin._setupUI(`cms-plugin-${plugin.options.plugin_id}`);
        plugin._ensureData();
        if (plugin.ui.container?.[0]) {
            ensurePluginDataArray(plugin.ui.container[0]).push(plugin.options);
        }
        plugin._setPluginContentEvents();
    }

    // Pass 3: generics. Upsert from the descriptor list.
    for (const [id, options] of getPluginsRegistry()) {
        if (options.type === 'placeholder' || options.type === 'plugin') continue;
        const existing = instances.find(
            (i) =>
                i.options.type === options.type &&
                Number(i.options.plugin_id) === Number(options.plugin_id),
        );
        if (existing) {
            const plugin = existing as Plugin;
            plugin._setupUI(id);
            plugin._ensureData();
            if (plugin.ui.container?.[0]) {
                ensurePluginDataArray(plugin.ui.container[0]).push(plugin.options);
            }
            plugin._setGeneric();
        } else {
            addInstance(new Plugin(id, options));
        }
    }
}

/**
 * Apply a list of mutation-flow plugin descriptors back into the
 * registry. For each descriptor: replace the matching `[id, opts]`
 * tuple in `CMS._plugins` and the matching instance in
 * `CMS._instances`, or append both if there's no existing entry.
 *
 * Mirrors legacy `Plugin._updateRegistry`. Used by structureboard
 * after a copy / paste / move response comes back with one or more
 * affected plugin descriptors.
 */
export function updateRegistry(plugins: PluginOptions[]): void {
    for (const descriptor of plugins) {
        const id = `cms-plugin-${descriptor.plugin_id}`;
        const descriptors = getPluginsRegistry();
        const idx = descriptors.findIndex(([key]) => key === id);
        if (idx === -1) {
            descriptors.push([id, descriptor]);
            addInstance(new Plugin(id, descriptor));
            continue;
        }
        // Replace existing descriptor + instance in place.
        descriptors[idx] = [id, descriptor];
        const instances = getInstancesRegistry();
        const instanceIdx = instances.findIndex(
            (i) =>
                i.options.type === descriptor.type &&
                Number(i.options.plugin_id) === Number(descriptor.plugin_id),
        );
        if (instanceIdx >= 0) {
            instances[instanceIdx] = new Plugin(id, descriptor);
        } else {
            addInstance(new Plugin(id, descriptor));
        }
    }
}

/**
 * Re-export the legacy `_getPluginById` shape — `findPluginById`
 * lives in the registry but legacy callers (structureboard) read
 * `CMS.Plugin._getPluginById`. Wired in `bundles/admin.toolbar.ts`
 * when the bundle entry is added (Phase 4).
 */
export { findPluginById };

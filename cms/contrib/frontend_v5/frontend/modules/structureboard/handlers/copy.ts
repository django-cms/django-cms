/*
 * COPY plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleCopyPlugin`. The server returns
 * fresh clipboard markup + an updated descriptor for the copied
 * plugin. We:
 *
 *   1. Replace `.cms-clipboard-containers` with the new HTML.
 *   2. Push the new descriptor + Plugin instance into the registries
 *      (via `updateRegistry`).
 *   3. Dispatch `cms-clipboard-update` so the (yet-unported) clipboard
 *      module can re-bind its modal triggers and `populate()` call.
 *
 * What we explicitly DON'T do (handled by the clipboard module when
 * it ports — Phase 4):
 *   - Re-clone the `.cms-clipboard` for jQuery event-cache refresh.
 *   - Instantiate `new CMS.API.Clipboard()`.
 *   - Call `Clipboard.populate(html, descriptor)` /
 *     `Clipboard._enableTriggers()`.
 *   - Open/close the clipboard modal.
 *
 * The dispatcher in `invalidate.ts` short-circuits any content-refresh
 * for COPY (legacy: `updateNeeded = false`). COPY only changes the
 * clipboard, not visible page content.
 */

import { updateRegistry } from '../../plugins/tree';
import type { PluginOptions } from '../../plugins/types';

export interface CopyPluginData {
    html?: string;
    plugins?: PluginOptions[];
    [key: string]: unknown;
}

export function handleCopyPlugin(data: CopyPluginData): void {
    const html = data.html;
    const containers = document.querySelector<HTMLElement>(
        '.cms-clipboard-containers',
    );
    if (containers && html) {
        containers.innerHTML = html;
    }

    const plugins = data.plugins ?? [];
    if (plugins.length > 0) {
        updateRegistry(plugins);
    }

    // Hand off to whoever owns clipboard chrome (legacy bundle
    // listens; the ported clipboard module — Phase 4 — will replace
    // the listener).
    document.dispatchEvent(new CustomEvent('cms-clipboard-update', { detail: data }));
}

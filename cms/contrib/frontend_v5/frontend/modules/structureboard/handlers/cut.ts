/*
 * CUT plugin handler.
 *
 * Mirrors legacy `StructureBoard.handleCutPlugin`. Cut = delete from
 * the source placeholder + put a copy on the clipboard. Composes
 * `handleDeletePlugin` and `handleCopyPlugin` directly — the order
 * matches legacy and the registry mutation is sequenced so the
 * COPY's `updateRegistry` re-adds the descriptor that DELETE just
 * dropped (cut leaves the plugin in the registry as a clipboard
 * item, not as a placed plugin).
 */

import { handleCopyPlugin, type CopyPluginData } from './copy';
import { handleDeletePlugin, type DeletePluginData } from './delete';

export type CutPluginData = DeletePluginData & CopyPluginData;

export function handleCutPlugin(data: CutPluginData): void {
    handleDeletePlugin(data);
    handleCopyPlugin(data);
}

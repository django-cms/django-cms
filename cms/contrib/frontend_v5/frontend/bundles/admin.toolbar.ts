/*
 * Entry stub for the admin.toolbar bundle.
 *
 * Drop-in replacement for the legacy `bundle.toolbar.min.js` will be
 * assembled here as the remaining toolbar pieces (cms.modal,
 * cms.toolbar, cms.messages, cms.tooltip, cms.changetracker, the
 * keyboard/scrollbar/trap helpers) port over. Today we ship only the
 * structureboard half — `window.CMS.API.StructureBoard` — so that
 * pages depending on the structureboard surface get the TS port even
 * while the legacy `cms.plugins.js` / `cms.toolbar.js` continue to
 * serve.
 *
 * On DOM-ready the StructureBoard class self-instantiates and exposes
 * itself on `window.CMS.API.StructureBoard`, matching the legacy
 * boot order.
 *
 * NOTE: This bundle is NOT yet listed in `webpack.config.js`'s
 * entry map — adding it would shadow the legacy
 * `bundle.toolbar.min.js` (which still owns the modal, toolbar, etc.
 * surfaces). Wire it up once the remaining toolbar bundles port
 * through 3j+.
 */

import { StructureBoard } from '../modules/structureboard/structureboard';

function instantiate(): void {
    window.CMS = window.CMS ?? {};
    window.CMS.API = window.CMS.API ?? {};
    if (window.CMS.API.StructureBoard) return;
    // The constructor wires every listener — DOM-ready guarantees the
    // toolbar markup is present. Cast through `unknown` because the
    // global `CmsApi.StructureBoard` field is typed as the legacy
    // duck-typed shape; the class implements that surface but TS
    // can't infer the structural compatibility automatically.
    (window.CMS.API as { StructureBoard?: unknown }).StructureBoard =
        new StructureBoard();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', instantiate, { once: true });
} else {
    instantiate();
}

export { StructureBoard };
export default StructureBoard;

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo layout in one sentence

This is the django-cms Python package; the active TypeScript frontend port lives in `cms/contrib/frontend_v5/` as a Django contrib app that ships drop-in replacement bundles, while the legacy jQuery frontend in `cms/static/cms/js/` and the root `webpack.config.js` / `gulpfile.js` remain untouched.

## Common commands

Run from repo root. The contrib app shares the root `node_modules` — no nested `npm install`.

```
npm run build:v5           # production build (webpack + sass + vendor copy)
npm run v5 -- build:dev    # dev build with sourcemaps
npm run v5 -- watch        # webpack watch mode
npm run v5 -- sass         # one-shot SCSS compile
npm run typecheck:v5       # tsc --noEmit
npm run test:v5            # vitest run (unit)
npm run test:v5:watch      # vitest watch
npm run test:v5:e2e        # Playwright (uses contrib's playwright.config.js)
```

Single vitest file: `npm run test:v5:watch -- frontend/modules/pagetree.ts`
Single Playwright spec: `npm run test:v5:e2e -- pagetree.spec.js`

The contrib bundles emit to `cms/contrib/frontend_v5/static/cms/js/dist/<CMS_VERSION>/` with the **same filenames** as legacy bundles (`bundle.admin.pagetree.min.js`, etc.). Django staticfiles serves them at the same URLs as the legacy ones when `cms.contrib.frontend_v5` is listed **before** `cms` in `INSTALLED_APPS` — that's the entire override mechanism. Do not change bundle filenames or output paths.

Python tests still use the existing root setup (`pytest`, `manage.py test`); the contrib app is JS/TS/SCSS only.

## Architectural decisions (the "why")

These are constraints that aren't visible from a single file. Read this before changing the listed subsystem.

### 1. Drop-in via app ordering, not template edits

The contrib app does not override Django templates or URLs — it only ships `static/` files with paths matching legacy. Adding a feature that requires a template change means either: (a) adding a template override to `cms/contrib/frontend_v5/templates/`, accepting that this template now also has to be maintained against upstream `cms/templates/` drift, or (b) pushing the change upstream into `cms/templates/` and keeping the contrib app's footprint to assets only. Prefer (b) unless the change is contrib-specific.

The one current template override is `templates/admin/cms/page/tree/menu.html` — minimal customisations only.

**Inline `<style>` blocks in overridden templates are forbidden.** They re-leak legacy SortableJS rules / drag-reveal hacks that conflict with the new TreeDrag controller and CSS. Keep all styling in `frontend/sass/`.

### 2. Pagetree DOM is nested `<ul>`, not the legacy table

The legacy pagetree was a `<table>` with parent/child rows wired up by jstree. The new DOM is `<ul role="tree"> > <li role="treeitem"> > .cms-tree-row + <ul role="group">` with indentation via `padding-inline-start: 24px` on the nested `<ul>`. Background colour is on `.cms-tree-row` so nested padding doesn't bleed.

Implications:
- Don't put block elements inside `<ul>` directly — browsers insert anonymous list-item boxes that cause unexpected reflow during drag. The TreeDrag clone and drop-marker live in `container.parentElement`, not inside the tree `<ul>`.
- Server-side rendering pre-wraps each row in `<div class="cms-tree-col">`. The JS hoists that wrapper directly via `parser.firstElementChild` — don't wrap again.
- Padding columns (`.cms-tree-col-padding-sm`) need flex centering, not the legacy `display: table-cell` (no `display: table` ancestor in the new DOM).

### 3. Custom TreeDrag controller (no SortableJS)

`frontend/modules/tree/drag.ts` (~370 LoC) is a hand-rolled pointer-events DnD controller. SortableJS was tried and removed because its "mutate the DOM during drag" model fights the desired jsTree-style UX (render a prospective marker, commit on drop). TreeDrag is the canonical pattern for any future tree-shaped DnD in this codebase (plugin tree, structureboard).

The "Drop on row = child" UX has three affordances:
- **Highlight** — middle 50% of a row → drop as first child
- **Line marker** — between siblings, depth picked from cursor `clientX` ÷ `depthPx`, clamped to legal range (cannot escape parent into root unless dragging from root)
- **Drag clone** — wrapped in `<ul class="cms-pagetree-list cms-tree-drag-clone"><li>…</li></ul>` shell so the SCSS cascade applies; parented to `container.parentElement` (not `<body>`) so component-scoped styles still hit it. Touch support is required — do not switch to HTML5 drag-and-drop.

Server-side gotcha: `PageTreeForm` indexes `position` against the **pre-move** sibling queryset, which **includes** the dragged item. When computing position from the new sibling list, include the dragged node in the count.

### 4. `jsonify_request` envelope

`cms/utils/admin.py::jsonify_request` wraps every response — including errors — as HTTP 200 with body `{status, content}`. Do NOT trust `response.ok` for tree mutation endpoints. Parse the JSON envelope and check the inner `status`. See `postTreeMutation` in `pagetree.ts` for the pattern. Errors come back as Django `ErrorList` HTML; strip the inner `<li>` and inject into the messagelist `<ul>` template — don't render the raw HTML, don't escape it.

### 5. SCSS forking strategy

Pagetree SCSS was forked because the new DOM doesn't match legacy table semantics. Active partials are under `frontend/sass/components/pagetree/` with `_tree-new-dom.scss` carrying everything specific to the nested-ul layout. Top-level entry is `frontend/sass/cms.pagetree.scss`. The other modules (changeform, base, widgets) currently still use legacy CSS via the staticfiles drop-in — only fork SCSS once the new module reaches feature parity for its bundle.

A few SCSS gotchas the legacy code mostly hid:
- `$padding-small` / `$font-weight-medium` don't exist; use `$padding-base` and literal `500`.
- `color.adjust` doesn't accept CSS variables; use `color-mix` for runtime-themable colours.
- `filter: drop-shadow()` follows alpha shapes — use it for the dropdown anchor triangle (border-triangle technique). `box-shadow` on a triangle bleeds inside the bounding rect.

### 6. Test layout

Vitest unit tests under `tests/unit/` mirror `frontend/modules/`. Playwright integration tests under `tests/integration/` use a real Django dev server (started by Playwright's `webServer` config) and exercise rendered admin pages. CI runs both.

### 7. plugins.ts is dev-only — does NOT ship in a bundle yet

`frontend/modules/plugins.ts` (~2360 LoC) is the TS port of `cms.plugins.js`. Feature-complete and exercised by 68 vitest tests, but **no webpack entry references it**. The legacy `cms.plugins.js` is bundled inside `bundle.toolbar.min.js` together with `cms.structureboard.js`, `cms.modal.js`, `cms.toolbar.js`, `cms.clipboard.js`, etc. — there is no per-module bundle to drop in. Until structureboard ports and we can ship the whole toolbar bundle as a unit, plugins.ts proves the model in isolation; runtime users still get the legacy plugins.js from the legacy bundle.

The class talks to legacy globals (`window.CMS.Modal`, `window.CMS.API.StructureBoard`, `window.CMS.API.Messages`, etc.) and is a no-op when those globals are absent — so it survives in the isolated vitest environment without stubbing every dependency.

File layout:
- `frontend/modules/plugins.ts` — the `Plugin` class proper
- `frontend/modules/plugins/cms-globals.ts` — every `window.CMS.X` lookup (`getCmsNamespace`, `isStructureReady`, `LegacyModal` interface). When the legacy bundle is dropped, **this is the file that changes**.
- `frontend/modules/plugins/global-handlers.ts` — `_initializeGlobalHandlers` body. Receives `Plugin` as a DI parameter to avoid a circular import.

Two legacy footguns the port preserves:
- `find('> .cms-dragitem')` — Sizzle's relative-child selector matches **descendants** too, not just direct children. Use `.children('.cms-dragitem')` in TS code (legacy got away with it via timing/empty-children differences in real browsers). Same for `> .cms-draggables`, `> .cms-dragitem-text`, `> .cms-collapsable-container`.
- `data('cms')` shape differs by plugin type: placeholders store a single object; plugins/generics store an array (the same DOM node may carry several descriptors when content is reused). Readers do `[0]` to get the first.

## Current port status

| Bundle | Status |
| --- | --- |
| `admin.base` + `cms-base` + `loader` | shipped |
| `admin.changeform` | shipped |
| `forms.pageselectwidget` | shipped |
| `forms.slugwidget` | shipped |
| `forms.apphookselect` | shipped |
| `admin.pagetree` | shipped (read, drag, dropdowns, search, paste/copy/cut, custom DnD) |
| `cms.plugins` | shipped (in `bundle.toolbar.min.js`) — feature-complete, vitest-tested. |
| `cms.structureboard` | shipped (in `bundle.toolbar.min.js`) — phases 5a–5g. `_updateContentFromDataBridge` fast-path and `_showAndHighlightPlugin` are partial stubs (functional fallbacks). |
| `cms.modal` | shipped (in `bundle.toolbar.min.js`) — iframe + markup modes, drag/resize, ChangeTracker, ctrl/cmd+enter save. |
| `cms.toolbar` | shipped (in `bundle.toolbar.min.js`) — nav menus, action delegation, `_refreshMarkup`, openAjax. `cms.navigation` (responsive overflow) is a stub. |
| `cms.messages` | shipped (in `bundle.toolbar.min.js`). |
| `cms.tooltip` | shipped (in `bundle.toolbar.min.js`). |
| `cms.changetracker` | shipped (in `bundle.toolbar.min.js`). |
| `keyboard` / `scrollbar` / `trap` | shipped (in `bundle.toolbar.min.js`). |
| `cms.sideframe` | NOT ported — toolbar checks for `window.CMS.Sideframe` at runtime; falls back to plain navigation. Apphook config / page history pages affected. |
| `cms.clipboard` | NOT ported — structureboard's copy/cut still populate the DOM, but the clipboard widget's drag triggers don't bind. |
| `cms.navigation` | NOT ported — toolbar uses an inline stub satisfying the API surface. Narrow-screen overflow handling not yet implemented. |
| `forms.pagesmartlinkwidget` | out of scope (#26) |

CSS: pagetree SCSS forked and shipping via `cms.pagetree.scss`. Other bundles still use legacy CSS through the staticfiles drop-in.

Deferred polish on plugins.ts (small, low-risk; pick up before wiring into the toolbar bundle):
- `_setAddPluginModal` — picker click wiring; for now the menu delegate's `add` action handles all add-plugin paths.
- Picker keyboard nav (arrow up/down through `.cms-submenu-item:visible`).
- `_setSettings(old, new)` — settings-update method called after edit modal save; bound up with structureboard's `invalidateState` flow.

Tracker items deferred:
- #28 "Add permission" buttons on advanced settings — out of scope for this port.
- #29 hidden-row cleanup is a workaround, not a feature — revisit once structureboard lands.
- #34 Switch event bus from jQuery `.on/.trigger` to native `CustomEvent` — blocked until **all** downstream bundles are TS-ported (legacy bundles still listen on the jQuery bus).

## Next steps (suggested order)

1. **In-browser testing** — `bundle.toolbar.min.js` is built and ships via the contrib drop-in. Smoke-test on a live admin page: open a plugin edit modal, save, verify structure refresh, drag plugins between placeholders, toggle structure/content modes.
2. **Sideframe + Clipboard ports** — close the remaining drop-in gaps. Sideframe (~446 LoC) unblocks apphook config / page history. Clipboard (~270 LoC) unblocks the toolbar clipboard widget UX (cut/copy/paste between placeholders works without it but is less discoverable).
3. **Navigation port** — ~385 LoC responsive overflow handler. Currently stubbed; matters when narrow-screen toolbar UX becomes a priority.
4. **structureboard polish** — `_updateContentFromDataBridge` fast-path (avoids full content re-fetch when the data bridge carries rendered HTML), `_showAndHighlightPlugin` (now that Tooltip is ported, can wire shift+space), 5h Playwright integration tests.
5. **Event bus migration** (#34) — only after every bundle above is on TS (no more jQuery-bus listeners in the legacy world).
6. **Root promotion** — fold `cms.contrib.frontend_v5/` back into `cms/` once at parity, drop legacy `webpack.config.js` / `gulpfile.js`.

Confirm scope with the user before starting any of these — none have been explicitly requested yet.

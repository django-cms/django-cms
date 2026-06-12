/*
 * Shortcuts help modal — port of `cms/static/cms/js/modules/shortcuts/help.js`.
 *
 * Two trigger paths, both opening a modal that lists every CMS-wide
 * keyboard shortcut grouped by area (data lives in
 * `CMS.config.lang.shortcutAreas`, populated by the toolbar template):
 *
 *   - `?` keyboard shortcut (default `cms` keyboard context)
 *   - `pointerup` on any `.cms-show-shortcuts` element (the
 *     "Shortcuts..." item in the admin menu)
 *
 * The legacy bundle pulled the body markup from a webpack-loaded
 * `help.html` partial; contrib's webpack has no html-loader, so the
 * template is inlined here. We render manually instead of using
 * lodash's `template()` to keep the bundle small and avoid eval.
 */
import { escape } from 'lodash-es';

import { Modal } from './modal/modal';
import * as keyboard from './keyboard';

interface ShortcutEntry {
    shortcut: string;
    desc: string;
}

interface ShortcutArea {
    title: string;
    shortcuts: Record<string, ShortcutEntry>;
}

interface ShortcutLang {
    shortcuts?: string;
    shortcutAreas?: ShortcutArea[];
}

function getLang(): ShortcutLang {
    const cms = window.CMS as { config?: { lang?: ShortcutLang } } | undefined;
    return cms?.config?.lang ?? {};
}

function renderHelpHtml(areas: ShortcutArea[]): string {
    const rows = areas
        .map((area) => {
            const header = `
                <tr>
                    <th></th>
                    <th class="cms-shortcut-key-wrapper"><h2>${escape(area.title)}</h2></th>
                </tr>`;
            const items = Object.values(area.shortcuts)
                .map((entry) => {
                    const keys = entry.shortcut
                        .replace(/>/g, '')
                        .split(' / ')
                        .map((k, i) => {
                            const sep = i === 1 ? ' / ' : '';
                            return `${sep}<kbd class="cms-shortcut-key">${escape(k.trim())}</kbd>`;
                        })
                        .join('');
                    return `
                        <tr class="cms-shortcut">
                            <td class="cms-shortcut-key-wrapper">${keys}</td>
                            <td class="cms-shortcut-desc">${escape(entry.desc)}</td>
                        </tr>`;
                })
                .join('');
            return header + items;
        })
        .join('');
    return `
        <div class="cms-shortcuts">
            <div class="cms-shortcuts-list-wrapper">
                <table class="cms-shortcuts-list">${rows}</table>
            </div>
        </div>`;
}

export interface ShortcutsHandle {
    destroy(): void;
}

/**
 * Bind the `?` keyboard shortcut and `.cms-show-shortcuts` click
 * handler. Idempotent guards live at the call site
 * (`admin.toolbar.ts::boot`); calling twice doubles handlers.
 */
export function initShortcuts(): ShortcutsHandle {
    const lang = getLang();
    const areas = lang.shortcutAreas ?? [];

    let modal: Modal | null = null;
    try {
        modal = new Modal({
            resizable: false,
            minimizable: false,
            maximizable: false,
        });
    } catch {
        // No `.cms-modal` markup on the page (e.g. contrib-only admin
        // pages without a toolbar). Skip — there's nothing to open.
        return { destroy: () => {} };
    }

    function open(e: Event): void {
        e.preventDefault();
        modal?.open({
            title: lang.shortcuts ?? 'Shortcuts',
            width: 600,
            height: 660,
            html: renderHelpHtml(areas),
        });
    }

    keyboard.setContext('cms');
    keyboard.bind('?', open);

    const onPointerUp = (e: Event): void => {
        const target = e.target as Element | null;
        const trigger = target?.closest('.cms-show-shortcuts');
        if (trigger) open(e);
    };
    document.addEventListener('pointerup', onPointerUp);

    return {
        destroy(): void {
            document.removeEventListener('pointerup', onPointerUp);
        },
    };
}

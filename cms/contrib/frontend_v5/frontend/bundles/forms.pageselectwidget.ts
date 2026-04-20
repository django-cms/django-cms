/*
 * Entry point for the forms.pageselectwidget bundle.
 *
 * Drop-in replacement for the legacy bundle.forms.pageselectwidget.min.js.
 * Reads the widget config JSON embedded inside
 * <div data-cms-widget-pageselect><script type="application/json">{...}</script></div>
 * and instantiates a PageSelectWidget per wrapper.
 *
 * Also exposes `window.CMS.PageSelectWidget` for third-party code that
 * may instantiate the widget programmatically (legacy public API).
 */

import { PageSelectWidget, type PageSelectWidgetOptions } from '../modules/page-select-widget';

window.CMS = window.CMS ?? {};
window.CMS.PageSelectWidget = PageSelectWidget;

function init(): void {
    const wrappers = document.querySelectorAll<HTMLElement>('[data-cms-widget-pageselect]');
    for (const wrapper of Array.from(wrappers)) {
        const script = wrapper.querySelector('script');
        if (!script?.textContent) continue;
        try {
            const options = JSON.parse(script.textContent) as PageSelectWidgetOptions;
            new PageSelectWidget(options);
        } catch (err) {
            // Don't let one malformed wrapper crash the page — the legacy
            // code would have failed silently on parse errors too.
            // eslint-disable-next-line no-console
            console.error('forms.pageselectwidget: failed to parse widget config', err);
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
    init();
}

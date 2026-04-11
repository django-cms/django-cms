/*
 * Entry point for the forms.apphookselect bundle.
 *
 * Drop-in replacement for the legacy bundle.forms.apphookselect.min.js.
 * Reads the apphook config JSON from
 * <div data-cms-widget-applicationconfigselect><script>{...}</script></div>
 * and wires up the apphook select.
 */

import { initApphookSelect, type ApphookWidgetData } from '../modules/apphook-select';

function readWidgetData(): ApphookWidgetData | undefined {
    const wrapper = document.querySelector('div[data-cms-widget-applicationconfigselect]');
    const script = wrapper?.querySelector('script');
    if (!script?.textContent) return undefined;
    try {
        return JSON.parse(script.textContent) as ApphookWidgetData;
    } catch (err) {
        // eslint-disable-next-line no-console
        console.error('forms.apphookselect: failed to parse widget config', err);
        return undefined;
    }
}

function init(): void {
    initApphookSelect(readWidgetData());
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
    init();
}

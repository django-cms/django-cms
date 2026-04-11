/*
 * Apphook-aware namespace/config visibility widget.
 *
 * Port of the legacy `forms.apphookselect.js`. Semantics preserved, with
 * ONE intentional bug fix documented inline (see `originalApphook`).
 *
 * The widget runs on the page advanced-settings admin form. When the
 * user picks a different "application" (apphook) from the main select,
 * we need to:
 *
 *   - Show the matching "config" select, pre-filling it with the configs
 *     registered for that apphook. Config is a secondary choice tied to
 *     the apphook — e.g. a News apphook might offer "news-blog" and
 *     "news-press" as configs.
 *   - OR, if the apphook has no configs but declares a default namespace
 *     (via a `data-namespace` attr on its `<option>`), show the namespace
 *     input and pre-fill it.
 *   - OR hide both rows entirely.
 *
 * The "config" data is rendered server-side as an embedded JSON blob
 * inside `<div data-cms-widget-applicationconfigselect>`; we parse it
 * once on init.
 */

/**
 * Shape of the embedded JSON config for this widget. Produced by the
 * matching Django form widget in `cms/forms/widgets.py`.
 */
export interface ApphookWidgetData {
    /** apphook name → list of [config_value, config_label] pairs. */
    apphooks_configuration: Record<string, Array<[string, string]>>;
    /** The initially-selected config value, if any. */
    apphooks_configuration_value?: string;
    /** apphook name → URL of the "add new config" admin page. */
    apphooks_configuration_url: Record<string, string>;
}

const DEFAULT_DATA: ApphookWidgetData = {
    apphooks_configuration: {},
    apphooks_configuration_url: {},
};

export interface ApphookSelectHandle {
    destroy(): void;
}

/**
 * Wire up the apphook select widget against the current document. Call
 * once from the bundle entry; idempotent behavior is not guaranteed
 * (don't call twice without `destroy()`ing the first handle).
 */
export function initApphookSelect(data: ApphookWidgetData = DEFAULT_DATA): ApphookSelectHandle {
    const apphooks_configuration = data.apphooks_configuration ?? {};

    // The admin form has TWO naming conventions depending on whether the
    // form is rendered through the model admin or a raw form — try both.
    const appHooks = document.querySelector<HTMLSelectElement>(
        '#application_urls, #id_application_urls',
    );
    const appNsRow = document.querySelector<HTMLElement>(
        '.form-row.application_namespace, .form-row.field-application_namespace',
    );
    const appNs = appNsRow?.querySelector<HTMLInputElement>(
        '#application_namespace, #id_application_namespace',
    ) ?? null;
    const appCfgsRow = document.querySelector<HTMLElement>(
        '.form-row.application_configs, .form-row.field-application_configs',
    );
    const appCfgs = appCfgsRow?.querySelector<HTMLSelectElement>(
        '#application_configs, #id_application_configs',
    ) ?? null;
    const appCfgsAdd = appCfgsRow?.querySelector<HTMLAnchorElement>('#add_application_configs')
        ?? null;

    // FIX vs. legacy: the legacy code stored `original_ns = appNs.value`
    // and later compared `opt.value === original_ns` — comparing an
    // apphook name to a namespace string, which is nonsensical and would
    // only ever match by accident. The intent was clearly "remember the
    // original apphook so we can restore its namespace when the user
    // reverts". We remember BOTH original values and compare the apphook
    // name against the apphook name. This fixes the "revert to original
    // restores namespace" feature that the legacy code had dormantly
    // broken.
    const originalApphook = appHooks?.value ?? '';
    const originalNamespace = appNs?.value ?? '';

    const getSelectedOption = (select: HTMLSelectElement | null): HTMLOptionElement | null =>
        select && select.selectedIndex >= 0 ? select.options[select.selectedIndex] ?? null : null;

    // eslint-disable-next-line complexity
    const setupNamespaces = (): void => {
        const opt = getSelectedOption(appHooks);
        const opts = opt ? apphooks_configuration[opt.value] : undefined;

        if (appCfgs && opt && opts) {
            // Rebuild the config select from the data for this apphook.
            appCfgs.innerHTML = '';
            for (const [value, label] of opts) {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = label;
                if (value === data.apphooks_configuration_value) {
                    option.selected = true;
                }
                appCfgs.appendChild(option);
            }

            if (appCfgsAdd) {
                const base = data.apphooks_configuration_url[opt.value] ?? '';
                // Modern Django admin uses showRelatedObjectPopup; the
                // presence of that global also signals that _popup=1 is
                // the right query flag to trigger the popup dialog.
                appCfgsAdd.setAttribute(
                    'href',
                    base + (window.showRelatedObjectPopup ? '?_popup=1' : ''),
                );
                appCfgsAdd.addEventListener('click', onAddClick);
            }

            appCfgsRow?.classList.remove('hidden');
            appNsRow?.classList.add('hidden');
            return;
        }

        // No config set for this apphook. Fall through: maybe it has a
        // default namespace instead.
        appCfgsRow?.classList.add('hidden');
        if (opt && opt.dataset.namespace && appNsRow) {
            appNsRow.classList.remove('hidden');
        } else {
            appNsRow?.classList.add('hidden');
        }
    };

    const onAddClick = (ev: Event): void => {
        ev.preventDefault();
        const target = ev.currentTarget;
        if (target instanceof HTMLElement && window.showAddAnotherPopup) {
            window.showAddAnotherPopup(target);
        }
    };

    // eslint-disable-next-line complexity
    const onApphookChange = (): void => {
        const opt = getSelectedOption(appHooks);
        setupNamespaces();

        if (!appNs) return;

        // User cleared the apphook → clear the namespace.
        if (!appHooks?.value) {
            appNs.value = '';
            appNs.removeAttribute('value');
            return;
        }

        if (opt && originalApphook && opt.value === originalApphook) {
            // Reverted to the original apphook → restore the namespace
            // the form was loaded with.
            appNs.value = originalNamespace;
        } else if (opt && opt.dataset.namespace) {
            // New apphook with a default namespace → use it.
            appNs.value = opt.dataset.namespace;
        } else {
            // Otherwise wipe — no sensible default to offer.
            appNs.value = '';
            appNs.removeAttribute('value');
        }
    };

    // Initial pass so the DOM is consistent with the preselected apphook
    // when the form first renders (or re-renders after a validation error).
    setupNamespaces();

    if (appHooks) {
        appHooks.addEventListener('change', onApphookChange);
    }

    return {
        destroy() {
            appHooks?.removeEventListener('change', onApphookChange);
            appCfgsAdd?.removeEventListener('click', onAddClick);
        },
    };
}

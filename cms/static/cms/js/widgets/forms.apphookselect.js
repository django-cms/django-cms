/*
 * APP HOOK SELECT
 * ===============
 * Copyright https://github.com/django-cms/django-cms
 */


let apphookData = {
    apphooks_configuration: {},
    apphooks_configuration_value: undefined,
    apphooks_configuration_url: {}
};

document.addEventListener('DOMContentLoaded', function () {
    const dataElement = document.querySelector('div[data-cms-widget-applicationconfigselect]');

    if (dataElement) {
        apphookData = JSON.parse(dataElement.querySelector('script').textContent);
    }
    const apphooks_configuration = apphookData.apphooks_configuration || {};

    // Select elements
    const appHooks = document.querySelector('#application_urls, #id_application_urls');
    const appNsRow = document.querySelector('.form-row.application_namespace, .form-row.field-application_namespace');
    const appNs = appNsRow ? appNsRow.querySelector('#application_namespace, #id_application_namespace') : null;
    const appCfgsRow = document.querySelector('.form-row.application_configs, .form-row.field-application_configs');
    const appCfgs = appCfgsRow ? appCfgsRow.querySelector('#application_configs, #id_application_configs') : null;
    const appCfgsAdd = appCfgsRow ? appCfgsRow.querySelector('#add_application_configs') : null;
    const original_ns = appNs ? appNs.value : '';

    // Helper: get selected option
    function getSelectedOption(select) {
        return select ? select.options[select.selectedIndex] : null;
    }

    // Shows / hides namespace / config selection widgets depending on the user input
    // eslint-disable-next-line complexity
    function setupNamespaces() {
        const opt = getSelectedOption(appHooks);

        if (appCfgs && apphooks_configuration[opt.value]) {
            appCfgs.innerHTML = '';
            for (let i = 0; i < apphooks_configuration[opt.value].length; i++) {
                const cfg = apphooks_configuration[opt.value][i];
                const option = document.createElement('option');

                option.value = cfg[0];
                option.textContent = cfg[1];
                if (cfg[0] === apphookData.apphooks_configuration_value) {
                    option.selected = true;
                }
                appCfgs.appendChild(option);
            }
            if (appCfgsAdd) {
                appCfgsAdd.setAttribute('href', apphookData.apphooks_configuration_url[opt.value] +
                    (window.showRelatedObjectPopup ? '?_popup=1' : ''));
                appCfgsAdd.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    window.showAddAnotherPopup(this);
                });
            }
            if (appCfgsRow) {
                appCfgsRow.classList.remove('hidden');
            }
            if (appNsRow) {
                appNsRow.classList.add('hidden');
            }
        } else {
            if (appCfgsRow) {
                appCfgsRow.classList.add('hidden');
            }
            if (opt && opt.dataset.namespace && appNsRow) {
                appNsRow.classList.remove('hidden');
            } else if (appNsRow) {
                appNsRow.classList.add('hidden');
            }
        }
    }

    // Hide the namespace widgets if its not required.
    setupNamespaces();

    // Show it if we change to an app_hook that requires a namespace
    if (appHooks) {
        appHooks.addEventListener('change', function () {
            const opt = getSelectedOption(appHooks);

            setupNamespaces();
            // If we clear the app_hook, clear out the app_namespace too
            if (appNs && !appHooks.value) {
                appNs.value = '';
                appNs.removeAttribute('value');
            }
            // When selecting back the original apphook we try to restore the original configuration
            if (opt && original_ns && opt.value === original_ns) {
                appNs.value = original_ns;
            } else if (opt && opt.dataset.namespace) {
                // If new apphook has a namespace, suggest the default
                appNs.value = opt.dataset.namespace;
            } else if (appNs) {
                // Cleanup the whole thing
                appNs.value = '';
                appNs.removeAttribute('value');
            }
        });
    }
});

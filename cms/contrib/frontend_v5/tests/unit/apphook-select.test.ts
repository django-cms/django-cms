import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    initApphookSelect,
    type ApphookWidgetData,
} from '../../src/modules/apphook-select';

/**
 * Build the DOM that Django's page advanced-settings form produces.
 *
 * Three form rows:
 *   - application_urls select (visible)
 *   - application_configs row (hidden/shown by the widget)
 *   - application_namespace row (hidden/shown by the widget)
 */
interface DomOptions {
    apphooks?: Array<{
        value: string;
        label: string;
        /** Sets data-namespace attribute on the option. */
        namespace?: string;
        selected?: boolean;
    }>;
    /** Initial value in the namespace input, if any. */
    initialNamespace?: string;
    /** Omit the "add config" anchor. */
    withoutAddButton?: boolean;
}

function setupDom(opts: DomOptions = {}): void {
    const apphooks = opts.apphooks ?? [
        { value: '', label: '---' },
        { value: 'NewsApp', label: 'News', namespace: 'news' },
        { value: 'BlogApp', label: 'Blog' },
        { value: 'ShopApp', label: 'Shop', namespace: 'shop' },
    ];

    const appHookOptions = apphooks
        .map(
            (a) =>
                `<option value="${a.value}"${a.namespace ? ` data-namespace="${a.namespace}"` : ''}${a.selected ? ' selected' : ''}>${a.label}</option>`,
        )
        .join('');

    document.body.innerHTML = `
        <form>
            <div class="form-row field-application_urls">
                <select id="application_urls">${appHookOptions}</select>
            </div>
            <div class="form-row field-application_configs hidden">
                <select id="application_configs"></select>
                ${opts.withoutAddButton ? '' : '<a id="add_application_configs" href="/admin/news/config/add/">Add</a>'}
            </div>
            <div class="form-row field-application_namespace hidden">
                <input id="application_namespace" type="text" value="${opts.initialNamespace ?? ''}" />
            </div>
        </form>
    `;
}

const $ = <E extends Element = HTMLElement>(sel: string): E => document.querySelector<E>(sel)!;

const appHookSelect = () => $<HTMLSelectElement>('#application_urls');
const configsRow = () => $<HTMLElement>('.form-row.field-application_configs');
const configsSelect = () => $<HTMLSelectElement>('#application_configs');
const namespaceRow = () => $<HTMLElement>('.form-row.field-application_namespace');
const namespaceInput = () => $<HTMLInputElement>('#application_namespace');

const change = (el: HTMLSelectElement, value: string): void => {
    el.value = value;
    el.dispatchEvent(new Event('change'));
};

const baseData: ApphookWidgetData = {
    apphooks_configuration: {
        NewsApp: [
            ['news-main', 'News — Main'],
            ['news-press', 'News — Press'],
        ],
        ShopApp: [['shop-default', 'Shop — Default']],
    },
    apphooks_configuration_url: {
        NewsApp: '/admin/news/config/add/',
        ShopApp: '/admin/shop/config/add/',
    },
};

describe('initApphookSelect', () => {
    afterEach(() => {
        document.body.innerHTML = '';
        delete window.showRelatedObjectPopup;
        delete window.showAddAnotherPopup;
    });

    describe('no-op cases', () => {
        it('does not throw when the apphook select is missing', () => {
            document.body.innerHTML = '<form></form>';
            expect(() => initApphookSelect(baseData)).not.toThrow();
        });

        it('works with default empty data', () => {
            setupDom();
            expect(() => initApphookSelect()).not.toThrow();
        });
    });

    describe('initial setup', () => {
        it('hides both namespace and config rows for an apphook with neither', () => {
            setupDom({
                apphooks: [{ value: 'BlogApp', label: 'Blog', selected: true }],
            });
            initApphookSelect(baseData);
            expect(configsRow().classList.contains('hidden')).toBe(true);
            expect(namespaceRow().classList.contains('hidden')).toBe(true);
        });

        it('shows the namespace row when apphook has data-namespace but no config', () => {
            setupDom({
                apphooks: [
                    { value: 'BlogApp', label: 'Blog', namespace: 'blog', selected: true },
                ],
            });
            initApphookSelect(baseData);
            expect(configsRow().classList.contains('hidden')).toBe(true);
            expect(namespaceRow().classList.contains('hidden')).toBe(false);
        });

        it('shows the config row when apphook has configs, hides namespace', () => {
            setupDom({
                apphooks: [
                    { value: 'NewsApp', label: 'News', namespace: 'news', selected: true },
                ],
            });
            initApphookSelect(baseData);
            expect(configsRow().classList.contains('hidden')).toBe(false);
            expect(namespaceRow().classList.contains('hidden')).toBe(true);
        });

        it('populates the config select with options for the selected apphook', () => {
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect(baseData);
            const options = Array.from(configsSelect().options);
            expect(options).toHaveLength(2);
            expect(options.map((o) => o.value)).toEqual(['news-main', 'news-press']);
            expect(options.map((o) => o.textContent)).toEqual(['News — Main', 'News — Press']);
        });

        it('pre-selects the config matching apphooks_configuration_value', () => {
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect({
                ...baseData,
                apphooks_configuration_value: 'news-press',
            });
            const selected = Array.from(configsSelect().options).find((o) => o.selected);
            expect(selected?.value).toBe('news-press');
        });

        it('sets the add button href to the config URL', () => {
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect(baseData);
            const addBtn = $<HTMLAnchorElement>('#add_application_configs');
            expect(addBtn.getAttribute('href')).toBe('/admin/news/config/add/');
        });

        it('appends ?_popup=1 to the add button href when showRelatedObjectPopup exists', () => {
            window.showRelatedObjectPopup = vi.fn();
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect(baseData);
            const addBtn = $<HTMLAnchorElement>('#add_application_configs');
            expect(addBtn.getAttribute('href')).toBe('/admin/news/config/add/?_popup=1');
        });
    });

    describe('add button click', () => {
        it('preventDefault and calls showAddAnotherPopup with the button element', () => {
            const showAddAnother = vi.fn();
            window.showAddAnotherPopup = showAddAnother;
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect(baseData);

            const addBtn = $<HTMLAnchorElement>('#add_application_configs');
            const clickEvent = new MouseEvent('click', { cancelable: true, bubbles: true });
            addBtn.dispatchEvent(clickEvent);

            expect(clickEvent.defaultPrevented).toBe(true);
            expect(showAddAnother).toHaveBeenCalledWith(addBtn);
        });

        it('is safe to click when showAddAnotherPopup is absent (prevents default, no crash)', () => {
            setupDom({
                apphooks: [{ value: 'NewsApp', label: 'News', selected: true }],
            });
            initApphookSelect(baseData);
            const addBtn = $<HTMLAnchorElement>('#add_application_configs');
            const ev = new MouseEvent('click', { cancelable: true, bubbles: true });
            expect(() => addBtn.dispatchEvent(ev)).not.toThrow();
            expect(ev.defaultPrevented).toBe(true);
        });
    });

    describe('apphook change event', () => {
        beforeEach(() => {
            setupDom({
                apphooks: [
                    { value: '', label: '---' },
                    { value: 'NewsApp', label: 'News', namespace: 'news' },
                    { value: 'BlogApp', label: 'Blog' },
                    { value: 'ShopApp', label: 'Shop', namespace: 'shop' },
                ],
                initialNamespace: '',
            });
        });

        it('clears the namespace when user clears the apphook', () => {
            namespaceInput().value = 'something';
            initApphookSelect(baseData);
            change(appHookSelect(), '');
            expect(namespaceInput().value).toBe('');
        });

        it('sets namespace to the default when switching to an apphook with data-namespace', () => {
            initApphookSelect(baseData);
            change(appHookSelect(), 'NewsApp');
            expect(namespaceInput().value).toBe('news');
        });

        it('clears namespace when switching to an apphook with neither config nor data-namespace', () => {
            initApphookSelect(baseData);
            change(appHookSelect(), 'BlogApp');
            expect(namespaceInput().value).toBe('');
        });

        it('shows the config row and rebuilds options when switching to an apphook with configs', () => {
            initApphookSelect(baseData);
            change(appHookSelect(), 'NewsApp');
            expect(configsRow().classList.contains('hidden')).toBe(false);
            expect(namespaceRow().classList.contains('hidden')).toBe(true);
            expect(Array.from(configsSelect().options).map((o) => o.value)).toEqual([
                'news-main',
                'news-press',
            ]);
        });

        it('hides the config row when switching to an apphook with no config', () => {
            setupDom({
                apphooks: [
                    { value: 'NewsApp', label: 'News', selected: true },
                    { value: 'BlogApp', label: 'Blog' },
                ],
            });
            initApphookSelect(baseData);
            change(appHookSelect(), 'BlogApp');
            expect(configsRow().classList.contains('hidden')).toBe(true);
        });
    });

    describe('original-apphook restore (bug fix vs. legacy)', () => {
        it('restores the original namespace when reverting to the original apphook', () => {
            // Page loads with NewsApp selected, namespace already "my-news".
            setupDom({
                apphooks: [
                    { value: 'NewsApp', label: 'News', namespace: 'news', selected: true },
                    { value: 'BlogApp', label: 'Blog' },
                    { value: 'ShopApp', label: 'Shop', namespace: 'shop' },
                ],
                initialNamespace: 'my-news',
            });
            initApphookSelect(baseData);
            // User switches away to ShopApp — namespace updates to "shop".
            change(appHookSelect(), 'ShopApp');
            expect(namespaceInput().value).toBe('shop');
            // User switches BACK to NewsApp — namespace should restore to "my-news",
            // not the default "news". This is the behavior the legacy code intended
            // but couldn't deliver (it compared apphook against namespace, nonsense).
            change(appHookSelect(), 'NewsApp');
            expect(namespaceInput().value).toBe('my-news');
        });

        it('uses the default namespace when no original was set', () => {
            setupDom({
                apphooks: [
                    { value: '', label: '---', selected: true },
                    { value: 'NewsApp', label: 'News', namespace: 'news' },
                ],
                initialNamespace: '',
            });
            initApphookSelect(baseData);
            change(appHookSelect(), 'NewsApp');
            expect(namespaceInput().value).toBe('news');
        });
    });

    describe('destroy()', () => {
        it('removes the change listener so subsequent changes are no-ops', () => {
            setupDom({
                apphooks: [
                    { value: 'NewsApp', label: 'News', namespace: 'news', selected: true },
                    { value: 'BlogApp', label: 'Blog' },
                ],
            });
            const handle = initApphookSelect(baseData);
            handle.destroy();
            change(appHookSelect(), 'BlogApp');
            // No change handler ran → config row is still in its initial (shown) state.
            expect(configsRow().classList.contains('hidden')).toBe(false);
        });
    });
});

/*
 * Two-select sync widget for the Django CMS page picker.
 *
 * Port of the legacy `forms.pageselectwidget.js`. Semantics preserved
 * exactly — this widget is a compatibility layer between three native
 * `<select>` elements rendered by the Django form:
 *
 *   group0 = site selector (visible, top-level)
 *   group1 = page selector filtered by the site chosen in group0 (visible)
 *   group2 = backing hidden select carrying EVERY page across all sites,
 *            grouped into <optgroup label="{site name}">. This is the
 *            single source of truth for form submission.
 *
 * Changing group0:
 *   → Remove every <optgroup> currently in group1.
 *   → Find the matching <optgroup label="{site}"> in group2 and
 *     clone it into group1.
 *   → Fire a `change` event on group1 so downstream listeners re-run.
 *
 * Changing group1:
 *   → Write the selected page's value back into group2 (the backing
 *     field that Django actually reads on submit). If nothing is
 *     selected in group1, fall back to the empty option in group2.
 *
 * The legacy code had a `__webpack_public_path__` trick for lazy chunks
 * that this widget never actually produces. It was dead code; dropped.
 */

export interface PageSelectWidgetOptions {
    /** Form field prefix — the three selects have ids `id_{name}_0`, `..._1`, `..._2`. */
    name: string;
}

export class PageSelectWidget {
    readonly options: PageSelectWidgetOptions;

    constructor(options: PageSelectWidgetOptions) {
        this.options = { ...options };
        this.setup();
    }

    private setup(): void {
        const { name } = this.options;
        const group0 = document.getElementById(`id_${name}_0`) as HTMLSelectElement | null;
        const group1 = document.getElementById(`id_${name}_1`) as HTMLSelectElement | null;
        const group2 = document.getElementById(`id_${name}_2`) as HTMLSelectElement | null;
        const addBtn = document.getElementById(`add_id_${name}`);

        // The legacy widget hides the "add new" button unconditionally. We
        // preserve this so the page-picker doesn't sprout a stray button
        // when dropped into the contrib app. `.cms-hidden` is defined in
        // `cms.base.css` which is loaded on every CMS admin page.
        addBtn?.classList.add('cms-hidden');

        // If any of the three selects is missing the widget is incomplete
        // (e.g. rendered under a non-standard template) — bail out silently.
        if (!group0 || !group1 || !group2) return;

        const onGroup0Change = (): void => {
            const selected = group0.options[group0.selectedIndex];
            const siteLabel = selected ? selected.textContent ?? '' : '';

            // Remove every existing optgroup from group1. We're rebuilding
            // its contents from group2 based on the new site.
            for (const og of Array.from(group1.querySelectorAll('optgroup'))) {
                og.remove();
            }

            const match = Array.from(group2.querySelectorAll('optgroup')).find(
                (og) => og.label === siteLabel,
            );
            if (match) {
                group1.appendChild(match.cloneNode(true));
            }

            // Fire a change event on group1 so onGroup1Change runs and
            // syncs the backing group2. setTimeout(0) matches the legacy
            // code's ordering — any microtasks queued by cloning options
            // resolve before the change handler sees the new DOM.
            setTimeout(() => {
                group1.dispatchEvent(new Event('change'));
            }, 0);
        };

        const onGroup1Change = (): void => {
            const selected = group1.options[group1.selectedIndex];
            const value = selected ? selected.value : '';

            if (value) {
                // Clear any previous selection in group2, then select the
                // matching value. Array conversion because HTMLOptionsCollection
                // isn't iterable with for-of in all targets.
                for (const opt of Array.from(group2.options)) {
                    opt.selected = false;
                }
                const match = Array.from(group2.options).find((opt) => opt.value === value);
                if (match) {
                    match.selected = true;
                }
            } else if (group2.options.length > 0) {
                // No selection in group1 → select the "empty" option in
                // group2 (the blank choice Django renders for optional
                // fields) so the backing field is explicitly cleared.
                const emptyOpt = Array.from(group2.options).find((opt) => opt.value === '');
                if (emptyOpt) {
                    emptyOpt.selected = true;
                }
            }
        };

        group0.addEventListener('change', onGroup0Change);
        group1.addEventListener('change', onGroup1Change);

        // Run group0 once to populate group1 from the initial server-rendered
        // site selection. Needed for forms that come back after a validation
        // error with the site already chosen.
        group0.dispatchEvent(new Event('change'));
    }
}

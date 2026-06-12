import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { PageSelectWidget } from '../../frontend/modules/page-select-widget';

/**
 * Fixture DOM for the three-select page picker. Mirrors what Django's
 * page-picker form widget actually renders:
 *
 *   id_page_0 → site picker (visible)
 *   id_page_1 → filtered page picker (visible, rebuilt from group2)
 *   id_page_2 → backing select with all pages grouped by site (hidden)
 */
function setupDom(initialSite = '', initialPage = ''): void {
    document.body.innerHTML = `
        <form>
            <select id="id_page_0">
                <option value=""></option>
                <option value="1" ${initialSite === '1' ? 'selected' : ''}>Example Site</option>
                <option value="2" ${initialSite === '2' ? 'selected' : ''}>Another Site</option>
            </select>
            <select id="id_page_1"></select>
            <select id="id_page_2">
                <option value=""></option>
                <optgroup label="Example Site">
                    <option value="p1" ${initialPage === 'p1' ? 'selected' : ''}>Home</option>
                    <option value="p2" ${initialPage === 'p2' ? 'selected' : ''}>About</option>
                </optgroup>
                <optgroup label="Another Site">
                    <option value="p3">Landing</option>
                </optgroup>
            </select>
            <a id="add_id_page" href="#">Add</a>
        </form>
    `;
}

const $ = <E extends Element = HTMLElement>(sel: string): E =>
    document.querySelector<E>(sel)!;

const group0 = () => $<HTMLSelectElement>('#id_page_0');
const group1 = () => $<HTMLSelectElement>('#id_page_1');
const group2 = () => $<HTMLSelectElement>('#id_page_2');

function changeSelect(select: HTMLSelectElement, value: string): void {
    select.value = value;
    select.dispatchEvent(new Event('change'));
}

/**
 * The widget uses setTimeout(0) to re-fire change on group1 after a
 * group0 change. Flush all pending timers with a microtask-friendly
 * approach: await a Promise that resolves after a setTimeout(0).
 */
const flushMacrotask = () =>
    new Promise<void>((resolve) => setTimeout(resolve, 0));

describe('PageSelectWidget', () => {
    beforeEach(() => {
        setupDom();
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    describe('construction', () => {
        it('hides the add button', () => {
            new PageSelectWidget({ name: 'page' });
            const addBtn = document.getElementById('add_id_page') as HTMLElement;
            expect(addBtn.classList.contains('cms-hidden')).toBe(true);
        });

        it('is a no-op when any of the three selects is missing', () => {
            document.body.innerHTML = '<select id="id_page_0"></select>';
            expect(() => new PageSelectWidget({ name: 'page' })).not.toThrow();
        });

        it('populates group1 from the initial site selection', async () => {
            setupDom('1');
            new PageSelectWidget({ name: 'page' });

            // Runs synchronously in the constructor via initial
            // change dispatch — group1 should contain Example Site options.
            const optgroups = group1().querySelectorAll('optgroup');
            expect(optgroups).toHaveLength(1);
            expect(optgroups[0]!.label).toBe('Example Site');
            expect(group1().options).toHaveLength(2);
            expect(group1().options[0]!.value).toBe('p1');
            expect(group1().options[1]!.value).toBe('p2');

            await flushMacrotask();
        });
    });

    describe('group0 → group1 filtering', () => {
        beforeEach(() => {
            new PageSelectWidget({ name: 'page' });
        });

        it('replaces group1 contents with the matching optgroup from group2', async () => {
            changeSelect(group0(), '1');
            expect(group1().querySelector('optgroup')?.label).toBe('Example Site');

            changeSelect(group0(), '2');
            expect(group1().querySelector('optgroup')?.label).toBe('Another Site');
            expect(group1().options).toHaveLength(1);
            expect(group1().options[0]!.value).toBe('p3');

            await flushMacrotask();
        });

        it('clears group1 when group0 selection does not match any optgroup', async () => {
            changeSelect(group0(), '1');
            expect(group1().querySelectorAll('optgroup')).toHaveLength(1);

            changeSelect(group0(), '');
            expect(group1().querySelectorAll('optgroup')).toHaveLength(0);
            expect(group1().options).toHaveLength(0);

            await flushMacrotask();
        });

        it('removes previous optgroups before adding new ones (no stacking)', async () => {
            changeSelect(group0(), '1');
            changeSelect(group0(), '2');
            // After two changes, only the most recent optgroup is present.
            expect(group1().querySelectorAll('optgroup')).toHaveLength(1);
            expect(group1().querySelector('optgroup')?.label).toBe('Another Site');
            await flushMacrotask();
        });
    });

    describe('group1 → group2 sync', () => {
        beforeEach(() => {
            new PageSelectWidget({ name: 'page' });
            changeSelect(group0(), '1');
        });

        it('writes the selected page back to group2', () => {
            changeSelect(group1(), 'p2');
            // Find the actually-selected option in group2.
            const selected = Array.from(group2().options).filter((o) => o.selected);
            expect(selected).toHaveLength(1);
            expect(selected[0]!.value).toBe('p2');
        });

        it('falls back to the empty option in group2 when group1 clears', () => {
            changeSelect(group1(), 'p1');
            changeSelect(group1(), '');
            // After clearing, the empty option is selected in group2.
            const selected = Array.from(group2().options).filter((o) => o.selected);
            expect(selected).toHaveLength(1);
            expect(selected[0]!.value).toBe('');
        });

        it('does not leave multiple options selected after switching', () => {
            changeSelect(group1(), 'p1');
            changeSelect(group1(), 'p2');
            const selected = Array.from(group2().options).filter((o) => o.selected);
            expect(selected).toHaveLength(1);
            expect(selected[0]!.value).toBe('p2');
        });
    });

    describe('group0 change triggers group1 change', () => {
        it('flushes the setTimeout so group2 ends up in sync with the new site', async () => {
            new PageSelectWidget({ name: 'page' });

            // Pre-populate: select a page in group2 that doesn't belong
            // to the current site (p3 belongs to "Another Site").
            const p3 = group2().querySelector<HTMLOptionElement>('option[value="p3"]')!;
            p3.selected = true;

            changeSelect(group0(), '1');
            await flushMacrotask();

            // After the async change fires, group1 has been rebuilt with
            // the Example Site options (p1, p2). Since no option is
            // explicitly selected in the cloned optgroup, the browser
            // picks the first one (p1) as the default selection, which
            // then syncs back to group2. Crucially, p3 is NO LONGER
            // selected — the cross-site stale selection has been cleared.
            const selected = Array.from(group2().options).filter((o) => o.selected);
            expect(selected).toHaveLength(1);
            expect(selected[0]!.value).toBe('p1');

            // And the previously-stale p3 selection is gone.
            expect(p3.selected).toBe(false);
        });
    });
});

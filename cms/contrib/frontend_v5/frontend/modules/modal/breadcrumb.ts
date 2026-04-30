/*
 * Modal breadcrumb rendering — the navigation strip at the top of an
 * iframe modal showing parent → child crumbs. Mirrors `_setBreadcrumb`
 * from the legacy modal.
 *
 * Returns true when breadcrumbs were rendered, false when the input
 * was empty / single-level (the modal class uses this to toggle the
 * `cms-modal-has-breadcrumb` class).
 */

export interface Breadcrumb {
    title: string;
    url: string;
}

export function renderBreadcrumbs(
    container: HTMLElement,
    crumbs: Breadcrumb[] | undefined | null,
): boolean {
    container.innerHTML = '';
    if (!crumbs || crumbs.length <= 1) return false;
    if (!crumbs[0]?.title) return false;

    const frag = document.createDocumentFragment();
    crumbs.forEach((item, index) => {
        const a = document.createElement('a');
        a.href = item.url;
        if (index >= crumbs.length - 1) a.classList.add('active');
        const span = document.createElement('span');
        span.textContent = item.title;
        a.appendChild(span);
        frag.appendChild(a);
    });
    container.appendChild(frag);
    return true;
}

/*
 * CMS top-of-viewport loading bar.
 *
 * Port of the legacy `cms/static/cms/js/modules/loader.js`. The legacy
 * file was already vanilla JS (no jQuery) — this is a 1:1 TS port with
 * minor ergonomics: `const` ids, typed handles, explicit return types.
 *
 * Depends on the `#cms-top` element being present in the DOM. On pages
 * that don't have it (e.g. login, non-admin contexts), calling
 * `showLoader` is a no-op rather than a crash — caller code is often
 * invoked before we know whether the target exists.
 *
 * The bar uses CSS classes from `components/_toolbar.scss` (legacy
 * location). Once the toolbar SCSS is forked into the contrib app,
 * the `.cms-loading-bar` + `.cms-loading-peg` rules need to come
 * along with it.
 */

const LOADER_ID = 'cms-loading-bar';
/** Time (ms) to wait before removing the loader from the DOM after fading out. */
const REMOVE_DELAY_MS = 300;

let debounceTimeout: ReturnType<typeof setTimeout> | null = null;

function createLoaderBar(): void {
    if (document.getElementById(LOADER_ID)) return;

    const cmsTop = document.getElementById('cms-top');
    if (!cmsTop) return;

    const bar = document.createElement('div');
    bar.id = LOADER_ID;
    bar.className = 'cms-loading-bar';
    bar.setAttribute('role', 'bar');
    bar.innerHTML = '<div class="cms-loading-peg"></div>';
    cmsTop.appendChild(bar);
}

function removeLoaderBar(): void {
    const bar = document.getElementById(LOADER_ID);
    if (!bar) return;

    bar.style.opacity = '0';
    setTimeout(() => {
        bar.parentNode?.removeChild(bar);
    }, REMOVE_DELAY_MS);
}

/**
 * Show the loading bar at the top of the viewport. Debounced at the
 * next tick so rapid show/hide sequences don't flicker — if hideLoader
 * fires before the tick, the bar never gets created at all.
 */
export const showLoader = (): void => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(createLoaderBar, 0);
};

/** Hide the loading bar. Fades out over REMOVE_DELAY_MS then removes from DOM. */
export const hideLoader = (): void => {
    if (debounceTimeout) {
        clearTimeout(debounceTimeout);
        debounceTimeout = null;
    }
    removeLoaderBar();
};

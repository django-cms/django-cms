
// Loader mit Vanilla JS, nutzt die vorhandenen Styles aus _toolbar.scss
let debounceTimeout = null;
const LOADER_ID = 'cms-loading-bar';

function createLoaderBar() {
    if (document.getElementById(LOADER_ID)) return;
    const cmsTop = document.getElementById('cms-top');
    const bar = document.createElement('div');
    bar.id = LOADER_ID;
    bar.className = 'cms-loading-bar';
    bar.setAttribute('role', 'bar');
    bar.innerHTML = '<div class="cms-loading-peg"></div>';
    cmsTop.appendChild(bar);
}

function removeLoaderBar() {
    const bar = document.getElementById(LOADER_ID);
    if (bar) {
        bar.style.opacity = '0';
        setTimeout(() => {
            if (bar.parentNode) bar.parentNode.removeChild(bar);
        }, 300);
    }
}

/**
 * Zeigt den Loader-Balken oben im Viewport an (debounced).
 */
export const showLoader = () => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
        createLoaderBar();
    }, 0);
};

/**
 * Versteckt den Loader-Balken.
 */
export const hideLoader = () => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    removeLoaderBar();
};

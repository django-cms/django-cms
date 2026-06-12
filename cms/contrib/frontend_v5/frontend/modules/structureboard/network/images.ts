/*
 * Best-effort image preloader. Walks an HTML string for `<img src>`
 * URLs and pings each via a transient `Image()` so the browser
 * caches the bytes ahead of the actual render.
 *
 * Ported from `cms/static/cms/js/modules/preload-images.js`. Failures
 * are swallowed — preloading is a perf hint, never load-bearing.
 */

const IMG_SRC_RE = /<\s*img[\s\S]*?src=['"](.*?)['"][\s\S]*?>/gi;

function preload(src: string): void {
    try {
        const img = new Image();
        img.src = src;
    } catch {
        /* preload failures are non-fatal */
    }
}

/**
 * Extract every `<img src="...">` URL from a markup string and
 * preload it. The regex is intentionally loose — we don't need
 * accurate parsing, just enough to seed the HTTP cache.
 */
export function preloadImagesFromMarkup(html: string): void {
    if (!html) return;
    let match: RegExpExecArray | null;
    // Reset lastIndex so repeat calls don't interfere.
    IMG_SRC_RE.lastIndex = 0;
    while ((match = IMG_SRC_RE.exec(html)) !== null) {
        const src = match[1];
        if (src) preload(src);
    }
}

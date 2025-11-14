
export default function addSlugHandlers(title, slug) {
    if (!slug) {
        return;
    }

    let prefill = false;

    // determine if slug is empty
    if (slug.value.trim() === '') {
        prefill = true;
    }
    if (window.unihandecode) {
        // eslint-disable-next-line new-cap
        window.UNIHANDECODER = window.unihandecode.Unihan(slug.dataset.decoder);
    }

    // always bind the title > slug generation and do the validation inside for better ux
    function updateSlug() {
        let value = title.value;
        // international language handling

        if (window.UNIHANDECODER) {
            value = window.UNIHANDECODER.decode(value);
        }
        // if slug is empty, prefill again
        if (prefill === false && slug.value === '') {
            prefill = true;
        }
        // urlify
        // eslint-disable-next-line
        const urlified = URLify(value, 64);
        if (prefill) {
            slug.value = urlified;
        }
    }
    title.addEventListener('keyup', updateSlug);
    title.addEventListener('keypress', updateSlug);
    // autocall
    updateSlug();

    function markChanged(e) {
        e.target.dataset.changed = 'true';
    }
    slug.addEventListener('change', markChanged);
    title.addEventListener('change', markChanged);
}

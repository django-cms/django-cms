/**
 * Returns true if the slug field is already handled by django admin's own
 * prepopulate.js, so that both mechanisms do not fight over the same input.
 */
function isPrepopulatedByAdmin(slug) {
    const constants = document.getElementById('django-admin-prepopulated-fields-constants');

    if (!constants) {
        return false;
    }
    let fields;

    try {
        fields = JSON.parse(constants.dataset.prepopulatedFields || '[]');
    } catch {
        return false;
    }
    return fields.some(field => field.id && document.querySelector(field.id) === slug);
}

export default function addSlugHandlers(title, slug) {
    if (!title || !slug || slug.dataset.slugHandlers === 'true' || isPrepopulatedByAdmin(slug)) {
        // Nothing to bind, or the field is already taken care of - either by another
        // bundle on the same page or by django admin's prepopulated fields.
        return;
    }
    slug.dataset.slugHandlers = 'true';

    if (window.unihandecode) {
        // eslint-disable-next-line new-cap
        window.UNIHANDECODER = window.unihandecode.Unihan(slug.dataset.decoder);
    }

    // The slug is only generated from the title as long as the user has not typed
    // into it themselves. A slug that already has a value (change form, redisplay
    // after a validation error) counts as user-provided.
    let prefill = slug.value.trim() === '';

    function updateSlug() {
        if (!prefill) {
            return;
        }
        let value = title.value;

        // international language handling
        if (window.UNIHANDECODER) {
            value = window.UNIHANDECODER.decode(value);
        }
        // urlify
        // eslint-disable-next-line
        slug.value = URLify(value, 64);
    }

    function slugTouched() {
        // Emptying the slug hands control back to the auto-generation
        prefill = slug.value.trim() === '';
    }

    function markChanged(e) {
        e.target.dataset.changed = 'true';
    }

    // Programmatic changes from updateSlug() do not fire "input", so the
    // auto-generated value never marks the slug as user-provided.
    title.addEventListener('input', updateSlug);
    slug.addEventListener('input', slugTouched);

    // add changed data bindings to elements
    slug.addEventListener('change', markChanged);
    title.addEventListener('change', markChanged);

    // autocall
    updateSlug();
}

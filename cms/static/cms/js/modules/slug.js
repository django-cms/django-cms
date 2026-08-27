import $ from 'jquery';

/**
 * Returns true if the slug field is already handled by django admin's own
 * prepopulate.js, so that both mechanisms do not fight over the same input.
 *
 * @function isPrepopulatedByAdmin
 * @param {HTMLElement} slug slug input element
 * @returns {Boolean} true if django admin takes care of the field
 */
function isPrepopulatedByAdmin(slug) {
    var constants = document.getElementById('django-admin-prepopulated-fields-constants');

    if (!constants) {
        return false;
    }
    var fields;

    try {
        fields = JSON.parse(constants.dataset.prepopulatedFields || '[]');
    } catch (e) {
        return false;
    }
    return fields.some(function(field) {
        return field.id && document.querySelector(field.id) === slug;
    });
}

/**
 * Binds the automatic slug generation to a title/slug field pair.
 *
 * @function addSlugHandlers
 * @param {jQuery} title title input element
 * @param {jQuery} slug slug input element
 * @returns {void}
 */
export default function addSlugHandlers(title, slug) {
    if (!title || !title.length || !slug || !slug.length) {
        return;
    }

    var titleField = title[0];
    var slugField = slug[0];

    if (slugField.dataset.slugHandlers === 'true' || isPrepopulatedByAdmin(slugField)) {
        // The field is already taken care of - either by another bundle on the
        // same page or by django admin's prepopulated fields.
        return;
    }
    slugField.dataset.slugHandlers = 'true';

    if (window.unihandecode) {
        // eslint-disable-next-line new-cap
        window.UNIHANDECODER = window.unihandecode.Unihan(slug.data('decoder'));
    }

    // The slug is only generated from the title as long as the user has not typed
    // into it themselves. A slug that already has a value (change form, redisplay
    // after a validation error) counts as user-provided.
    var prefill = slugField.value.trim() === '';

    /**
     * Generates the slug from the title, as long as the user has not taken over.
     *
     * @function updateSlug
     * @returns {void}
     */
    function updateSlug() {
        if (!prefill) {
            return;
        }
        var value = titleField.value;

        // international language handling
        if (window.UNIHANDECODER) {
            value = window.UNIHANDECODER.decode(value);
        }
        // urlify
        // eslint-disable-next-line
        slugField.value = URLify(value, 64);
    }

    /**
     * Emptying the slug hands control back to the auto-generation.
     *
     * @function slugTouched
     * @returns {void}
     */
    function slugTouched() {
        prefill = slugField.value.trim() === '';
    }

    /**
     * Marks a field as changed, used to warn before switching language tabs.
     *
     * @function markChanged
     * @returns {void}
     */
    function markChanged() {
        $(this).data('changed', true);
    }

    // Programmatic changes from updateSlug() do not fire "input", so the
    // auto-generated value never marks the slug as user-provided.
    title.on('input', updateSlug);
    slug.on('input', slugTouched);

    // add changed data bindings to elements
    slug.add(title).on('change', markChanged);

    // autocall
    updateSlug();
}

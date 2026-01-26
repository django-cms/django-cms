
/* global gettext, fetch */

import addSlugHandlers from './slug';

document.addEventListener('DOMContentLoaded', () => {
    // set local variables
    const title = document.getElementById('id_title');
    const slug = document.getElementById('id_slug');

    addSlugHandlers(title, slug);

    // all permissions and page states loader
    document.querySelectorAll('div.loading').forEach(div => {
        const rel = div.getAttribute('rel');

        if (rel) {
            fetch(rel)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    div.textContent = '';
                    while (doc.body.firstChild) {
                        div.appendChild(doc.body.firstChild);
                    }
                });
        }
    });

    // hide rows when hidden input fields are added
    document.querySelectorAll('input[type="hidden"]').forEach(input => {
        const parent = input.closest('.form-row');

        if (parent) {
            parent.style.display = 'none';
        }
    });

    document.querySelectorAll('#page_form_lang_tabs .language_button').forEach(btn => {
        btn.addEventListener('click', function() {
            CMS.API.changeLanguage(this.dataset.adminUrl);
        });
    });

    // public api for changing the language tabs
    // used in admin/cms/page/change_form.html
    window.CMS.API.changeLanguage = function(url) {
        // also make sure that we will display the confirm dialog
        // in case users switch tabs while editing plugins
        let answer = true;
        let changed = false;

        if (slug) {
            // check if the slug has the changed attribute
            if (slug.dataset.changed === 'true' || (title && title.dataset.changed === 'true')) {
                changed = true;
            }
        }

        if (changed) {
            const question = typeof gettext === 'function'
                ? gettext('Are you sure you want to change tabs without saving the page first?')
                : 'Are you sure you want to change tabs without saving the page first?';


            // eslint-disable-next-line no-alert
            answer = confirm(question);
        }
        if (answer) {
            window.location.href = url;
        }
    };
});

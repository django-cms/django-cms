// CSP-safe replacement for the previously inline script in templates/cms/welcome.html
// Reads its configuration from the #cms-welcome-config element's data-* attributes
// so that no inline JavaScript (and no template interpolation into JS) is required.

(function () {
    /**
     * Reads configuration from #cms-welcome-config and either redirects anonymous
     * users to the login page or wires up the wizard modal for authenticated users.
     *
     * @function init
     * @returns {void}
     */
    function init() {
        var config = document.getElementById('cms-welcome-config');

        if (!config) {
            return;
        }

        // Anonymous users get redirected to the login page.
        var loginUrl = config.dataset.loginUrl;

        if (loginUrl) {
            window.location.href = loginUrl;
            return;
        }

        // Authenticated users get the wizard modal wired up to the "add" button.
        var CMS = window.CMS;

        if (!CMS) {
            return;
        }

        var buttons = document.querySelectorAll('.js-welcome-add');
        var i;

        for (i = 0; i < buttons.length; i++) {
            buttons[i].addEventListener('click', function (e) {
                e.preventDefault();
                var modal = new CMS.Modal();

                modal.open({
                    url: config.dataset.addUrl,
                    title: config.dataset.addTitle
                });
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

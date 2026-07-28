// Loaded by templates/admin/cms/usersettings/change_form.html, which renders
// inside the CMS sideframe iframe. After the user changes their settings (e.g.
// the admin language), the server redirects this iframe to its new URL with a
// "?reload_window" marker. This script detects that marker and tells the parent
// window's CMS instance to store the corrected sideframe URL and reload the whole
// page, so the new settings take effect in the toolbar and surrounding UI.
window.addEventListener('load', function () {
    // we have to setTimeout here because the cms.sideframe load event
    // fires after this one :(
    setTimeout(function () {
        var CMS = window.parent.CMS;
        // we need to reload the parent window once "?reload_window" is defined and
        // set the new url for the sideframe with the correct language specification
        if (location.href.indexOf('reload_window') > -1 && CMS) {
            // save url in settings
            CMS.settings.sideframe.url = window.location.href.replace(/[?&]reload_window/, '');
            CMS.settings = CMS.API.Helpers.setSettings(CMS.settings);
            // reload everything
            CMS.API.Helpers.reloadBrowser();
        }
    }, 0);
});

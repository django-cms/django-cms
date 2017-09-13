import $ from 'jquery';
import Plugin from 'cms.plugins';
import Modal from 'cms.modal';

const originalDelegate = Plugin.prototype._delegate;

export function overridePlugin() {
    Plugin.prototype._delegate = function(e) {
        e.preventDefault();
        e.stopPropagation();

        var items = '.cms-submenu-edit, .cms-submenu-item a';
        var el = $(e.target).closest(items);

        if (el.data('url') && el.data('rel') === 'add') {
            var nav;

            if (e.data && e.data.nav) {
                nav = e.data.nav;
            }

            // show loader and make sure scroll doesn't jump
            CMS.API.Toolbar.showLoader();

            Plugin._hideSettingsMenu(nav);

            const { url } = el.data();

            this.addModule(url, el.text(), el.closest('.cms-plugin-picker').data('parentId'));
        } else {
            return originalDelegate.call(this, e);
        }
    };

    Plugin.prototype.addModule = function(url, name, parent) {
        var params = {
            language: this.options.plugin_language,
        };

        if (parent) {
            params.target_plugin = parent;
        } else {
            params.target_placeholder = this.options.placeholder_id;
        }

        if (document.cookie.match(/modules_disable_confirmation=True/)) {
            $.ajax({
                method: 'POST',
                url: CMS.API.Helpers.updateUrlWithPath(url),
                data: $.extend(params, { csrfmiddlewaretoken: CMS.config.csrf })
            }).done((resp) => {
                const responseDocument = new DOMParser().parseFromString(resp, 'text/html');

                const script = $(responseDocument).find('script').filter((i, el) => {
                    return $(el).text().match(/dataBridge/);
                });

                $.globalEval($(script).html());

                $('.cms-modal-open').find('.cms-modal-close').trigger('click');
                $('.cms-add-plugin-placeholder').remove();
            });
        } else {
            var url = CMS.API.Helpers.updateUrlWithPath(url + '?' + $.param(params));
            var modal = new Modal({
                onClose: this.options.onClose || false,
                redirectOnClose: this.options.redirectOnClose || false
            });

            modal.open({
                url: url,
                title: name
            });
            modal.on('cms.modal.closed', function removePlaceholder() {
                $('.cms-add-plugin-placeholder').remove();
            });
        }
    };


    CMS.Plugin = Plugin;
}

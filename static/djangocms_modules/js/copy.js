import $ from 'jquery';

function findModulePlugin(link) {
    const plugin = link.closest('.cms-plugin');
    const { plugin_id } = plugin.data('cms')[0];
    const index = CMS._instances.findIndex((instance) => instance.options.plugin_id === plugin_id);

    if (index === -1) {
        return null;
    }

    return CMS._instances[index];
}

export function initCopyFromContent() {
    if (!$('.cms-modules-page').length) {
        return;
    }

    $('.js-cms-modules-copy').on('click', (e) => {
        e.preventDefault();

        const link = $(e.target);

        const pluginInstance = findModulePlugin(link);

        if (pluginInstance) {
            pluginInstance.copyPlugin();
        }
    });
}

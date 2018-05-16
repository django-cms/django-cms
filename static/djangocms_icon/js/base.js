import $ from 'jquery';
import IconWidget from './icon-widget';

window.djangoCMSIcon = {
    $
}

$(() => {
    const widgets = $('.djangocms-icon');

    if (widgets.length) {
        widgets.each(function () {
            new IconWidget($(this));
        });
    }
});

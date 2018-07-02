import $ from 'jquery';
import Cookies from 'js-cookie';

const COOKIE_NAME = 'divio-com-alerts';

export function initMessages() {
    const alerts = Cookies.getJSON(COOKIE_NAME) || {};
    const currentAlert = $('.js-global-alert');
    const id = currentAlert.data('id');

    if (!alerts[id]) {
        currentAlert.css('display', 'block').addClass('show');

        currentAlert.find('.close').on('click', () => {
            alerts[id] = true;
            Cookies.set(COOKIE_NAME, alerts, { expires: 365 });

            currentAlert.removeClass('show');
        });
    }
}

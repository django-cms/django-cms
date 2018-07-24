import $ from 'jquery';
import Velocity from 'velocity-animate';
import 'velocity-ui-pack';
import { scrollTo } from 'addons/localscroll';

Velocity.RegisterEffect('transition.expandIn', {
    defaultDuration: 700,
    calls: [
        [
            {
                opacity: [1, 0],
                transformOriginX: ['50%', '50%'],
                transformOriginY: ['50%', '50%'],
                scaleX: [1, 0.9],
                scaleY: [1, 0.9],
                translateZ: 0,
            },
        ],
    ],
});
Velocity.RegisterEffect('transition.expandOut', {
    defaultDuration: 700,
    calls: [
        [
            {
                opacity: [0, 1],
                transformOriginX: ['50%', '50%'],
                transformOriginY: ['50%', '50%'],
                scaleX: 0.9,
                scaleY: 0.9,
                translateZ: 0,
            },
        ],
    ],
    reset: { scaleX: 1, scaleY: 1 },
});

function initSticky() {
    const win = $(window);
    // let position = win.scrollTop();

    win.on('scroll', () => {
        const scroll = win.scrollTop();

        // if (scroll < position) {
        //     console.log('scrolling up');
        // } else {
        //     console.log('scrolling down');
        // }

        if (scroll >= 20) {
            $('.main-nav').addClass('main-nav-scrolled');
        } else {
            $('.main-nav').removeClass('main-nav-scrolled');
        }

        // position = scroll;
    }).trigger('scroll');
}

function initMobileMenu() {
    $('[data-toggle="custom-collapse"]').on('click', async function () {
        const toggle = $(this);
        const isCollapsed = toggle.hasClass('collapsed');
        const target = $(toggle.data('target'));
        const html = $('html');

        if (isCollapsed) {
            await scrollTo(0, 30);

            toggle.removeClass('collapsed');
            toggle.attr('aria-expanded', true);
            Velocity(target, 'transition.expandIn', {
                duration: 200,
                complete: () => html.addClass('mobile-menu-shown'),
            });
            Velocity(document.querySelectorAll('.navbar-collapse-container .nav-link'), 'transition.slideLeftIn', {
                duration: 200,
                display: 'flex',
                stagger: 80,
            });

        } else {
            toggle.attr('aria-expanded', false);
            toggle.addClass('collapsed');
            Velocity(target, 'transition.expandOut', {
                duration: 200,
            });
            html.removeClass('mobile-menu-shown');
        }
    });
}

export function initHeader() {
    initSticky();
    initMobileMenu();
}

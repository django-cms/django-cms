export function initHeader() {
    const win = $(window);
    const mainNav = $('.main-nav');

    win.on('scroll', () => {
        if (win.scrollTop() > 0) {
            mainNav.addClass('main-nav-scrolled');
        } else {
            mainNav.removeClass('main-nav-scrolled');
        }
    }).trigger('scroll');
}

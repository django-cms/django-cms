export function initHeader() {
    const win = $(window);

    win.on('scroll', () => {
        if (win.scrollTop() > 0) {
            $('.main-nav').addClass('main-nav-scrolled');
        } else {
            $('.main-nav').removeClass('main-nav-scrolled');
        }
    }).trigger('scroll');
}

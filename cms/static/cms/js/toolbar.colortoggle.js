(function($) {
    function switch_color_scheme(body, scheme) {
        body.attr('data-color-scheme', scheme);
        body.find('iframe').each(function(i, e) {
            e.contentDocument.documentElement.dataset.colorScheme = scheme;
        });
    }

    function isSafari() {
        return navigator.userAgent.toLowerCase().indexOf('safari/') > -1;
    }

    var toggler = $('#cms-color-scheme-toggle');
    var $html = $('html');
    toggler.on('click', function () {
        var state = $html.attr('data-color-scheme');
        switch (state) {
            case 'light':
                switch_color_scheme($html, 'dark');
                break;
            case 'dark':
                switch_color_scheme($html, 'light');
                break;
            default:
                break;
        }
        // Safari needs to redraw to adjust scrollbars etc.
        if (isSafari()) {
            document.documentElement.hidden = true;
            setTimeout(function () {
                document.documentElement.hidden = false;
            }, 2);
        }
    });
})(CMS.$);

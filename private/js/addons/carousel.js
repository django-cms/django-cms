import $ from 'jquery';
import 'slick-carousel';

export function initBlogCarousel(selector = '.js-carousel') {
    $(selector).each((i, el) => {
        const carousel = $(el);
        const extraSettings = carousel.data('carousel');
        const inner = carousel.find('> .carousel-inner');
        const prevArrow = carousel.find('.carousel-control.left');
        const nextArrow = carousel.find('.carousel-control.right');

        inner.slick({
            slidesToShow: 2,
            slidesToScroll: 2,
            infinite: false,
            prevArrow,
            nextArrow,
            pauseOnHover: true,
            pauseOnFocus: true,
            ...extraSettings,
            responsive: [
                {
                    breakpoint: 992,
                    settings: {
                        slidesToShow: 1,
                        slidesToScroll: 1,
                        infinite: true,
                    },
                },
            ],
        });

        carousel.addClass('carousel-ready');
    });
}

export function initIframeCarousel(selector = '.js-carousel-iframe') {
    const carousel = $(selector);
    const extraSettings = carousel.data();
    const inner = carousel.find('> .carousel-inner');
    const prevArrow = carousel.find('.carousel-control-prev');
    const nextArrow = carousel.find('.carousel-control-next');

    inner.slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        infinite: true,
        prevArrow,
        nextArrow,
        pauseOnHover: true,
        pauseOnFocus: true,
        dots: true,
        ...extraSettings,
    });
    carousel.addClass('carousel-ready');
}

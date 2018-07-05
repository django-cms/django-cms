import LazyLoad from 'vanilla-lazyload';

export let lazyloadInstance;

export function initLazyLoad() {
    lazyloadInstance = new LazyLoad({
        elements_selector: '.js-lazyload',
        class_loading: 'img-lazyload-loading',
    });
}

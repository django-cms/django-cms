import Breakpoint from 'bootstrap-breakpoints';

Breakpoint.init({
    xs: {
        min: 0,
        max: 575,
    },
    sm: {
        min: 576,
        max: 767,
    },
    md: {
        min: 768,
        max: 991,
    },
    lg: {
        min: 992,
        max: 1199,
    },
    xl: {
        min: 1200,
        max: Infinity,
    },
});

export default Breakpoint;

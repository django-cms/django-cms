import $ from 'jquery';
import noUISlider from 'nouislider';
import Sticky from 'sticky-js';


const Sliders = {};

class PricingSlider {

    constructor(options) {
        this.options = options;
        this.priceContainer = this.options.priceContainer;
        this.baseValue = this.priceContainer.text();
        this.elements = this.options.container.find('.js-range-slider');
        this.elements.each((index, element) => {
            this._initialize(element);
        });
    }

    _initialize(element) {
        let el = $(element);
        let data = el.data();
        let range = {};
        let snap = false;

        // special handling if data-range is defined
        if (data.range) {
            data.range.forEach((choice, index) => {
                let key;

                if (index === 0) {
                    key = 'min';
                } else if (index === data.range.length - 1) {
                    key = 'max';
                } else {
                    key = (index / (data.range.length - 1)) * 100 + '%';
                }

                range[key] = choice;
            });
            snap = true;
        } else {
            range = {
                'min': data.min,
                'max': data.max,
            };
            snap = false;
        }

        noUISlider.create(element, {
            start: data.min,
            // step patterns
            step: data.step,
            tooltips: true,
            snap: snap,
            range,
            format: {
                to: value => {
                    let val = value;
                    let unit = data.unit;

                    if (val <= 1) {
                        unit = unit.replace(/s$/, '');
                    }

                    // normalize data if raw is not set
                    if (!data.raw) {
                        value = Math.round(value);
                    }

                    return value + ' ' + unit;
                },
                from: value => value,
            },
            connect: [true, false],
        }).on('update', (values, handle, unencoded) =>
            this._updatePrice(element, values, handle, unencoded));
    }

    _updatePrice(element, values, handle, unencoded) {
        // we need to loop through each element and get the content
        let baseValue = parseInt(this.baseValue);
        let value = unencoded[0];
        let el = $(element);
        let data = el.data();
        let costs = 0;

        // if it matches the base value no additional
        // calculation is required
        if (value === data.step) {
            // special treatment to handle the base cost of one value
            // this is used to display the general base costs for each group
            if (data.base) {
                el.data('calculatedCosts', data.base);
            } else {
                el.data('calculatedCosts', 0);
            }
        } else {
            // update data costs on each element
            el.data('calculatedCosts', data.cost * (value - data.min));
        }

        // calculate new costs
        this.elements.each((index, item) => {
            let calculatedCosts = parseInt($(item).data('calculatedCosts'));
            if (calculatedCosts) {
                costs += calculatedCosts;
            }
        });

        this.priceContainer.text(costs||baseValue);
    }

    setDataSequence(sequence) {
        let seq = sequence.split(',');

        // cancel if the sequence doesn't match the elements
        if (seq.length !== this.elements.length) {
            return false;
        }

        this.elements.each((index, el) => {
            el.noUiSlider.set(seq[index]);
        });
    }

}

export function initPriceSlider() {
    let tabs = $('.nav-tabs');
    let pane = $('.tab-pane');
    let economySticky;
    let businessSticky;

    Sliders.economy = new PricingSlider({
        container: pane.eq(0),
        priceContainer: $('.pricing-tabs-price-value').eq(0),
    });

    Sliders.business = new PricingSlider({
        container: pane.eq(1),
        priceContainer: $('.pricing-tabs-price-value').eq(1),
    });

    // stick price to container when scrolling
    tabs.find('a').on('click', () => {
        if (economySticky && businessSticky) {
            economySticky.destroy();
            businessSticky.destroy();
        }
        economySticky = new Sticky('.js-pricing-tabs-price-economy');
        businessSticky = new Sticky('.js-pricing-tabs-price-business');
    }).trigger('click');

    // url handling for tabs
    setHash(getHash(window.location.hash));
}

function setHash(obj) {
    let tabs = $('.nav-tabs .nav-link');

    switch(obj.tab) {
    case 'business':
        tabs.eq(1).tab('show');
        break;
    case 'premium':
        tabs.eq(2).tab('show');
        break;
    default:
        tabs.eq(0).tab('show');
    }

    // pass to initialisation, can be: 2,6,500,6,15,4
    if (obj.economy) {
        Sliders.economy.setDataSequence(obj.economy);
    }
    if (obj.business) {
        Sliders.business.setDataSequence(obj.business);
    }
}

// for example
// #tab=business&economy=2,6,500,6,15,4
function getHash(hash) {
    hash = hash.substr(1);

    let result = hash.split('&').reduce((result, item) => {
        let parts = item.split('=');
        result[parts[0]] = parts[1];
        return result;
    }, {});

    return result;
}

// sample markup
// <div class="js-range-slider"
//     data-cost="2"
//     data-unit="Instances"
//
//     data-value="1"
//     data-step="1"
//     data-min="1"
//     data-max="10"
// ></div>

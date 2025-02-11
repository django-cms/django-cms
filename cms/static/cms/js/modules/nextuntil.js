/**
 * Essentially same as jQuery's `.nextUntil` but also includes non-element nodes.
 *
 * @function nextUntil
 * @public
 * @param {Element} element to start from
 * @param {String} until class name of the element
 * @returns {Array<Element>} resulting array of elements
 */

export default function nextUntil(element, until) {
    const regex = new RegExp(until);
    const next = [];
    let el = element;

    while (
        el.nextSibling &&
        !(
            el.nextSibling.className &&
            // in case it's and svg element, it's `className` is not a string
            typeof el.nextSibling.className === 'string' &&
            el.nextSibling.className.match(regex)
        )
    ) {
        el = el.nextSibling;
        next.push(el);
    }

    return next;
}

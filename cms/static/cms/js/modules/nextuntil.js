/**
 * Collects all sibling elements after the given element until an element matching the specified condition is found.
 * Essentially same as jQuery's `.nextUntil` but also includes non-element nodes.
 *
 * @param {Element} element - The starting element.
 * @param {string} until - A string representing the class name pattern to stop at.
 * @returns {Element[]} An array of sibling elements after the given element until the condition is met.
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

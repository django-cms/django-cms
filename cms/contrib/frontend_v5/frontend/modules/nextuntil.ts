/**
 * Walk subsequent siblings (including non-element nodes) of `element`
 * until the next sibling whose className matches `until`. The matching
 * sibling is excluded.
 *
 * Like jQuery's `.nextUntil` but also returns text and comment nodes,
 * which we need when consolidating template-bracketed plugin content
 * (`<template class="cms-plugin-start">…text and elements…
 *  <template class="cms-plugin-end">`).
 */
export default function nextUntil(element: Node, until: string): Node[] {
    const regex = new RegExp(until);
    const next: Node[] = [];
    let el: Node = element;

    while (el.nextSibling) {
        const sibling = el.nextSibling as Node & { className?: unknown };
        // SVG elements expose `className` as an SVGAnimatedString; only
        // string-valued className participates in the until-match.
        if (
            sibling.className &&
            typeof sibling.className === 'string' &&
            regex.test(sibling.className)
        ) {
            break;
        }
        el = sibling;
        next.push(sibling);
    }

    return next;
}

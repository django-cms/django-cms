/*
 * Modal position calculation. Mirrors `_calculateNewPosition` from
 * `cms.modal.js`. Pure function — given current modal CSS, viewport
 * size, and requested width/height, returns the target dimensions
 * and (top, left) center coordinates. Returns `triggerMaximized:
 * true` when the requested size doesn't fit the viewport.
 */

const WIDTH_OFFSET = 300;
const HEIGHT_OFFSET = 300;

export interface PositionInput {
    /** Modal's current `style.left` (parsed CSS string, may be `'50%'`). */
    currentLeft: string;
    /** Modal's current `style.top`. */
    currentTop: string;
    /** Viewport width. */
    screenWidth: number;
    /** Viewport height. */
    screenHeight: number;
    /** Requested width override (`opts.width` from `open()`). */
    requestedWidth?: number | undefined;
    /** Requested height override (`opts.height`). */
    requestedHeight?: number | undefined;
    /** Modal's minimum width — `options.minWidth`. */
    minWidth: number;
    /** Modal's minimum height — `options.minHeight`. */
    minHeight: number;
}

export interface Position {
    width: number;
    height: number;
    /** Center top (px), or `undefined` if no recentre needed. */
    top: number | undefined;
    /** Center left (px), or `undefined` if no recentre needed. */
    left: number | undefined;
    /** True when the requested size doesn't fit — caller should maximize. */
    triggerMaximized: boolean;
}

export function calculatePosition(input: PositionInput): Position {
    const modalWidth = input.requestedWidth ?? input.minWidth;
    const modalHeight = input.requestedHeight ?? input.minHeight;
    const fitsWidth = input.screenWidth >= modalWidth + WIDTH_OFFSET;
    const fitsHeight = input.screenHeight >= modalHeight + HEIGHT_OFFSET;

    const width =
        fitsWidth && input.requestedWidth === undefined
            ? input.screenWidth - WIDTH_OFFSET
            : modalWidth;
    const height =
        fitsHeight && input.requestedHeight === undefined
            ? input.screenHeight - HEIGHT_OFFSET
            : modalHeight;

    let cl: number;
    let ct: number;
    if (input.currentLeft === '50%') cl = input.screenWidth / 2;
    else cl = parseInt(input.currentLeft, 10) || 0;
    if (input.currentTop === '50%') ct = input.screenHeight / 2;
    else ct = parseInt(input.currentTop, 10) || 0;

    let newLeft: number | undefined;
    let newTop: number | undefined;

    if (
        width / 2 + cl > input.screenWidth ||
        height / 2 + ct > input.screenHeight ||
        cl - width / 2 < 0 ||
        ct - height / 2 < 0
    ) {
        newLeft = input.screenWidth / 2;
        newTop = input.screenHeight / 2;
    }

    const triggerMaximized =
        width >= input.screenWidth || height >= input.screenHeight;

    return {
        width,
        height,
        top: newTop,
        left: newLeft,
        triggerMaximized,
    };
}

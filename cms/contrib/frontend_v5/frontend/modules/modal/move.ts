/*
 * Modal drag and resize controllers. Each returns a teardown handle
 * so the modal class can release the body-level pointermove/pointerup
 * listeners cleanly. Touch actions are disabled on the body while a
 * gesture is in progress and re-enabled on release.
 */

export interface DragOptions {
    /** The `.cms-modal` element. */
    modal: HTMLElement;
    /** The `<html>` element — owns body-level pointer listeners. */
    body: HTMLElement;
    /** The drag-shim element — shown during drag to swallow events. */
    shim: HTMLElement;
    /** The pointer event that initiated the drag. */
    pointerEvent: PointerEvent;
    /** When true, the gesture is cancelled (caller is in maximised/minimised state). */
    cancelled?: boolean;
}

export interface DragHandle {
    /** Release listeners. The caller invokes this on pointerup. */
    destroy(): void;
}

/**
 * Begin a drag of the modal — pin to the cursor delta until pointerup.
 * Returns a handle whose destroy() releases the listeners; caller is
 * responsible for invoking destroy() on pointerup/pointercancel.
 */
export function startDrag(opts: DragOptions): DragHandle | null {
    if (opts.cancelled) return null;

    const startLeft = parseFloat(opts.modal.style.left) || 0;
    const startTop = parseFloat(opts.modal.style.top) || 0;
    const startX = opts.pointerEvent.pageX;
    const startY = opts.pointerEvent.pageY;

    opts.shim.classList.add('cms-modal-shim--active');
    document.body.style.touchAction = 'none';

    const onMove = (e: PointerEvent): void => {
        const dx = startX - e.pageX;
        const dy = startY - e.pageY;
        opts.modal.style.left = `${startLeft - dx}px`;
        opts.modal.style.top = `${startTop - dy}px`;
    };
    const onUp = (): void => {
        cleanup();
    };

    function cleanup(): void {
        opts.body.removeEventListener('pointermove', onMove);
        opts.body.removeEventListener('pointerup', onUp);
        opts.body.removeEventListener('pointercancel', onUp);
        opts.shim.classList.remove('cms-modal-shim--active');
        document.body.style.touchAction = '';
    }

    opts.body.addEventListener('pointermove', onMove);
    opts.body.addEventListener('pointerup', onUp);
    opts.body.addEventListener('pointercancel', onUp);

    return { destroy: cleanup };
}

export interface ResizeOptions {
    modal: HTMLElement;
    body: HTMLElement;
    shim: HTMLElement;
    pointerEvent: PointerEvent;
    /** RTL flag — flips horizontal delta. */
    rtl: boolean;
    /** Minimum allowed width — clamps if smaller. */
    minWidth: number;
    /** Minimum allowed height — clamps if smaller. */
    minHeight: number;
    cancelled?: boolean;
}

export type ResizeHandle = DragHandle;

export function startResize(opts: ResizeOptions): ResizeHandle | null {
    if (opts.cancelled) return null;

    const rect = opts.modal.getBoundingClientRect();
    const startWidth = rect.width;
    const startHeight = rect.height;
    const startLeft = parseFloat(opts.modal.style.left) || 0;
    const startTop = parseFloat(opts.modal.style.top) || 0;
    const dir = opts.rtl ? -1 : +1;
    const startX = opts.pointerEvent.pageX;
    const startY = opts.pointerEvent.pageY;

    opts.shim.classList.add('cms-modal-shim--active');
    document.body.style.touchAction = 'none';

    const onMove = (e: PointerEvent): void => {
        const mvX = startX - e.pageX;
        const mvY = startY - e.pageY;
        let w = startWidth - dir * mvX * 2;
        let h = startHeight - mvY * 2;
        let left = dir * mvX + startLeft;
        let top = mvY + startTop;
        if (w <= opts.minWidth) {
            w = opts.minWidth;
            left = startLeft + startWidth / 2 - w / 2;
        }
        if (h <= opts.minHeight) {
            h = opts.minHeight;
            top = startTop + startHeight / 2 - h / 2;
        }
        opts.modal.style.width = `${w}px`;
        opts.modal.style.height = `${h}px`;
        opts.modal.style.left = `${left}px`;
        opts.modal.style.top = `${top}px`;
    };
    const onUp = (): void => cleanup();

    function cleanup(): void {
        opts.body.removeEventListener('pointermove', onMove);
        opts.body.removeEventListener('pointerup', onUp);
        opts.body.removeEventListener('pointercancel', onUp);
        opts.shim.classList.remove('cms-modal-shim--active');
        document.body.style.touchAction = '';
    }

    opts.body.addEventListener('pointermove', onMove);
    opts.body.addEventListener('pointerup', onUp);
    opts.body.addEventListener('pointercancel', onUp);

    return { destroy: cleanup };
}

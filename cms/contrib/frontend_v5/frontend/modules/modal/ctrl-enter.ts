/*
 * Ctrl+Enter / Cmd+Enter quick-save — fires the modal's default
 * action button (`.cms-btn-action:first`) when the user hits the
 * combo from inside the iframe (or the parent doc). Mirrors
 * `_setupCtrlEnterSave`.
 *
 * The legacy ESC trick was kept: tracking `cmdPressed` separately
 * because Mac Cmd-keyup doesn't fire if the cmd key is released
 * outside the iframe. We mirror that to keep parity even though it
 * would be cleaner to read `event.metaKey` directly.
 *
 * Returns a teardown so callers can detach when the modal closes.
 */

export interface CtrlEnterHandle {
    destroy(): void;
}

export function setupCtrlEnterSave(doc: Document): CtrlEnterHandle {
    const isMac = navigator.platform.toLowerCase().includes('mac');
    let cmdPressed = false;

    const onKeydown = (e: KeyboardEvent): void => {
        const isEnter = e.key === 'Enter' || e.keyCode === 13;
        if (e.ctrlKey && isEnter && !isMac) {
            triggerDefault(doc);
            return;
        }
        if (isMac) {
            if (
                e.keyCode === 91 || // CMD_LEFT
                e.keyCode === 93 || // CMD_RIGHT
                e.keyCode === 224 // CMD_FIREFOX
            ) {
                cmdPressed = true;
            }
            if (isEnter && (cmdPressed || e.metaKey)) {
                triggerDefault(doc);
            }
        }
    };
    const onKeyup = (e: KeyboardEvent): void => {
        if (!isMac) return;
        if (
            e.keyCode === 91 ||
            e.keyCode === 93 ||
            e.keyCode === 224
        ) {
            cmdPressed = false;
        }
    };

    doc.addEventListener('keydown', onKeydown);
    doc.addEventListener('keyup', onKeyup);

    return {
        destroy(): void {
            doc.removeEventListener('keydown', onKeydown);
            doc.removeEventListener('keyup', onKeyup);
        },
    };
}

function triggerDefault(doc: Document): void {
    const btn = doc.querySelector<HTMLElement>(
        '.cms-modal-buttons .cms-btn-action',
    );
    btn?.click();
}

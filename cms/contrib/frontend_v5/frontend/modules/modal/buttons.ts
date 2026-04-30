/*
 * Modal footer buttons — clones the rendered Django admin form's
 * submit row (`.submit-row` or `.save-box`) into the modal's
 * `.cms-modal-buttons` strip. Each cloned button submits the form
 * inside the iframe via either `.click()` (multi-button forms) or
 * `requestSubmit` (single-button forms).
 *
 * The "default" button gets the `cms-btn-action` (blue) class; the
 * delete-link gets `cms-btn-caution` (red). A manual Cancel button
 * is appended last and invokes the supplied `onCancel`.
 *
 * Mirrors `_setButtons` from the legacy modal.
 */

import { Helpers } from '../cms-base';

export interface ButtonsOptions {
    /** The iframe whose form we clone buttons from. */
    iframe: HTMLIFrameElement;
    /** The `.cms-modal-buttons` container we render into. */
    container: HTMLElement;
    /** Cancel button label (CMS.config.lang.cancel). */
    cancelLabel: string;
    /** Invoked when Cancel is clicked. */
    onCancel: () => void;
    /** Setter for `hideFrame` — mirrored from the modal so the iframe
     * load handler knows to hide the iframe after submit. */
    setHideFrame: (value: boolean) => void;
    /** Setter for `saved` — set when a non-default action fires
     * (e.g. delete) so the load handler knows to close on next load. */
    setSaved: (value: boolean) => void;
    /** Reference to the modal element — used to hide the iframe on
     * non-default click. */
    modal: HTMLElement;
    /** Setter for the modal-body `cms-loader` class on submit. */
    setBodyLoader: (value: boolean) => void;
    /**
     * Loader for follow-up GET (when the cloned button is an `<a>`
     * rather than a submit input). The legacy code calls
     * `_loadIframe({url, name})` again to re-render the modal.
     */
    loadIframe: (opts: { url: string; name: string }) => void;
}

export function renderButtons(opts: ButtonsOptions): void {
    const doc = opts.iframe.contentDocument;
    if (!doc) return;

    const djangoSuit = doc.querySelectorAll('.suit-columns').length > 0;
    const row = djangoSuit
        ? doc.querySelector<HTMLElement>('.save-box')
        : doc.querySelector<HTMLElement>('.submit-row');
    const form = doc.querySelector<HTMLFormElement>('form');

    // Hide the iframe's submit row so we don't show two button strips.
    // Inline `display: none` rather than `.cms-hidden` because we're
    // operating on the iframe's contentDocument — contrib CSS lives in
    // the parent doc and doesn't apply here.
    doc.querySelectorAll<HTMLElement>('.submit-row').forEach((el) => {
        el.style.display = 'none';
    });

    if (form) {
        form.addEventListener('submit', () => {
            // Hidden by default — `setHideFrame(true)` toggles it.
            // Matches the legacy semantics where pressing Save (default
            // action) hides the iframe immediately so the user doesn't
            // see the redirect flicker.
        });
    }

    let buttons: NodeListOf<HTMLElement> | null = null;
    if (row) {
        buttons = row.querySelectorAll<HTMLElement>('input, a, button');
    }
    // Fallback: scan the form for any submit-type input.
    if (!buttons || buttons.length === 0) {
        const fallbackForm = doc.querySelector<HTMLFormElement>(
            'body:not(.change-list) #content form',
        );
        if (fallbackForm) {
            buttons = fallbackForm.querySelectorAll<HTMLElement>(
                'input[type="submit"], button[type="submit"]',
            );
            buttons.forEach((b) => {
                b.classList.add('deletelink');
                (b as HTMLElement).style.display = 'none';
            });
        }
    }

    // Track default-button click on the iframe form so submit handler
    // knows to hide the frame.
    if (buttons) {
        buttons.forEach((btn) => {
            btn.addEventListener('click', () => {
                if (btn.classList.contains('default')) {
                    opts.setHideFrame(true);
                }
            });
        });
    }

    // Render group containers + Cancel.
    const render = document.createElement('div');
    render.className = 'cms-modal-buttons-inner';

    if (buttons) {
        buttons.forEach((btn, index) => {
            const tag = btn.tagName;
            // Skip hidden inputs.
            if (
                tag === 'INPUT' &&
                (btn as HTMLInputElement).type === 'hidden'
            ) {
                return;
            }
            btn.dataset.rel = `_${index}`;

            let title = '';
            if (tag === 'BUTTON') title = btn.textContent ?? '';
            else
                title =
                    (btn as HTMLInputElement).value ||
                    btn.textContent ||
                    '';

            let cls = 'cms-btn';
            if (btn.classList.contains('default')) cls = 'cms-btn cms-btn-action';
            if (btn.classList.contains('deletelink'))
                cls = 'cms-btn cms-btn-caution';

            const a = document.createElement('a');
            a.href = '#';
            a.className = `${cls} ${btn.className}`;
            a.textContent = title;

            const onActivate = (e: Event): void => {
                e.preventDefault();

                if (tag === 'A') {
                    const href =
                        (btn as HTMLAnchorElement).href || '';
                    opts.loadIframe({
                        url: Helpers.updateUrlWithPath(href),
                        name: title,
                    });
                }

                if (
                    btn.classList.contains('default') ||
                    btn.classList.contains('deletelink')
                ) {
                    if (btn.classList.contains('default')) {
                        opts.setHideFrame(true);
                    } else {
                        opts.modal
                            .querySelectorAll<HTMLElement>(
                                '.cms-modal-frame iframe',
                            )
                            .forEach((f) => {
                                f.classList.add('cms-hidden');
                            });
                        opts.setSaved(true);
                    }
                }

                if (tag === 'INPUT' || tag === 'BUTTON') {
                    opts.setBodyLoader(true);
                    const frm = (btn as HTMLInputElement | HTMLButtonElement)
                        .form;
                    if (!frm) return;
                    const otherButtons = frm.querySelectorAll(
                        'button, input[type="button"], input[type="submit"]',
                    );
                    if (otherButtons.length > 1) {
                        (btn as HTMLElement).click();
                    } else {
                        // Single-button form: dispatch then submit.
                        const evt = new CustomEvent('submit', {
                            bubbles: false,
                            cancelable: true,
                        });
                        if (frm.dispatchEvent(evt)) {
                            try {
                                frm.submit();
                            } catch {
                                /* WebKit no-op; Gecko throws */
                            }
                        }
                    }
                }
            };

            a.addEventListener('click', onActivate);
            a.addEventListener('touchend', onActivate);

            const group = document.createElement('div');
            group.className = 'cms-modal-item-buttons';
            group.appendChild(a);
            render.appendChild(group);
        });
    }

    // Append the manual Cancel button.
    const cancel = document.createElement('a');
    cancel.href = '#';
    cancel.className = 'cms-btn';
    cancel.textContent = opts.cancelLabel;
    cancel.addEventListener('click', (e) => {
        e.preventDefault();
        opts.onCancel();
    });
    const cancelGroup = document.createElement('div');
    cancelGroup.className = 'cms-modal-item-buttons';
    cancelGroup.appendChild(cancel);
    render.appendChild(cancelGroup);

    opts.container.replaceChildren(render);
}

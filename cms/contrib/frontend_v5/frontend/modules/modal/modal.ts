/*
 * Modal class — port of `cms.modal.js`. Iframe + markup modal with
 * drag, resize, maximize, minimize, change tracking, breadcrumbs,
 * footer button cloning, Ctrl-Enter save, Esc-cancel-with-dirty-check.
 *
 * Public surface (read by the toolbar's `_delegate`, by plugin
 * code, and by tests):
 *
 *   class Modal {
 *       constructor(options?: ModalOptions)
 *       open(opts: { url?, html?, title?, ... }): this
 *       close(): boolean | void
 *       minimize(): boolean | void
 *       maximize(): boolean | void
 *   }
 *
 * Most of the heavy lifting (iframe load handling, button cloning,
 * breadcrumbs, drag, resize) is delegated to focused submodules.
 * The class's job is to:
 *   - Stand up the UI refs against the rendered `.cms-modal` element.
 *   - Maintain instance state (maximized/minimized, saved, hideFrame).
 *   - Wire transient listeners (Esc handler, beforeunload guard).
 *   - Coordinate the open/close lifecycle and animation.
 */

import { Helpers, KEYS } from '../cms-base';
import { ChangeTracker } from '../changetracker';
import { hideLoader } from '../loader';
import keyboard from '../keyboard';
import { getCmsConfig } from '../plugins/cms-globals';
import { untrap, trap } from '../trap';
import {
    loadIframe as loadIframeImpl,
    type LoadIframeOptions,
} from './iframe-loader';
import {
    calculatePosition,
    type Position,
} from './position';
import { startDrag, startResize } from './move';

const DEFAULT_OPTIONS: Required<Omit<ModalOptions, 'onClose'>> & {
    onClose: ModalOptions['onClose'];
} = {
    onClose: false,
    closeOnEsc: true,
    minHeight: 400,
    minWidth: 800,
    modalDuration: 200,
    resizable: true,
    maximizable: true,
    minimizable: true,
};

const MINIMIZED_OFFSET = 50;

export interface ModalOptions {
    /** URL to redirect to on close, `false`/`null` to skip. */
    onClose?: string | false | null;
    closeOnEsc?: boolean;
    minHeight?: number;
    minWidth?: number;
    modalDuration?: number;
    resizable?: boolean;
    maximizable?: boolean;
    minimizable?: boolean;
}

export interface ModalOpenOptions {
    url?: string | undefined;
    html?: string | HTMLElement | undefined;
    title?: string | undefined;
    subtitle?: string | undefined;
    breadcrumbs?: Array<{ title: string; url: string }> | undefined;
    width?: number | undefined;
    height?: number | undefined;
}

interface ModalUi {
    modal: HTMLElement;
    body: HTMLElement;
    toolbarLeftPart: HTMLElement | null;
    minimizeButton: HTMLElement | null;
    maximizeButton: HTMLElement | null;
    title: HTMLElement | null;
    titlePrefix: HTMLElement;
    titleSuffix: HTMLElement;
    resize: HTMLElement | null;
    breadcrumb: HTMLElement;
    closeAndCancel: NodeListOf<HTMLElement>;
    modalButtons: HTMLElement;
    modalBody: HTMLElement;
    frame: HTMLElement;
    shim: HTMLElement;
}

let previousKeyboardContext: string | null = null;
let previouslyFocusedElement: Element | null = null;

export class Modal {
    public readonly options: typeof DEFAULT_OPTIONS;
    public ui!: ModalUi;
    public maximized = false;
    public minimized = false;
    public saved = false;
    public hideFrame = false;
    public enforceReload = false;
    public enforceClose = false;
    public tracker: ChangeTracker | null = null;
    public triggerMaximized = false;

    private savedCss: Partial<CSSStyleDeclaration> | null = null;
    private escListener: ((e: KeyboardEvent) => void) | null = null;
    private buttonCleanups: Array<() => void> = [];
    private boundBeforeUnload: (e: BeforeUnloadEvent) => void;

    constructor(options: ModalOptions = {}) {
        this.options = { ...DEFAULT_OPTIONS, ...options };
        this.boundBeforeUnload = (e) => this.onBeforeUnload(e);
        this.setupUi();
    }

    // ────────────────────────────────────────────────────────────
    // Public lifecycle
    // ────────────────────────────────────────────────────────────

    open(opts: ModalOpenOptions): this {
        if (!opts || (!opts.url && !opts.html)) {
            throw new Error('The arguments passed to "open" were invalid.');
        }

        this.bindControlEvents();

        Helpers.dispatchEvent('modal-load', { instance: this });

        if (this.ui.resize) {
            this.ui.resize.style.display = this.options.resizable ? '' : 'none';
        }
        if (this.ui.minimizeButton) {
            this.ui.minimizeButton.style.display = this.options.minimizable
                ? ''
                : 'none';
        }
        if (this.ui.maximizeButton) {
            this.ui.maximizeButton.style.display = this.options.maximizable
                ? ''
                : 'none';
        }

        const position = this.calculateNewPosition(opts);

        this.ui.maximizeButton?.classList.remove('cms-modal-maximize-active');
        this.maximized = false;

        if (this.ui.body.classList.contains('cms-modal-minimized')) {
            this.minimized = true;
            this.minimize();
        }

        this.ui.modalButtons.replaceChildren();
        this.ui.breadcrumb.replaceChildren();
        this.ui.modal.classList.remove('cms-modal-has-breadcrumb');

        // Hide the tooltip if it's around (defensive — Tooltip may
        // not have been instantiated yet).
        const tooltip = (
            window.CMS?.API as { Tooltip?: { hide(): void } } | undefined
        )?.Tooltip;
        tooltip?.hide();

        if (opts.url) {
            this.loadIframe({
                url: opts.url,
                title: opts.title,
                breadcrumbs: opts.breadcrumbs,
            });
        } else {
            this.loadMarkup({
                html: opts.html!,
                title: opts.title,
                subtitle: opts.subtitle,
            });
        }

        Helpers.dispatchEvent('modal-loaded', { instance: this });

        const currentContext = keyboard.getContext();
        if (currentContext !== 'modal') {
            previousKeyboardContext = currentContext;
            previouslyFocusedElement = document.activeElement;
        }

        this.show({
            duration: this.options.modalDuration,
            ...position,
        });

        keyboard.setContext('modal');
        return this;
    }

    close(): boolean | void {
        // The legacy event payload exposes `isDefaultPrevented`; the
        // ported event bus doesn't carry that semantic, so we treat
        // close as always proceeding (matching the documented intent).
        Helpers.dispatchEvent('modal-close', { instance: this });

        Helpers._getWindow().removeEventListener(
            'beforeunload',
            this.boundBeforeUnload,
        );

        if (this.options.onClose) {
            Helpers.reloadBrowser(this.options.onClose);
        }
        untrap(this.ui.body);
        keyboard.setContext(previousKeyboardContext ?? 'cms');
        try {
            (previouslyFocusedElement as HTMLElement | null)?.focus();
        } catch {
            /* ignore */
        }
        this.hide({ duration: this.options.modalDuration / 2 });
    }

    // ────────────────────────────────────────────────────────────
    // Maximize / minimize
    // ────────────────────────────────────────────────────────────

    minimize(): boolean | void {
        if (this.maximized) return false;

        if (!this.minimized) {
            this.savedCss = {
                left: this.ui.modal.style.left,
                top: this.ui.modal.style.top,
                marginLeft: this.ui.modal.style.marginLeft,
                marginTop: this.ui.modal.style.marginTop,
            };
            this.ui.body.classList.add('cms-modal-minimized');
            const tlw = outerWidthWithMargins(this.ui.toolbarLeftPart);
            this.ui.modal.style.left = `${tlw + MINIMIZED_OFFSET}px`;
            this.minimized = true;
        } else {
            this.ui.body.classList.remove('cms-modal-minimized');
            this.applySavedCss();
            this.minimized = false;
        }
    }

    maximize(): boolean | void {
        if (this.minimized) return false;

        if (!this.maximized) {
            this.savedCss = {
                left: this.ui.modal.style.left,
                top: this.ui.modal.style.top,
                marginLeft: this.ui.modal.style.marginLeft,
                marginTop: this.ui.modal.style.marginTop,
                width: this.ui.modal.style.width,
                height: this.ui.modal.style.height,
            };
            this.ui.body.classList.add('cms-modal-maximized');
            this.maximized = true;
            Helpers.dispatchEvent('modal-maximized', { instance: this });
        } else {
            this.ui.body.classList.remove('cms-modal-maximized');
            this.applySavedCss();
            this.maximized = false;
            Helpers.dispatchEvent('modal-restored', { instance: this });
        }
    }

    // ────────────────────────────────────────────────────────────
    // Internal
    // ────────────────────────────────────────────────────────────

    private setupUi(): void {
        const modal = document.querySelector<HTMLElement>('.cms-modal');
        if (!modal) {
            throw new Error(
                'Modal markup not found — `.cms-modal` is required.',
            );
        }
        this.ui = {
            modal,
            body: document.documentElement,
            toolbarLeftPart: document.querySelector<HTMLElement>(
                '.cms-toolbar-left',
            ),
            minimizeButton: modal.querySelector<HTMLElement>(
                '.cms-modal-minimize',
            ),
            maximizeButton: modal.querySelector<HTMLElement>(
                '.cms-modal-maximize',
            ),
            title: modal.querySelector<HTMLElement>('.cms-modal-title'),
            titlePrefix: modal.querySelector<HTMLElement>(
                '.cms-modal-title-prefix',
            )!,
            titleSuffix: modal.querySelector<HTMLElement>(
                '.cms-modal-title-suffix',
            )!,
            resize: modal.querySelector<HTMLElement>('.cms-modal-resize'),
            breadcrumb: modal.querySelector<HTMLElement>(
                '.cms-modal-breadcrumb',
            )!,
            closeAndCancel: modal.querySelectorAll<HTMLElement>(
                '.cms-modal-close, .cms-modal-cancel',
            ),
            modalButtons: modal.querySelector<HTMLElement>(
                '.cms-modal-buttons',
            )!,
            modalBody: modal.querySelector<HTMLElement>('.cms-modal-body')!,
            frame: modal.querySelector<HTMLElement>('.cms-modal-frame')!,
            shim: modal.querySelector<HTMLElement>('.cms-modal-shim')!,
        };
    }

    private bindControlEvents(): void {
        // Tear down any previous wiring first.
        for (const c of this.buttonCleanups) c();
        this.buttonCleanups = [];

        const onMinimize = (e: Event): void => {
            const ke = e as KeyboardEvent;
            if (
                e.type !== 'keyup' ||
                (e.type === 'keyup' && ke.keyCode === KEYS.ENTER)
            ) {
                e.preventDefault();
                this.minimize();
            }
        };
        const onMaximize = (e: Event): void => {
            const ke = e as KeyboardEvent;
            if (
                e.type !== 'keyup' ||
                (e.type === 'keyup' && ke.keyCode === KEYS.ENTER)
            ) {
                e.preventDefault();
                this.maximize();
            }
        };
        const onCancel = (e: Event): void => {
            const ke = e as KeyboardEvent;
            if (
                e.type !== 'keyup' ||
                (e.type === 'keyup' && ke.keyCode === KEYS.ENTER)
            ) {
                e.preventDefault();
                this.cancelHandler();
            }
        };
        const onTitleDown = (e: Event): void => {
            e.preventDefault();
            startDrag({
                modal: this.ui.modal,
                body: this.ui.body,
                shim: this.ui.shim,
                pointerEvent: e as PointerEvent,
                cancelled: this.maximized || this.minimized,
            });
        };
        const onTitleDouble = (): void => {
            this.maximize();
        };
        const onResizeDown = (e: Event): void => {
            e.preventDefault();
            const rtl =
                getComputedStyle(this.ui.resize!).direction === 'rtl';
            startResize({
                modal: this.ui.modal,
                body: this.ui.body,
                shim: this.ui.shim,
                pointerEvent: e as PointerEvent,
                rtl,
                minWidth: this.options.minWidth,
                minHeight: this.options.minHeight,
                cancelled: this.maximized,
            });
        };
        const onBreadcrumbClick = (e: Event): void => {
            const target = e.target as HTMLElement;
            const a = target.closest<HTMLAnchorElement>('a');
            if (!a) return;
            e.preventDefault();
            this.changeIframe(a);
        };

        this.bindOne(
            this.ui.minimizeButton,
            ['click', 'touchend', 'keyup'],
            onMinimize,
        );
        this.bindOne(
            this.ui.maximizeButton,
            ['click', 'touchend', 'keyup'],
            onMaximize,
        );
        this.bindOne(this.ui.title, ['pointerdown'], onTitleDown);
        this.bindOne(this.ui.title, ['dblclick'], onTitleDouble);
        this.bindOne(this.ui.resize, ['pointerdown'], onResizeDown);
        for (const el of Array.from(this.ui.closeAndCancel)) {
            this.bindOne(el, ['click', 'touchend', 'keyup'], onCancel);
        }
        this.bindOne(
            this.ui.breadcrumb,
            ['click'],
            onBreadcrumbClick,
        );
    }

    private bindOne(
        el: HTMLElement | null,
        events: string[],
        handler: (e: Event) => void,
    ): void {
        if (!el) return;
        for (const ev of events) {
            el.addEventListener(ev, handler);
        }
        this.buttonCleanups.push(() => {
            for (const ev of events) {
                el.removeEventListener(ev, handler);
            }
        });
    }

    private calculateNewPosition(
        opts: ModalOpenOptions,
    ): Pick<Position, 'width' | 'height' | 'top' | 'left'> {
        const result = calculatePosition({
            currentLeft:
                this.ui.modal.style.left ||
                (getComputedStyle(this.ui.modal).left ?? '50%'),
            currentTop:
                this.ui.modal.style.top ||
                (getComputedStyle(this.ui.modal).top ?? '50%'),
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            requestedWidth: opts.width,
            requestedHeight: opts.height,
            minWidth: this.options.minWidth,
            minHeight: this.options.minHeight,
        });
        if (result.triggerMaximized) this.triggerMaximized = true;
        return result;
    }

    private show(
        opts: {
            duration: number;
            width: number;
            height: number;
            top?: number | undefined;
            left?: number | undefined;
        },
    ): void {
        if (this.ui.modal.classList.contains('cms-modal-open')) {
            this.ui.modal.classList.add('cms-modal-morphing');
        }
        Object.assign(this.ui.modal.style, {
            display: 'block',
            width: `${opts.width}px`,
            height: `${opts.height}px`,
            top: opts.top !== undefined ? `${opts.top}px` : this.ui.modal.style.top,
            left: opts.left !== undefined ? `${opts.left}px` : this.ui.modal.style.left,
            marginLeft: `${-(opts.width / 2)}px`,
            marginTop: `${-(opts.height / 2)}px`,
        });
        // Defer to next frame so transitions kick in.
        setTimeout(() => {
            this.ui.modal.classList.add('cms-modal-open');
        }, 0);

        // After the legacy "transitionend" duration, finalise.
        setTimeout(() => {
            this.ui.modal.classList.remove('cms-modal-morphing');
            Object.assign(this.ui.modal.style, {
                marginLeft: `${-(opts.width / 2)}px`,
                marginTop: `${-(opts.height / 2)}px`,
            });
            if (this.triggerMaximized) {
                this.triggerMaximized = false;
                this.maximize();
            }
            (window.CMS?.API as { locked?: boolean } | undefined) &&
                ((window.CMS!.API as { locked?: boolean }).locked = false);
            Helpers.dispatchEvent('modal-shown', { instance: this });
        }, opts.duration);

        // ESC to close.
        this.escListener?.bind(this);
        if (this.escListener) {
            this.ui.body.removeEventListener('keydown', this.escListener);
        }
        const escHandler = (e: KeyboardEvent): void => {
            if (e.keyCode === KEYS.ESC && this.options.closeOnEsc) {
                e.stopPropagation();
                if (this.confirmDirtyEscCancel()) this.cancelHandler();
            }
        };
        this.escListener = escHandler;
        this.ui.body.addEventListener('keydown', escHandler);
        this.ui.modal.focus();
    }

    private hide(opts?: { duration?: number }): void {
        const duration = opts?.duration ?? this.options.modalDuration;
        this.ui.frame.replaceChildren();
        this.ui.modalBody.classList.remove('cms-loader');
        this.ui.modal.classList.remove('cms-modal-open');

        setTimeout(() => {
            this.ui.modal.style.display = 'none';
        }, duration);

        // Reset minimize/maximize.
        setTimeout(() => {
            if (this.minimized) this.minimize();
            if (this.maximized) this.maximize();
            hideLoader();
            Helpers.dispatchEvent('modal-closed', { instance: this });
        }, duration);

        if (this.escListener) {
            this.ui.body.removeEventListener('keydown', this.escListener);
            this.escListener = null;
        }
    }

    private cancelHandler(): void {
        this.options.onClose = null;
        this.close();
    }

    private confirmDirtyEscCancel(): boolean {
        if (this.tracker?.isFormChanged()) {
            const lang = (
                getCmsConfig() as {
                    lang?: { confirmDirty?: string; confirmDirtyESC?: string };
                }
            ).lang;
            const message = `${lang?.confirmDirty ?? ''}\n\n${
                lang?.confirmDirtyESC ?? ''
            }`;
            return Helpers.secureConfirm(message);
        }
        return true;
    }

    private onBeforeUnload(e: BeforeUnloadEvent): void {
        if (this.tracker?.isFormChanged()) {
            const lang = (getCmsConfig() as { lang?: { confirmDirty?: string } })
                .lang;
            e.returnValue = lang?.confirmDirty ?? '';
        }
    }

    private changeIframe(anchor: HTMLAnchorElement): void {
        if (anchor.classList.contains('active')) return;
        const parent = anchor.parentElement;
        parent
            ?.querySelectorAll<HTMLElement>('a')
            .forEach((a) => a.classList.remove('active'));
        anchor.classList.add('active');
        this.loadIframe({ url: anchor.getAttribute('href') ?? '' });
        this.ui.titlePrefix.textContent = anchor.textContent ?? '';
    }

    private loadIframe(opts: LoadIframeOptions): void {
        loadIframeImpl(
            {
                modal: this.ui.modal,
                frame: this.ui.frame,
                modalBody: this.ui.modalBody,
                modalButtons: this.ui.modalButtons,
                breadcrumb: this.ui.breadcrumb,
                titlePrefix: this.ui.titlePrefix,
                titleSuffix: this.ui.titleSuffix,
                getSaved: () => this.saved,
                setSaved: (v) => {
                    this.saved = v;
                },
                setHideFrame: (v) => {
                    this.hideFrame = v;
                },
                getOnClose: () => this.options.onClose,
                enforceReload: this.enforceReload,
                enforceClose: this.enforceClose,
                close: () => this.close(),
                setTracker: (t) => {
                    this.tracker = t;
                    Helpers._getWindow().addEventListener(
                        'beforeunload',
                        this.boundBeforeUnload,
                    );
                },
                loadIframe: (o) => this.loadIframe(o),
            },
            opts,
        );
    }

    private loadMarkup(opts: {
        html: string | HTMLElement;
        title?: string | undefined;
        subtitle?: string | undefined;
    }): void {
        this.ui.modal.classList.remove('cms-modal-iframe');
        this.ui.modal.classList.add('cms-modal-markup');
        this.ui.modalBody.classList.remove('cms-loader');

        if (typeof opts.html === 'string') {
            this.ui.frame.innerHTML = opts.html;
        } else {
            this.ui.frame.replaceChildren(opts.html);
        }
        this.ui.titlePrefix.textContent = opts.title ?? '';
        this.ui.titleSuffix.textContent = opts.subtitle ?? '';
        trap(this.ui.frame);
    }

    private applySavedCss(): void {
        if (!this.savedCss) return;
        for (const [k, v] of Object.entries(this.savedCss)) {
            (this.ui.modal.style as unknown as Record<string, string>)[k] =
                v as string;
        }
    }
}

function outerWidthWithMargins(el: HTMLElement | null): number {
    if (!el) return 0;
    const rect = el.getBoundingClientRect();
    const cs = window.getComputedStyle(el);
    const ml = parseFloat(cs.marginLeft) || 0;
    const mr = parseFloat(cs.marginRight) || 0;
    return rect.width + ml + mr;
}

export default Modal;

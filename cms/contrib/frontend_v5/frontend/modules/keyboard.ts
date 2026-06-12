/*
 * Minimal keyboard module — context-scoped key bindings. Mirrors the
 * legacy `keyboard.js` (~120 LoC). Used by the modal to gate ESC /
 * Ctrl-Enter handling on whether a modal is open.
 *
 * The active context lives on `<html data-cms-kb-context>` so it
 * survives DOM mutations from other modules (e.g. structureboard's
 * head-swap). Key handlers are registered per-context; the active
 * context's handlers fire on every `keydown`. The default context
 * is `'cms'`.
 */

const DEFAULT_CONTEXT = 'cms';

type Handler = (event: KeyboardEvent) => void;
const contexts: Record<string, Record<string, Handler>> = {
    [DEFAULT_CONTEXT]: {},
};
let lastKey: string | null = null;

function isInputFocused(): boolean {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName.toLowerCase();
    return (
        tag === 'input' ||
        tag === 'textarea' ||
        tag === 'select' ||
        (el as HTMLElement).isContentEditable
    );
}

export function setContext(ctx: string): void {
    document.documentElement.dataset.cmsKbContext = ctx;
}

export function getContext(): string {
    return document.documentElement.dataset.cmsKbContext ?? DEFAULT_CONTEXT;
}

export function bind(
    key: string | string[],
    callback: Handler,
    ctx: string | null = null,
): void {
    if (Array.isArray(key)) {
        key.forEach((k) => bind(k, callback, ctx));
        return;
    }
    const context = ctx ?? getContext();
    if (!contexts[context]) contexts[context] = {};
    contexts[context]![key] = callback;
}

export function unbind(
    key: string | string[],
    ctx: string | null = null,
): void {
    if (Array.isArray(key)) {
        key.forEach((k) => unbind(k, ctx));
        return;
    }
    const context = ctx ?? getContext();
    if (contexts[context]) delete contexts[context]![key];
}

function toKeyCode(event: KeyboardEvent): string {
    const isLetter =
        /^Key[a-zA-Z]$/.test(event.code) ||
        event.code === 'Space' ||
        event.code === 'Enter';
    let key = /^Key[a-zA-Z]$/.test(event.code)
        ? event.code.slice(-1)
        : event.key;
    if (event.code === 'Space') key = 'space';
    if (isLetter) {
        if (event.altKey) key = `alt+${key}`;
        if (event.ctrlKey) key = `ctrl+${key}`;
        if (event.shiftKey) key = `shift+${key}`;
    }
    return key.toLowerCase();
}

function handleKeydown(event: KeyboardEvent): void {
    if (isInputFocused()) return;
    const context = contexts[getContext()];
    const key = toKeyCode(event);
    if (context) {
        if (context[key]) {
            context[key](event);
        } else if (lastKey) {
            const combo = `${lastKey} > ${key}`;
            if (context[combo]) context[combo](event);
        }
    }
    lastKey = null;
}

function handleKeyup(event: KeyboardEvent): void {
    if (isInputFocused()) return;
    lastKey = toKeyCode(event);
}

window.addEventListener('keydown', handleKeydown);
window.addEventListener('keyup', handleKeyup);

const keyboard = {
    setContext,
    getContext,
    bind,
    unbind,
};

export default keyboard;

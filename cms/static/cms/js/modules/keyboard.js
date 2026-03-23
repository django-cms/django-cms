// Minimal Keyboard-Modul mit Kontext und Event-Registrierung

/* global KeyboardEvent */
const DEFAULT_CONTEXT = 'cms';
const contexts = {
    DEFAULT_CONTEXT: {}
};
let lastKey = null;

function isInputFocused() {
    const activeElement = document.activeElement;

    if (!activeElement) {
        return false;
    }
    const tagName = activeElement.tagName.toLowerCase();

    return tagName === 'input' || tagName === 'textarea' || tagName === 'select' || activeElement.isContentEditable;
}

function setContext(ctx) {
    document.documentElement.dataset.cmsKbContext = ctx;
}

function getContext() {
    return document.documentElement.dataset.cmsKbContext || DEFAULT_CONTEXT;
}

function bind(key, callback, ctx = null) {
    if (Array.isArray(key)) {
        key.forEach(k => bind(k, callback, ctx));
        return;
    }
    const context = ctx || getContext();

    if (!contexts[context]) {
        contexts[context] = {};
    }
    contexts[context][key] = callback;
}

function unbind(key, ctx = null) {
    if (Array.isArray(key)) {
        key.forEach(k => unbind(k, ctx));
        return;
    }
    const context = ctx || getContext();

    if (contexts[context]) {
        delete contexts[context][key];
    }
}

function toKeyCode(event) {
    const isLetter = /^Key[a-zA-Z]$/.test(event.code) || event.code === 'Space' || event.code === 'Enter';
    let key = /^Key[a-zA-Z]$/.test(event.code) ? event.code.slice(-1) : event.key;

    if (event.code === 'Space') {
        key = 'space';
    }
    if (isLetter) {
        if (event.altKey) {
            key = `alt+${key}`;
        }
        if (event.ctrlKey) {
            key = `ctrl+${key}`;
        }
        if (event.shiftKey) {
            key = `shift+${key}`;
        }
    }
    return key.toLowerCase();
}

function handleKeydown(event) {
    if (isInputFocused()) {
        return;
    }
    const context = contexts[getContext()];
    const key = toKeyCode(event);

    if (context) {
        if (context[key]) {
            context[key](event);
        } else if (lastKey) {
            const comboKey = `${lastKey} > ${key}`;

            if (context[comboKey]) {
                context[comboKey](event);
            }
        }
    }
    lastKey = null;
}

function handleKeyup(event) {
    if (isInputFocused()) {
        return;
    }
    lastKey = toKeyCode(event);
}

function pressKey(key) {
    const event = new KeyboardEvent('keydown', { key });

    handleKeydown(event);
}

window.addEventListener('keydown', handleKeydown);
window.addEventListener('keyup', handleKeyup);

const keyboard = {
    setContext,
    getContext,
    bind,
    unbind,
    pressKey
};

export default keyboard;

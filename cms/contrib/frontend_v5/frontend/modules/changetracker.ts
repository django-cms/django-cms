/*
 * Form change tracker — watches form fields inside an iframe modal
 * and reports whether the user has unsaved edits. Mirrors legacy
 * `cms.changetracker.js`.
 *
 * The reason there's an actual tracking implementation (rather than a
 * single value-vs-defaultValue pass at submit time) is that browsers
 * don't reliably populate `defaultValue` after a form has been
 * round-tripped — so we capture the original on first interaction.
 *
 * Public surface (read by cms.modal):
 *
 *   class ChangeTracker {
 *       constructor(iframe: HTMLIFrameElement)
 *       isFormChanged(): boolean
 *   }
 *
 * Quirks preserved from the legacy implementation:
 *   - When a tracked field is changed back to its original value,
 *     `formChanged` is reset to `false` regardless of whether OTHER
 *     fields are still dirty. This is a known shortcut in the legacy
 *     code; consumers (cms.modal) only call `isFormChanged()` when
 *     deciding whether to show a "discard?" prompt, so the false
 *     negative is rare in practice.
 *   - Multi-select fields always look dirty after the first
 *     interaction because the value is a fresh array each time and
 *     `=== ` never matches. Same as legacy.
 */

interface FieldState {
    originalValue: unknown;
    editedValue: unknown;
}

interface CkEditorInstance {
    checkDirty?: () => boolean;
}

interface CkEditorWindow extends Window {
    CKEDITOR?: { instances?: Record<string, CkEditorInstance> };
}

export class ChangeTracker {
    private readonly iframe: HTMLIFrameElement;
    private readonly fields: Map<Element, FieldState> = new Map();
    private formChanged = false;
    private cleanups: Array<() => void> = [];

    constructor(iframe: HTMLIFrameElement) {
        this.iframe = iframe;
        this.bindFieldListeners();
    }

    /** True if any tracked field, or any CKEditor instance, is dirty. */
    isFormChanged(): boolean {
        return this.formChanged || this.isEditorChanged();
    }

    /** Release every listener bound by the constructor. */
    destroy(): void {
        for (const cleanup of this.cleanups) cleanup();
        this.cleanups = [];
        this.fields.clear();
    }

    // ────────────────────────────────────────────────────────────

    private bindFieldListeners(): void {
        let doc: Document | null = null;
        try {
            doc = this.iframe.contentDocument;
        } catch {
            // Cross-origin iframe — silently give up. The legacy
            // module catches the same case.
            return;
        }
        if (!doc) return;

        const form = doc.querySelector('.change-form form');
        if (!form) return;

        const elements = form.querySelectorAll<HTMLElement>(
            'input, textarea, select',
        );
        const handler = (e: Event): void => this.trackChange(e);
        for (const el of Array.from(elements)) {
            el.addEventListener('change', handler);
            el.addEventListener('keydown', handler);
            this.cleanups.push(() => {
                el.removeEventListener('change', handler);
                el.removeEventListener('keydown', handler);
            });
        }
    }

    private trackChange(e: Event): void {
        const target = e.target as Element | null;
        if (!target) return;

        const existing = this.fields.get(target);
        if (existing) {
            const newValue = this.getValue(target);
            if (existing.originalValue === newValue) {
                this.formChanged = false;
            }
            this.fields.set(target, {
                originalValue: existing.originalValue,
                editedValue: newValue,
            });
            return;
        }

        const original = this.getOriginalValue(target);
        const edited = this.getValue(target);
        this.fields.set(target, {
            originalValue: original,
            editedValue: edited,
        });
        if (original !== edited) {
            this.formChanged = true;
        }
    }

    private getValue(target: Element): unknown {
        // Use tagName + duck-typing rather than `instanceof`. The iframe
        // has its own window with its own HTMLInputElement constructor;
        // cross-realm `instanceof` returns false.
        const tag = target.tagName;
        if (tag === 'INPUT') {
            const input = target as HTMLInputElement;
            if (input.type === 'checkbox' || input.type === 'radio') {
                return input.checked;
            }
            return input.value;
        }
        if (tag === 'SELECT') {
            const select = target as HTMLSelectElement;
            if (select.multiple) {
                return Array.from(select.selectedOptions).map((o) => o.value);
            }
            return select.value;
        }
        if (tag === 'TEXTAREA') {
            return (target as HTMLTextAreaElement).value;
        }
        return undefined;
    }

    private getOriginalValue(target: Element): unknown {
        const tag = target.tagName;
        if (tag === 'INPUT') {
            const input = target as HTMLInputElement;
            if (input.type === 'checkbox' || input.type === 'radio') {
                return input.defaultChecked;
            }
            return input.defaultValue;
        }
        if (tag === 'SELECT') {
            const select = target as HTMLSelectElement;
            const options = Array.from(select.options);
            if (select.multiple) {
                return options
                    .filter((o) => o.defaultSelected)
                    .map((o) => o.value);
            }
            // Legacy single-select picks the LAST defaultSelected option
            // (it iterates and overwrites). Match that.
            let value: string | undefined;
            for (const o of options) {
                if (o.defaultSelected) value = o.value;
            }
            return value;
        }
        if (tag === 'TEXTAREA') {
            return (target as HTMLTextAreaElement).defaultValue;
        }
        return undefined;
    }

    private isEditorChanged(): boolean {
        let win: Window | null = null;
        try {
            win = this.iframe.contentWindow;
        } catch {
            return false;
        }
        if (!win) return false;

        const ck = (win as CkEditorWindow).CKEDITOR;
        if (!ck?.instances) return false;
        return Object.keys(ck.instances).some((key) =>
            Boolean(ck.instances?.[key]?.checkDirty?.()),
        );
    }
}

export default ChangeTracker;

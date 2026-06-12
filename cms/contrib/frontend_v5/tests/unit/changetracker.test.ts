import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ChangeTracker } from '../../frontend/modules/changetracker';

const liveTrackers: ChangeTracker[] = [];
function track(t: ChangeTracker): ChangeTracker {
    liveTrackers.push(t);
    return t;
}

function makeIframe(html: string): HTMLIFrameElement {
    const iframe = document.createElement('iframe');
    document.body.appendChild(iframe);
    const doc = iframe.contentDocument!;
    doc.open();
    doc.write(html);
    doc.close();
    return iframe;
}

function changeForm(body: string): string {
    return `<!doctype html><html><body>
        <div class="change-form">
            <form>${body}</form>
        </div>
    </body></html>`;
}

afterEach(() => {
    while (liveTrackers.length > 0) liveTrackers.pop()!.destroy();
    document.body.innerHTML = '';
});

describe('ChangeTracker — text inputs', () => {
    it('starts clean', () => {
        const iframe = makeIframe(
            changeForm('<input name="x" value="hello" />'),
        );
        const t = track(new ChangeTracker(iframe));
        expect(t.isFormChanged()).toBe(false);
    });

    it('marks dirty when input value changes from default', () => {
        const iframe = makeIframe(
            changeForm('<input name="x" value="hello" />'),
        );
        const t = track(new ChangeTracker(iframe));
        const input =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        input.value = 'world';
        input.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
    });

    it('stays clean when typed value matches default', () => {
        const iframe = makeIframe(
            changeForm('<input name="x" value="hello" />'),
        );
        const t = track(new ChangeTracker(iframe));
        const input =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        // Same value as default — no change.
        input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
        expect(t.isFormChanged()).toBe(false);
    });

    it('resets to clean when value reverts to default', () => {
        const iframe = makeIframe(
            changeForm('<input name="x" value="hello" />'),
        );
        const t = track(new ChangeTracker(iframe));
        const input =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        input.value = 'world';
        input.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
        input.value = 'hello';
        input.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(false);
    });
});

describe('ChangeTracker — checkboxes', () => {
    it('marks dirty when checkbox toggles', () => {
        const iframe = makeIframe(
            changeForm('<input type="checkbox" name="x" />'),
        );
        const t = track(new ChangeTracker(iframe));
        const cb =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        cb.checked = true;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
    });

    it('clean when checkbox returns to default state', () => {
        const iframe = makeIframe(
            changeForm('<input type="checkbox" name="x" checked />'),
        );
        const t = track(new ChangeTracker(iframe));
        const cb =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        cb.checked = false;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
        cb.checked = true;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(false);
    });
});

describe('ChangeTracker — selects', () => {
    it('detects single-select change', () => {
        const iframe = makeIframe(
            changeForm(
                '<select name="x"><option value="a" selected>a</option><option value="b">b</option></select>',
            ),
        );
        const t = track(new ChangeTracker(iframe));
        const select =
            iframe.contentDocument!.querySelector<HTMLSelectElement>(
                'select',
            )!;
        select.value = 'b';
        select.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
    });

    it('multi-select always marks dirty on first interaction', () => {
        // Preserved legacy quirk: array reference comparison.
        const iframe = makeIframe(
            changeForm(
                '<select name="x" multiple><option value="a" selected>a</option><option value="b">b</option></select>',
            ),
        );
        const t = track(new ChangeTracker(iframe));
        const select =
            iframe.contentDocument!.querySelector<HTMLSelectElement>(
                'select',
            )!;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
    });
});

describe('ChangeTracker — textarea', () => {
    it('detects textarea edit', () => {
        const iframe = makeIframe(
            changeForm('<textarea name="x">hi</textarea>'),
        );
        const t = track(new ChangeTracker(iframe));
        const ta =
            iframe.contentDocument!.querySelector<HTMLTextAreaElement>(
                'textarea',
            )!;
        ta.value = 'changed';
        ta.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(true);
    });
});

describe('ChangeTracker — CKEditor integration', () => {
    it('reports dirty when any CKEditor instance is dirty', () => {
        const iframe = makeIframe(changeForm('<input name="x" value="a" />'));
        const t = track(new ChangeTracker(iframe));
        // Inject a fake CKEDITOR onto the iframe's contentWindow.
        (iframe.contentWindow as unknown as { CKEDITOR: unknown }).CKEDITOR = {
            instances: {
                editor1: { checkDirty: () => true },
                editor2: { checkDirty: () => false },
            },
        };
        expect(t.isFormChanged()).toBe(true);
    });

    it('reports clean when all CKEditor instances are clean', () => {
        const iframe = makeIframe(changeForm('<input name="x" value="a" />'));
        const t = track(new ChangeTracker(iframe));
        (iframe.contentWindow as unknown as { CKEDITOR: unknown }).CKEDITOR = {
            instances: {
                editor1: { checkDirty: () => false },
            },
        };
        expect(t.isFormChanged()).toBe(false);
    });

    it('tolerates missing CKEDITOR global', () => {
        const iframe = makeIframe(changeForm('<input name="x" value="a" />'));
        const t = track(new ChangeTracker(iframe));
        expect(t.isFormChanged()).toBe(false);
    });
});

describe('ChangeTracker — resilience', () => {
    it('does not throw when iframe has no document', () => {
        const iframe = document.createElement('iframe');
        // Not appended to body — contentDocument may still exist as
        // about:blank, but no .change-form will be present.
        expect(() => track(new ChangeTracker(iframe))).not.toThrow();
    });

    it('does not throw when there is no .change-form', () => {
        const iframe = makeIframe('<!doctype html><html><body></body></html>');
        const t = track(new ChangeTracker(iframe));
        expect(t.isFormChanged()).toBe(false);
    });

    it('destroy() releases listeners — further events do not mutate state', () => {
        const iframe = makeIframe(
            changeForm('<input name="x" value="hello" />'),
        );
        const t = track(new ChangeTracker(iframe));
        const input =
            iframe.contentDocument!.querySelector<HTMLInputElement>('input')!;
        t.destroy();
        input.value = 'world';
        input.dispatchEvent(new Event('change', { bubbles: true }));
        expect(t.isFormChanged()).toBe(false);
    });
});

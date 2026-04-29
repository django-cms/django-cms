import { describe, expect, it } from 'vitest';
import {
    elementPresent,
    extractMessages,
    getPluginDataFromMarkup,
} from '../../frontend/modules/structureboard/parsers/markup';

function parseHtml(html: string): Document {
    return new DOMParser().parseFromString(html, 'text/html');
}

describe('parsers/markup — getPluginDataFromMarkup', () => {
    it('reads each <script id="cms-plugin-{id}"> JSON blob', () => {
        const doc = parseHtml(`
            <script type="application/json" id="cms-plugin-1">
                {"type":"plugin","plugin_id":1,"plugin_type":"TextPlugin"}
            </script>
            <script type="application/json" id="cms-plugin-2">
                {"type":"plugin","plugin_id":2,"plugin_type":"PicturePlugin"}
            </script>
        `);
        const data = getPluginDataFromMarkup(doc, [1, 2]);
        expect(data).toEqual([
            { type: 'plugin', plugin_id: 1, plugin_type: 'TextPlugin' },
            { type: 'plugin', plugin_id: 2, plugin_type: 'PicturePlugin' },
        ]);
    });

    it('drops missing ids silently', () => {
        const doc = parseHtml(`
            <script type="application/json" id="cms-plugin-1">{"type":"plugin","plugin_id":1}</script>
        `);
        const data = getPluginDataFromMarkup(doc, [1, 99]);
        expect(data).toHaveLength(1);
        expect(data[0]?.plugin_id).toBe(1);
    });

    it('drops malformed JSON silently', () => {
        const doc = parseHtml(`
            <script type="application/json" id="cms-plugin-1">not-valid</script>
            <script type="application/json" id="cms-plugin-2">{"type":"plugin","plugin_id":2}</script>
        `);
        const data = getPluginDataFromMarkup(doc, [1, 2]);
        expect(data).toHaveLength(1);
        expect(data[0]?.plugin_id).toBe(2);
    });

    it('returns [] when none of the requested ids match', () => {
        const doc = parseHtml('<div></div>');
        expect(getPluginDataFromMarkup(doc, [1, 2, 3])).toEqual([]);
    });
});

describe('parsers/markup — elementPresent', () => {
    it('returns true when an outerHTML match exists', () => {
        const a = document.createElement('script');
        a.setAttribute('src', 'foo.js');
        const b = document.createElement('script');
        b.setAttribute('src', 'foo.js');
        expect(elementPresent([a], b)).toBe(true);
    });

    it('returns false on attribute mismatch', () => {
        const a = document.createElement('script');
        a.setAttribute('src', 'foo.js');
        const b = document.createElement('script');
        b.setAttribute('src', 'bar.js');
        expect(elementPresent([a], b)).toBe(false);
    });

    it('returns false on empty current set', () => {
        const b = document.createElement('script');
        expect(elementPresent([], b)).toBe(false);
    });
});

describe('parsers/markup — extractMessages', () => {
    it('reads .messagelist > li (legacy admin shape)', () => {
        const doc = parseHtml(`
            <ul class="messagelist">
                <li>Saved</li>
                <li class="error">Bad input</li>
            </ul>
        `);
        const messages = extractMessages(doc);
        expect(messages).toEqual([
            { message: 'Saved', error: false },
            { message: 'Bad input', error: true },
        ]);
    });

    it('reads [data-cms-messages-container] > [data-cms-message] when messagelist absent', () => {
        const doc = parseHtml(`
            <div data-cms-messages-container>
                <div data-cms-message>OK</div>
                <div data-cms-message data-cms-message-tags="error">Boom</div>
            </div>
        `);
        const messages = extractMessages(doc);
        expect(messages).toEqual([
            { message: 'OK', error: false },
            { message: 'Boom', error: true },
        ]);
    });

    it('skips empty messages', () => {
        const doc = parseHtml(`
            <ul class="messagelist">
                <li></li>
                <li>real</li>
            </ul>
        `);
        const messages = extractMessages(doc);
        expect(messages).toEqual([{ message: 'real', error: false }]);
    });

    it('returns [] when no messagelist present', () => {
        const doc = parseHtml('<div>Hi</div>');
        expect(extractMessages(doc)).toEqual([]);
    });
});

import { afterEach, describe, expect, it } from 'vitest';
import { renderBreadcrumbs } from '../../frontend/modules/modal/breadcrumb';

afterEach(() => {
    document.body.innerHTML = '';
});

function makeContainer(): HTMLElement {
    const div = document.createElement('div');
    document.body.appendChild(div);
    return div;
}

describe('renderBreadcrumbs', () => {
    it('returns false and clears the container with no crumbs', () => {
        const c = makeContainer();
        c.innerHTML = '<a>stale</a>';
        expect(renderBreadcrumbs(c, [])).toBe(false);
        expect(c.innerHTML).toBe('');
    });

    it('returns false for a single-level crumb (no "trail" to render)', () => {
        const c = makeContainer();
        expect(
            renderBreadcrumbs(c, [{ title: 'Only', url: '/x/' }]),
        ).toBe(false);
    });

    it('returns false when first crumb has no title', () => {
        const c = makeContainer();
        expect(
            renderBreadcrumbs(c, [
                { title: '', url: '/' },
                { title: 'X', url: '/x/' },
            ]),
        ).toBe(false);
    });

    it('renders crumbs with the last marked active', () => {
        const c = makeContainer();
        const ok = renderBreadcrumbs(c, [
            { title: 'Root', url: '/' },
            { title: 'Sub', url: '/sub/' },
            { title: 'Leaf', url: '/sub/leaf/' },
        ]);
        expect(ok).toBe(true);
        const anchors = c.querySelectorAll('a');
        expect(anchors.length).toBe(3);
        expect(anchors[0]!.classList.contains('active')).toBe(false);
        expect(anchors[2]!.classList.contains('active')).toBe(true);
        expect(anchors[1]!.querySelector('span')?.textContent).toBe('Sub');
    });
});

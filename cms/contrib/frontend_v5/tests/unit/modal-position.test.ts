import { describe, expect, it } from 'vitest';
import { calculatePosition } from '../../frontend/modules/modal/position';

describe('calculatePosition', () => {
    it('uses screen size minus 300px offset when modal fits', () => {
        const result = calculatePosition({
            currentLeft: '50%',
            currentTop: '50%',
            screenWidth: 1920,
            screenHeight: 1080,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.width).toBe(1920 - 300);
        expect(result.height).toBe(1080 - 300);
        expect(result.triggerMaximized).toBe(false);
    });

    it('uses minWidth when screen is too narrow', () => {
        const result = calculatePosition({
            currentLeft: '50%',
            currentTop: '50%',
            screenWidth: 600,
            screenHeight: 1080,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.width).toBe(800);
        expect(result.triggerMaximized).toBe(true);
    });

    it('uses requested width when provided', () => {
        const result = calculatePosition({
            currentLeft: '50%',
            currentTop: '50%',
            screenWidth: 1920,
            screenHeight: 1080,
            requestedWidth: 500,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.width).toBe(500);
    });

    it('recenters when current position would push modal off-screen', () => {
        const result = calculatePosition({
            currentLeft: '5',
            currentTop: '5',
            screenWidth: 1920,
            screenHeight: 1080,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.left).toBe(1920 / 2);
        expect(result.top).toBe(1080 / 2);
    });

    it('does not recenter when current position is in-bounds', () => {
        const result = calculatePosition({
            currentLeft: '50%',
            currentTop: '50%',
            screenWidth: 1920,
            screenHeight: 1080,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.left).toBeUndefined();
        expect(result.top).toBeUndefined();
    });

    it('triggerMaximized when modal exceeds viewport', () => {
        const result = calculatePosition({
            currentLeft: '50%',
            currentTop: '50%',
            screenWidth: 100,
            screenHeight: 100,
            minWidth: 800,
            minHeight: 400,
        });
        expect(result.triggerMaximized).toBe(true);
    });
});

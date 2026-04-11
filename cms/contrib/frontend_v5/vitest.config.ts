import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    root: here,
    resolve: {
        alias: {
            '@': resolve(here, 'frontend'),
        },
    },
    test: {
        environment: 'jsdom',
        globals: true,
        include: ['tests/unit/**/*.test.ts'],
        coverage: {
            provider: 'v8',
            include: ['frontend/**/*.ts'],
            reporter: ['text', 'lcov'],
        },
    },
});

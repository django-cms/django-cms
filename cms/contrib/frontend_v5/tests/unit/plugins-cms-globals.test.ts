import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    getCmsConfig,
    getCmsLocked,
    getCmsNamespace,
    getCmsSettings,
    getClipboard,
    getInstancesRegistry,
    getMessages,
    getModalConstructor,
    getPluginsRegistry,
    getStructureBoard,
    getTooltip,
    isContentReady,
    isStructureReady,
    setCmsLocked,
} from '../../frontend/modules/plugins/cms-globals';

describe('cms-globals — defensive accessors', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('getCmsNamespace returns undefined when CMS is absent', () => {
        expect(getCmsNamespace()).toBeUndefined();
    });

    it('getCmsConfig returns an empty object when CMS or config are missing', () => {
        expect(getCmsConfig()).toEqual({});
        window.CMS = {} as CmsGlobal;
        expect(getCmsConfig()).toEqual({});
    });

    it('getCmsConfig returns the live config when present', () => {
        window.CMS = { config: { csrf: 'tok', settings: { mode: 'structure' } } } as CmsGlobal;
        expect(getCmsConfig().csrf).toBe('tok');
        expect(getCmsConfig().settings?.mode).toBe('structure');
    });

    it('getCmsSettings auto-creates settings on the namespace', () => {
        window.CMS = {} as CmsGlobal;
        const settings = getCmsSettings();
        expect(settings).toEqual({});
        // Same reference on second read.
        expect(getCmsSettings()).toBe(settings);
        expect(window.CMS.settings).toBe(settings);
    });

    it('getCmsSettings returns {} when CMS itself is absent', () => {
        expect(getCmsSettings()).toEqual({});
    });

    it('getCmsLocked / setCmsLocked round-trip via CMS.API.locked', () => {
        window.CMS = {} as CmsGlobal;
        expect(getCmsLocked()).toBe(false);
        setCmsLocked(true);
        expect(window.CMS.API?.locked).toBe(true);
        expect(getCmsLocked()).toBe(true);
        setCmsLocked(false);
        expect(getCmsLocked()).toBe(false);
    });

    it('setCmsLocked auto-creates CMS.API when missing', () => {
        // Start with no CMS namespace at all — setCmsLocked must
        // still succeed and not throw.
        setCmsLocked(true);
        expect(window.CMS?.API?.locked).toBe(true);
    });
});

describe('cms-globals — legacy API accessors return undefined when absent', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('returns undefined for every API surface when CMS is missing', () => {
        expect(getStructureBoard()).toBeUndefined();
        expect(getMessages()).toBeUndefined();
        expect(getTooltip()).toBeUndefined();
        expect(getClipboard()).toBeUndefined();
        expect(getModalConstructor()).toBeUndefined();
    });

    it('returns the API surface when present', () => {
        const StructureBoard = { invalidateState: () => undefined };
        const Messages = { open: () => undefined };
        const Tooltip = { displayToggle: () => undefined };
        const Clipboard = { populate: () => undefined };
        const Modal = function FakeModal() {} as unknown;
        window.CMS = {
            API: { StructureBoard, Messages, Tooltip, Clipboard },
            Modal,
        } as unknown as CmsGlobal;
        expect(getStructureBoard()).toBe(StructureBoard);
        expect(getMessages()).toBe(Messages);
        expect(getTooltip()).toBe(Tooltip);
        expect(getClipboard()).toBe(Clipboard);
        expect(getModalConstructor()).toBe(Modal);
    });
});

describe('cms-globals — plugin registries', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('getInstancesRegistry creates the array on first read', () => {
        const reg = getInstancesRegistry();
        expect(Array.isArray(reg)).toBe(true);
        expect(reg).toHaveLength(0);
        expect((window.CMS as unknown as { _instances: unknown })._instances).toBe(reg);
    });

    it('getInstancesRegistry returns the same reference across calls (mutation visible)', () => {
        const reg = getInstancesRegistry();
        const fakeInstance = { options: { type: 'plugin', plugin_id: 1 } };
        reg.push(fakeInstance);
        expect(getInstancesRegistry()).toHaveLength(1);
        expect(getInstancesRegistry()[0]).toBe(fakeInstance);
    });

    it('getPluginsRegistry creates the descriptor array on first read', () => {
        const descriptors = getPluginsRegistry();
        expect(descriptors).toEqual([]);
        descriptors.push(['cms-plugin-1', { type: 'plugin', plugin_id: 1 }]);
        expect(getPluginsRegistry()).toHaveLength(1);
    });
});

describe('cms-globals — isStructureReady / isContentReady', () => {
    afterEach(() => {
        delete (window as { CMS?: CmsGlobal }).CMS;
    });

    it('isStructureReady true when config.settings.mode is "structure"', () => {
        window.CMS = { config: { settings: { mode: 'structure' } } } as CmsGlobal;
        expect(isStructureReady()).toBe(true);
        expect(isContentReady()).toBe(false);
    });

    it('isContentReady true when config.settings.mode is not "structure"', () => {
        window.CMS = { config: { settings: { mode: 'content' } } } as CmsGlobal;
        expect(isContentReady()).toBe(true);
        expect(isStructureReady()).toBe(false);
    });

    it('legacy_mode flips both predicates true', () => {
        window.CMS = { config: { settings: { legacy_mode: true } } } as CmsGlobal;
        expect(isStructureReady()).toBe(true);
        expect(isContentReady()).toBe(true);
    });

    it('isStructureReady falls back to StructureBoard._loadedStructure when mode != "structure"', () => {
        window.CMS = {
            config: { settings: { mode: 'content' } },
            API: { StructureBoard: { _loadedStructure: true } },
        } as unknown as CmsGlobal;
        expect(isStructureReady()).toBe(true);
    });

    it('isContentReady falls back to StructureBoard._loadedContent when mode == "structure"', () => {
        window.CMS = {
            config: { settings: { mode: 'structure' } },
            API: { StructureBoard: { _loadedContent: true } },
        } as unknown as CmsGlobal;
        expect(isContentReady()).toBe(true);
    });

    it('returns false when nothing signals ready', () => {
        window.CMS = { config: { settings: { mode: 'structure' } } } as CmsGlobal;
        expect(isContentReady()).toBe(false);
        window.CMS = { config: { settings: { mode: 'content' } } } as CmsGlobal;
        expect(isStructureReady()).toBe(false);
    });
});

describe('cms.base.js', () => {
    it('creates CMS namespace', () => {
        expect(CMS).toBeDefined();
        expect(CMS).toEqual(jasmine.any(Object));
        expect(CMS.API).toEqual(jasmine.any(Object));
        expect(CMS.KEYS).toEqual(jasmine.any(Object));
        expect(CMS.BREAKPOINTS).toEqual(jasmine.any(Object));
    });
});

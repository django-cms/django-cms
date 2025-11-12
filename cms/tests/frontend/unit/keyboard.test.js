
import keyboard from '../../../static/cms/js/modules/keyboard';

describe('keyboard', () => {
    it('works as usual', () => {
        const callback = jasmine.createSpy();

        keyboard.bind('1', callback);
        keyboard.pressKey('1');
        expect(callback).toHaveBeenCalledTimes(1);
    });

    it('modifies callback execution to stop when inputs are focused', () => {
        const callback = jasmine.createSpy();

        keyboard.bind('1', callback);

        // Create and focus an input element
        const input = document.createElement('input');
        document.body.appendChild(input);
        input.focus();

        keyboard.pressKey('1');
        expect(callback).not.toHaveBeenCalled();

        // Cleanup
        document.body.removeChild(input);
    });
});

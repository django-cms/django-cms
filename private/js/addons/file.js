import $ from 'jquery';

export function initFileInputs(selector = '.js-file') {
    const files = $(selector);

    files.each((i, el) => {
        const fileWidget = $(el);
        const fileInput = fileWidget.find('input[type=file]');
        const fileLabel = fileWidget.find('.custom-file-control');

        fileInput.on('change', function () {
            let value = this.value.replace('C:\\fakepath\\', '');

            if (this.files && this.files.length) {
                value = Array.prototype.slice.call(this.files).map((f) => f.name).join(', ');
            }

            fileLabel.text(value);
        });
    });
}

// #DROPZONE#
// This script implements the dropzone settings
'use strict';

/* globals Dropzone */
(function ($) {
    $(function () {
        var dropzoneSelector = '.js-filer-dropzone';
        var dropzones;
        var infoMessage = '.js-filer-dropzone-info-message';
        var errorMessage = '.js-filer-dropzone-error-message';
        var uploadInfo = '.js-filer-dropzone-upload-info';
        var uploadWelcome = '.js-filer-dropzone-upload-welcome';
        var uploadFileName = '.js-filer-dropzone-file-name';
        var uploadProgress = '.js-filer-dropzone-progress';
        var uploadSuccess = '.js-filer-dropzone-upload-success';
        var dragHoverClass = 'dz-drag-hover';
        var originalImage = '.js-original-image';
        var hideMessageTimeout;
        var errorMessageTimeout = 2;

        dropzones = $(dropzoneSelector);
        if (dropzones.length && Dropzone) {
            Dropzone.autoDiscover = false;
            dropzones.each(function () {
                var dropzone = $(this);
                var dropzoneUrl = $(this).data('filer-url');
                new Dropzone(this, {
                    url: dropzoneUrl,
                    paramName: 'file',
                    uploadMultiple: false,
                    previewTemplate: '<div></div>',
                    clickable: false,
                    addRemoveLinks: false,
                    accept: function (file, done) {
                        if (!file.type.match('image.*')) {
                            dropzone.find(errorMessage).show();
                            clearTimeout(hideMessageTimeout);
                            hideMessageTimeout = setTimeout(function () {
                                dropzone.find(errorMessage).hide();
                            }, errorMessageTimeout * 1000);
                            done('Error')
                        } else {
                            dropzone.find(errorMessage).hide();
                            done();
                        }
                    },
                    maxfilesexceeded: function (file) {
                        this.removeAllFiles();
                        this.addFile(file);
                    },
                    dragover: function () {
                        dropzone.find(uploadSuccess).hide();
                        dropzone.find(infoMessage).show();
                        dropzone.addClass(dragHoverClass);
                    },
                    dragleave: function () {
                        clearTimeout(hideMessageTimeout);
                        hideMessageTimeout = setTimeout(function () {
                            dropzone.find(infoMessage).hide();
                        }, 100);

                        dropzone.find(infoMessage).show();
                        dropzone.removeClass(dragHoverClass);
                    },
                    drop: function () {
                        clearTimeout(hideMessageTimeout);
                        dropzone.find(infoMessage).show();
                        dropzone.removeClass(dragHoverClass);
                    },
                    sending: function (file) {
                        dropzone.find(uploadWelcome).hide();
                        dropzone.find(uploadFileName).text(file.name);
                        dropzone.find(uploadProgress).width(0);
                        dropzone.find(uploadInfo).show();
                    },
                    uploadprogress: function (file, progress) {
                        dropzone.find(uploadProgress).width(progress + '%');
                    },
                    success: function (file, response) {
                        dropzone.find(uploadInfo).hide();
                        dropzone.find(uploadSuccess).show();
                        if (file && file.status === 'success' && response) {
                            if (response.original_image) {
                                dropzone.find(originalImage).attr('src', response.original_image)
                                // TODO this should be CMS.API call
                                // FIXME only works on 3.2
                                $('.cms-btn-publish').addClass('cms-btn-publish-active')
                                    .removeClass('cms-btn-disabled')
                                    .parent().show();
                                $('.cms-toolbar-revert').removeClass('cms-toolbar-item-navigation-disabled');
                                $(window).trigger('resize');
                            }
                        }
                    },
                    queuecomplete: function () {
                        dropzone.find(infoMessage).hide();
                        dropzone.find(uploadSuccess).hide();
                        dropzone.find(uploadWelcome).show();
                    }
                });
            });
        }
    });
})(jQuery);

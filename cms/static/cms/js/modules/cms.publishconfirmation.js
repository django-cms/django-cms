/*
 * Copyright https://github.com/divio/django-cms
 */

import $ from 'jquery';
import Modal from './cms.modal';
import { showLoader, hideLoader } from './loader';
import { Helpers } from './cms.base';

/**
 * Publish confirmation dialog for pages with descendant selection.
 *
 * @class PublishConfirmation
 * @namespace CMS
 */
class PublishConfirmation {
    constructor(options) {
        this.options = $.extend(true, {}, {
            publishBtnSelector: '.cms-btn-publish, .cms-publish-page, [data-action="publish"]',
            confirmTemplate: null,
            apiUrl: null,
            pageId: null,
            pageContentId: null,
            language: null,
        }, options);

        this.click = 'click.cms.publishconfirmation';
        this._setupUI();
        this._events();
    }

    /**
     * @method _setupUI
     * @private
     */
    _setupUI() {
        this.ui = {
            document: $(document),
            window: $(window),
            body: $('html'),
        };
    }

    /**
     * @method _events
     * @private
     */
    _events() {
        var that = this;

        this.ui.document.on(this.click, this.options.publishBtnSelector, function(e) {
            var btn = $(this);
            
            if (btn.hasClass('cms-btn-disabled')) {
                return false;
            }

            e.preventDefault();
            e.stopImmediatePropagation();
            
            that._handlePublishClick(btn);
        });
    }

    /**
     * Handle publish button click
     * @method _handlePublishClick
     * @private
     * @param {jQuery} btn The publish button element
     */
    _handlePublishClick(btn) {
        var that = this;
        var pageInfo = this._extractPageInfo(btn);
        
        if (!pageInfo.pageId && !pageInfo.pageContentId && !pageInfo.apiUrl) {
            this._showError(_('Missing page information for publish confirmation'));
            return;
        }

        var apiUrl = pageInfo.apiUrl || this._buildApiUrl(pageInfo);

        showLoader();
        
        $.ajax({
            url: apiUrl,
            method: 'GET',
            dataType: 'json',
        })
        .done(function(response) {
            hideLoader();
            that._showConfirmationDialog(response, btn);
        })
        .fail(function(jqXHR) {
            hideLoader();
            CMS.API.Messages.open({
                message: jqXHR.responseText + ' | ' + jqXHR.status + ' ' + jqXHR.statusText,
                error: true
            });
        });
    }

    /**
     * Extract page information from button or current context
     * @method _extractPageInfo
     * @private
     * @param {jQuery} btn
     * @returns {Object}
     */
    _extractPageInfo(btn) {
        var pageInfo = {
            pageId: this.options.pageId || btn.data('page-id'),
            pageContentId: this.options.pageContentId || btn.data('page-content-id'),
            apiUrl: this.options.apiUrl || btn.data('api-url'),
            language: this.options.language || btn.data('language'),
        };

        if (!pageInfo.pageId && !pageInfo.pageContentId) {
            var urlInfo = this._extractFromUrl(btn.attr('href'));
            if (urlInfo.pageId) {
                pageInfo.pageId = urlInfo.pageId;
            }
            if (urlInfo.language && !pageInfo.language) {
                pageInfo.language = urlInfo.language;
            }
        }

        if (!pageInfo.pageId && !pageInfo.pageContentId) {
            var currentUrlInfo = this._extractFromUrl(window.location.pathname);
            if (currentUrlInfo.pageId) {
                pageInfo.pageId = currentUrlInfo.pageId;
            }
            if (currentUrlInfo.pageContentId) {
                pageInfo.pageContentId = currentUrlInfo.pageContentId;
            }
            if (currentUrlInfo.language && !pageInfo.language) {
                pageInfo.language = currentUrlInfo.language;
            }
        }

        return pageInfo;
    }

    /**
     * Extract page ID and language from URL
     * URL patterns:
     * - /en/admin/cms/page/33/en/publish/  -> pageId: 33, language: en
     * - /admin/cms/pagecontent/123/change/ -> pageContentId: 123
     * @method _extractFromUrl
     * @private
     * @param {String} url
     * @returns {Object}
     */
    _extractFromUrl(url) {
        var result = {
            pageId: null,
            pageContentId: null,
            language: null,
        };

        if (!url) {
            return result;
        }

        var pageContentMatch = url.match(/\/pagecontent\/(\d+)/);
        if (pageContentMatch) {
            result.pageContentId = parseInt(pageContentMatch[1], 10);
        }

        var pageMatch = url.match(/\/page\/(\d+)/);
        if (pageMatch) {
            result.pageId = parseInt(pageMatch[1], 10);
        }

        var langMatch = url.match(/\/([a-z]{2}(-[a-z]{2})?)\//);
        if (langMatch && langMatch[1].length >= 2) {
            var lang = langMatch[1].toLowerCase();
            if (lang !== 'admin' && lang !== 'cms') {
                result.language = lang;
            }
        }

        return result;
    }

    /**
     * Build API URL from page information
     * @method _buildApiUrl
     * @private
     * @param {Object} pageInfo
     * @returns {String}
     */
    _buildApiUrl(pageInfo) {
        var baseUrl = window.location.pathname;
        var adminMatch = baseUrl.match(/^(.+\/admin\/)/);
        var adminBase = adminMatch ? adminMatch[1] : '/admin/';
        
        var apiUrl;

        if (pageInfo.pageContentId) {
            apiUrl = adminBase + 'cms/pagecontent/' + pageInfo.pageContentId + '/get-descendants-for-publish/';
        } else if (pageInfo.pageId) {
            apiUrl = adminBase + 'cms/page/' + pageInfo.pageId + '/get-descendants-for-publish/';
        } else {
            return null;
        }

        if (pageInfo.language) {
            var separator = apiUrl.indexOf('?') === -1 ? '?' : '&';
            apiUrl += separator + 'language=' + encodeURIComponent(pageInfo.language);
        }

        return apiUrl;
    }

    /**
     * Show confirmation dialog with descendant selection
     * @method _showConfirmationDialog
     * @private
     * @param {Object} data The API response data
     * @param {jQuery} originalBtn The original publish button
     */
    _showConfirmationDialog(data, originalBtn) {
        var that = this;
        var modal = new Modal({
            onClose: function() {
                that._cleanup();
            }
        });

        var dialogHtml = this._renderDialog(data);

        modal.open({
            html: dialogHtml,
            title: _('Publish Confirmation'),
            width: 600,
            height: 500,
        });

        this._bindDialogEvents(modal, data, originalBtn);
    }

    /**
     * Render dialog HTML
     * @method _renderDialog
     * @private
     * @param {Object} data
     * @returns {String}
     */
    _renderDialog(data) {
        var that = this;
        var html = '<div class="cms-publish-confirmation">';
        
        html += '<div class="cms-publish-confirmation-header" style="padding: 20px; border-bottom: 1px solid var(--border-color);">';
        html += '<h3 style="margin: 0 0 10px 0; font-size: 18px;">' + _('Publish Confirmation') + '</h3>';
        html += '<p style="margin: 0;">' + _('Publishing page:') + ' <strong>' + this._escapeHtml(data.page_title) + '</strong></p>';
        html += '</div>';

        if (data.has_descendants && data.descendants && data.descendants.length > 0) {
            html += '<div class="cms-publish-confirmation-descendants" style="padding: 20px; max-height: 300px; overflow-y: auto;">';
            html += '<h4 style="margin: 0 0 15px 0; font-size: 14px;">' + _('Select child pages to publish (optional):') + '</h4>';
            
            html += '<div class="cms-publish-confirmation-select-all" style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color);">';
            html += '<label style="cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">';
            html += '<input type="checkbox" id="id_select_all_descendants" class="js-cms-publish-select-all" style="cursor: pointer;">';
            html += '<span>' + _('Select all') + '</span>';
            html += '</label>';
            html += '</div>';

            html += '<ul class="cms-publish-confirmation-list" style="list-style: none; margin: 0; padding: 0;">';
            
            data.descendants.forEach(function(descendant) {
                var indentStyle = descendant.depth > 1 ? 'padding-left: ' + (descendant.depth * 20) + 'px;' : '';
                var indicatorClass = descendant.indicator ? 'cms-pagetree-node-state cms-pagetree-node-state-' + descendant.indicator : '';
                
                html += '<li class="cms-publish-confirmation-item" style="' + indentStyle + 'margin-bottom: 8px;">';
                html += '<label style="cursor: pointer; display: inline-flex; align-items: center; gap: 8px;">';
                html += '<input type="checkbox" name="descendant_ids" value="' + descendant.id + '" class="js-cms-publish-descendant-checkbox" style="cursor: pointer;" data-indicator="' + (descendant.indicator || '') + '">';
                html += '<span class="cms-publish-confirmation-title" style="flex: 1;">' + that._escapeHtml(descendant.title) + '</span>';
                if (indicatorClass) {
                    html += '<span class="cms-publish-confirmation-indicator ' + indicatorClass + '" style="display: inline-block; width: 12px; height: 12px; border-radius: 50%;"></span>';
                }
                html += '</label>';
                html += '</li>';
            });
            
            html += '</ul>';
            html += '</div>';
        } else {
            html += '<div class="cms-publish-confirmation-no-descendants" style="padding: 40px 20px; text-align: center; color: var(--body-quiet-color);">';
            html += '<p style="margin: 0;">' + _('This page has no child pages.') + '</p>';
            html += '</div>';
        }

        html += '<div class="cms-publish-confirmation-footer" style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; gap: 10px; justify-content: flex-end;">';
        html += '<button type="button" class="cms-btn cms-btn-action js-cms-publish-confirm" style="padding: 8px 16px; cursor: pointer;">' + _('Confirm Publish') + '</button>';
        html += '<button type="button" class="cms-btn js-cms-publish-cancel" style="padding: 8px 16px; cursor: pointer;">' + _('Cancel') + '</button>';
        html += '</div>';

        html += '</div>';
        
        return html;
    }

    /**
     * Bind dialog events
     * @method _bindDialogEvents
     * @private
     * @param {Modal} modal
     * @param {Object} data
     * @param {jQuery} originalBtn
     */
    _bindDialogEvents(modal, data, originalBtn) {
        var that = this;
        var $modal = modal.ui.modal;

        $modal.on(this.click, '.js-cms-publish-select-all', function() {
            var isChecked = $(this).prop('checked');
            $modal.find('.js-cms-publish-descendant-checkbox').prop('checked', isChecked);
        });

        $modal.on(this.click, '.js-cms-publish-descendant-checkbox', function() {
            var allChecked = $modal.find('.js-cms-publish-descendant-checkbox').length === 
                              $modal.find('.js-cms-publish-descendant-checkbox:checked').length;
            $modal.find('.js-cms-publish-select-all').prop('checked', allChecked);
        });

        $modal.on(this.click, '.js-cms-publish-cancel', function() {
            modal.close();
        });

        $modal.on(this.click, '.js-cms-publish-confirm', function() {
            var selectedIds = [];
            $modal.find('.js-cms-publish-descendant-checkbox:checked').each(function() {
                selectedIds.push(parseInt($(this).val(), 10));
            });

            that._executePublish(modal, data, originalBtn, selectedIds);
        });
    }

    /**
     * Execute the actual publish operation
     * @method _executePublish
     * @private
     * @param {Modal} modal
     * @param {Object} data
     * @param {jQuery} originalBtn
     * @param {Array} selectedDescendantIds
     */
    _executePublish(modal, data, originalBtn, selectedDescendantIds) {
        modal.close();

        var originalHref = originalBtn.attr('href');
        var originalOnClick = originalBtn.attr('onclick');
        var hasDataRel = originalBtn.data('rel');

        if (selectedDescendantIds.length > 0) {
            var publishUrl = this._appendDescendantsToUrl(originalHref, selectedDescendantIds);
            originalBtn.attr('href', publishUrl);
        }

        if (hasDataRel === 'ajax') {
            var postData = originalBtn.data('post') || {};
            if (selectedDescendantIds.length > 0) {
                postData.descendant_ids = selectedDescendantIds;
            }
            originalBtn.data('post', postData);
            
            CMS.API.Toolbar._delegate(originalBtn);
        } else if (originalHref && originalHref !== '#') {
            Helpers._getWindow().location.href = originalBtn.attr('href');
        } else if (originalOnClick) {
            originalBtn[0].click();
        } else if (originalBtn.hasClass('cms-form-post-method')) {
            this._submitWithPostMethod(originalBtn, selectedDescendantIds);
        }
    }

    /**
     * Append descendant IDs to URL
     * @method _appendDescendantsToUrl
     * @private
     * @param {String} url
     * @param {Array} descendantIds
     * @returns {String}
     */
    _appendDescendantsToUrl(url, descendantIds) {
        if (!url || descendantIds.length === 0) {
            return url;
        }

        var separator = url.indexOf('?') === -1 ? '?' : '&';
        var queryString = descendantIds.map(function(id) {
            return 'descendant_ids=' + id;
        }).join('&');

        return url + separator + queryString;
    }

    /**
     * Submit using form post method
     * @method _submitWithPostMethod
     * @private
     * @param {jQuery} btn
     * @param {Array} descendantIds
     */
    _submitWithPostMethod(btn, descendantIds) {
        var formToken = document.querySelector('form input[name="csrfmiddlewaretoken"]');
        var csrfToken = ((formToken ? formToken.value : formToken) || window.CMS.config.csrf);
        
        var hiddenFields = '';
        if (descendantIds.length > 0) {
            descendantIds.forEach(function(id) {
                hiddenFields += '<input type="hidden" name="descendant_ids" value="' + id + '">';
            });
        }

        var fakeForm = $(
            '<form style="display: none" action="' + btn.attr('href') + '" method="POST">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrfToken + '">' +
            hiddenFields +
            '</form>'
        );

        fakeForm.appendTo(Helpers._getWindow().document.body).submit();
    }

    /**
     * Show error message
     * @method _showError
     * @private
     * @param {String} message
     */
    _showError(message) {
        CMS.API.Messages.open({
            message: message,
            error: true
        });
    }

    /**
     * Escape HTML
     * @method _escapeHtml
     * @private
     * @param {String} text
     * @returns {String}
     */
    _escapeHtml(text) {
        if (!text) {
            return '';
        }
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Cleanup
     * @method _cleanup
     * @private
     */
    _cleanup() {
        this.ui.modal = null;
    }
}

PublishConfirmation.options = {
    publishBtnSelector: '.cms-btn-publish, .cms-publish-page, [data-action="publish"]',
};

export default PublishConfirmation;

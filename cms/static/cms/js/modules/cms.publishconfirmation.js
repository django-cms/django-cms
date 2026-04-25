/*
 * Copyright https://github.com/divio/django-cms
 */

/* global gettext */

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
            debug: false,
        }, options);

        this.click = 'click.cms.publishconfirmation';
        this._setupUI();
        this._events();
        
        if (this.options.debug) {
            console.log('[PublishConfirmation] Initialized with selector:', this.options.publishBtnSelector);
        }
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
            
            if (that.options.debug) {
                console.log('[PublishConfirmation] Button clicked:', btn);
                console.log('[PublishConfirmation] Button href:', btn.attr('href'));
                console.log('[PublishConfirmation] Button classes:', btn.attr('class'));
            }
            
            if (btn.hasClass('cms-btn-disabled')) {
                if (that.options.debug) {
                    console.log('[PublishConfirmation] Button is disabled, skipping');
                }
                return false;
            }

            e.preventDefault();
            e.stopImmediatePropagation();
            
            that._handlePublishClick(btn);
        });

        if (this.options.debug) {
            console.log('[PublishConfirmation] Events bound to document for selector:', this.options.publishBtnSelector);
        }
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
        
        if (this.options.debug) {
            console.log('[PublishConfirmation] Extracted page info:', pageInfo);
        }
        
        if (!pageInfo.pageId && !pageInfo.pageContentId && !pageInfo.apiUrl) {
            this._showError(gettext('Missing page information for publish confirmation'));
            if (this.options.debug) {
                console.error('[PublishConfirmation] Missing page information');
            }
            return;
        }

        var apiUrl = pageInfo.apiUrl || this._buildApiUrl(pageInfo);
        
        if (this.options.debug) {
            console.log('[PublishConfirmation] API URL:', apiUrl);
        }

        if (!apiUrl) {
            this._showError(gettext('Could not build API URL for publish confirmation'));
            return;
        }

        showLoader();
        
        $.ajax({
            url: apiUrl,
            method: 'GET',
            dataType: 'json',
        })
        .done(function(response) {
            hideLoader();
            if (that.options.debug) {
                console.log('[PublishConfirmation] API response:', response);
            }
            that._showConfirmationDialog(response, btn);
        })
        .fail(function(jqXHR) {
            hideLoader();
            if (that.options.debug) {
                console.error('[PublishConfirmation] API request failed:', jqXHR);
            }
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
            adminBase: null,
        };

        var btnHref = btn.attr('href');
        if (btnHref && btnHref !== '#') {
            var urlInfo = this._extractFromUrl(btnHref);
            if (urlInfo.pageId && !pageInfo.pageId) {
                pageInfo.pageId = urlInfo.pageId;
            }
            if (urlInfo.pageContentId && !pageInfo.pageContentId) {
                pageInfo.pageContentId = urlInfo.pageContentId;
            }
            if (urlInfo.language && !pageInfo.language) {
                pageInfo.language = urlInfo.language;
            }
            if (urlInfo.adminBase) {
                pageInfo.adminBase = urlInfo.adminBase;
            }
        }

        if (!pageInfo.pageId && !pageInfo.pageContentId) {
            var currentUrlInfo = this._extractFromUrl(window.location.pathname);
            if (currentUrlInfo.pageId && !pageInfo.pageId) {
                pageInfo.pageId = currentUrlInfo.pageId;
            }
            if (currentUrlInfo.pageContentId && !pageInfo.pageContentId) {
                pageInfo.pageContentId = currentUrlInfo.pageContentId;
            }
            if (currentUrlInfo.language && !pageInfo.language) {
                pageInfo.language = currentUrlInfo.language;
            }
            if (currentUrlInfo.adminBase && !pageInfo.adminBase) {
                pageInfo.adminBase = currentUrlInfo.adminBase;
            }
        }

        return pageInfo;
    }

    /**
     * Extract page ID, language, and admin base from URL
     * URL patterns:
     * - /en/admin/cms/page/33/en/publish/  -> pageId: 33, language: en (after page ID), adminBase: /en/admin/
     * - /admin/cms/pagecontent/123/change/ -> pageContentId: 123, adminBase: /admin/
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
            adminBase: null,
        };

        if (!url) {
            return result;
        }

        var adminMatch = url.match(/^(.+\/admin\/)/);
        if (adminMatch) {
            result.adminBase = adminMatch[1];
        }

        var pageContentMatch = url.match(/\/pagecontent\/(\d+)/);
        if (pageContentMatch) {
            result.pageContentId = parseInt(pageContentMatch[1], 10);
        }

        var pageMatch = url.match(/\/page\/(\d+)/);
        if (pageMatch) {
            result.pageId = parseInt(pageMatch[1], 10);
            
            var afterPageId = url.substring(url.indexOf('/page/' + result.pageId) + ('/page/' + result.pageId).length);
            var langAfterPageMatch = afterPageId.match(/^\/([a-z]{2}(-[a-z]{2})?)\//);
            if (langAfterPageMatch) {
                result.language = langAfterPageMatch[1].toLowerCase();
            }
        }

        if (!result.language) {
            var langMatch = url.match(/\/([a-z]{2}(-[a-z]{2})?)\//);
            if (langMatch && langMatch[1].length >= 2) {
                var lang = langMatch[1].toLowerCase();
                if (lang !== 'admin' && lang !== 'cms') {
                    result.language = lang;
                }
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
        var adminBase;
        
        if (pageInfo.adminBase) {
            adminBase = pageInfo.adminBase;
        } else {
            var baseUrl = window.location.pathname;
            var adminMatch = baseUrl.match(/^(.+\/admin\/)/);
            adminBase = adminMatch ? adminMatch[1] : '/admin/';
        }
        
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
            title: gettext('Publish Confirmation'),
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
        
        html += '<div class="cms-publish-confirmation-header">';
        html += '<h3>' + gettext('Publish Confirmation') + '</h3>';
        html += '<p>' + gettext('Publishing page:') + ' <strong>' + this._escapeHtml(data.page_title) + '</strong></p>';
        html += '</div>';

        if (data.has_descendants && data.descendants && data.descendants.length > 0) {
            html += '<div class="cms-publish-confirmation-descendants">';
            html += '<h4>' + gettext('Select child pages to publish (optional):') + '</h4>';
            
            html += '<div class="cms-publish-confirmation-select-all">';
            html += '<label>';
            html += '<input type="checkbox" id="id_select_all_descendants" class="js-cms-publish-select-all">';
            html += '<span>' + gettext('Select all') + '</span>';
            html += '</label>';
            html += '</div>';

            html += '<ul class="cms-publish-confirmation-list">';
            
            data.descendants.forEach(function(descendant) {
                var indentClass = descendant.depth > 1 ? ' cms-publish-confirmation-item-indent-' + descendant.depth : '';
                var indicatorClass = descendant.indicator ? 'cms-pagetree-node-state cms-pagetree-node-state-' + descendant.indicator : '';
                
                html += '<li class="cms-publish-confirmation-item' + indentClass + '">';
                html += '<label>';
                html += '<input type="checkbox" name="descendant_ids" value="' + descendant.id + '" class="js-cms-publish-descendant-checkbox" data-indicator="' + (descendant.indicator || '') + '">';
                html += '<span class="cms-publish-confirmation-title">' + that._escapeHtml(descendant.title) + '</span>';
                if (indicatorClass) {
                    html += '<span class="cms-publish-confirmation-indicator ' + indicatorClass + '"></span>';
                }
                html += '</label>';
                html += '</li>';
            });
            
            html += '</ul>';
            html += '</div>';
        } else {
            html += '<div class="cms-publish-confirmation-no-descendants">';
            html += '<p>' + gettext('This page has no child pages.') + '</p>';
            html += '</div>';
        }

        html += '<div class="cms-publish-confirmation-footer">';
        html += '<button type="button" class="cms-btn cms-btn-action js-cms-publish-confirm">' + gettext('Confirm Publish') + '</button>';
        html += '<button type="button" class="cms-btn js-cms-publish-cancel">' + gettext('Cancel') + '</button>';
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

        if (this.options.debug) {
            console.log('[PublishConfirmation] Executing publish with selected IDs:', selectedDescendantIds);
            console.log('[PublishConfirmation] Original href:', originalHref);
            console.log('[PublishConfirmation] Original onclick:', originalOnClick);
        }

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
            this._executeOnClick(originalBtn);
        } else if (originalBtn.hasClass('cms-form-post-method')) {
            this._submitWithPostMethod(originalBtn, selectedDescendantIds);
        }
    }

    /**
     * Execute the onclick handler directly without re-triggering event listeners
     * @method _executeOnClick
     * @private
     * @param {jQuery} btn
     */
    _executeOnClick(btn) {
        var that = this;
        var originalOnClick = btn.attr('onclick');
        
        if (this.options.debug) {
            console.log('[PublishConfirmation] Executing onclick directly:', originalOnClick);
        }

        if (typeof btn[0].onclick === 'function') {
            if (this.options.debug) {
                console.log('[PublishConfirmation] onclick is a function, executing directly');
            }
            btn[0].onclick.call(btn[0]);
        } else if (originalOnClick) {
            if (this.options.debug) {
                console.log('[PublishConfirmation] onclick is a string, using eval');
            }
            try {
                eval(originalOnClick);
            } catch (e) {
                console.error('[PublishConfirmation] Error executing onclick:', e);
                this._showError(gettext('Error executing publish action'));
            }
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

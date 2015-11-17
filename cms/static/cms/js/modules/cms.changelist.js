//##############################################################################
// CHANGELIST
/* global CMS, tree_component */

(function ($) {
    'use strict';
    // CMS.$ will be passed for $
    $(document).ready(function () {

        /*!
         * TreeManager
         * Handles treeview
         * TODO this will be refactored in 3.2
         */
        CMS.TreeManager = new CMS.Class({

            options: {
                'lang': {}
            },

            initialize: function (options) {
                this.options = $.extend(true, {}, this.options, options);

                this.setupFunctions();
                this.setupTreePublishing();
                this.setupInfoTooltip();
                this.setupUIHacks();

                // load internal functions
                if (!this.options.settings.filtered) {
                    this.setupGlobals();
                    this.setupTree();

                    // init tree component
                    window.initTree();
                } else {
                    // when filtered is active, prevent tree actions
                    $.syncCols();
                }
            },

            setupFunctions: function () {
                var that = this;

                $.syncCols = function () {
                    $('#sitemap .col-softroot').syncWidth(0);
                    $('#sitemap .col-apphook').syncWidth(0);
                    $('#sitemap .col-language').syncWidth(0);
                    $('#sitemap .col-navigation').syncWidth(0);
                    $('#sitemap .col-actions').syncWidth(0);
                    $('#sitemap .col-info').syncWidth(0);

                    that.refreshColumns.call($('ul.tree-default li'));
                };

                /* Colums width sync */
                $.fn.syncWidth = function (max) {
                    var visible = false;

                    $(this).each(function () {
                        if ($(this).is(':visible')) {
                            visible = true;
                            var val = $(this).width();
                            if (val > max) {
                                max = val;
                            }
                        }
                    });
                    if (visible && max > 0) {
                        $(this).each(function () {
                            $(this).css('width', max);
                        });
                    }
                };

                // jquery.functional
                $.curry = function (fn) {
                    if (arguments.length < 2) {
                        return fn;
                    }
                    var args = $.makeArray(arguments).slice(1, arguments.length);
                    return function () {
                        return fn.apply(this, args.concat($.makeArray(arguments)));
                    };
                };

                $.__callbackPool = {};

                $.callbackRegister = function (name, fn /*, arg0, arg1, ..*/) {
                    if (arguments.length > 2) {
                        // create curried function
                        fn = $.curry.apply(this, $.makeArray(arguments).slice(1, arguments.length));
                    }
                    $.__callbackPool[name] = fn;
                    return name;
                };

                $.callbackCall = function (name/*, extra arg0, extra arg1, ..*/) {
                    if (!name || !(name in $.__callbackPool)) {
                        throw 'No callback registered with name: ' + name;
                    }
                    $.__callbackPool[name].apply(this, $.makeArray(arguments).slice(1, arguments.length));
                    $.callbackRemove(name);
                    return name;
                };

                $.callbackRemove = function (name) {
                    delete $.__callbackPool[name];
                };

                // very simple yellow fade plugin..
                $.fn.yft = function () {
                    this.effect('highlight', {}, 1000);
                };

                // jquery replace plugin :)
                $.fn.replace = function (o) {
                    return this.after(o).remove().end();
                };

            },

            setupInfoTooltip: function () {
                var tree = $('.tree');
                var infoTrigger = '.col-info .info';
                var infoTooltips = '.info-details';
                var infoTimer = function () {};
                var infoDelay = 100;
                // workaround for the info tooltip on touch devices
                var touchUsedInfoTooltip;

                tree.delegate(infoTrigger, 'pointerover touchstart', function (e) {
                    var tooltip = $(this).closest('.col-info').find('.info-details');

                    // clear timer
                    clearTimeout(infoTimer);

                    // cancel if tooltip already visible
                    if (tooltip.is(':visible') && !touchUsedInfoTooltip) {
                        return false;
                    }

                    $(infoTooltips).hide();
                    $(infoTrigger).removeClass('hover');
                    $('.moveable').removeClass('hover');

                    if (e.type === 'touchstart') {
                        e.preventDefault();
                        var target = $(e.target).closest(infoTrigger);
                        touchUsedInfoTooltip = touchUsedInfoTooltip && touchUsedInfoTooltip.is(target) ? false : target;
                        if (touchUsedInfoTooltip) {
                            return;
                        }
                    }

                    infoTimer = setTimeout(function () {
                        tooltip.show();
                        $(infoTrigger).addClass('hover');
                        tooltip.closest('.moveable').addClass('hover');
                    }, infoDelay);

                });
                // hide the tooltip when leaving the area
                tree.delegate(infoTrigger, 'pointerout', function () {
                    if (touchUsedInfoTooltip) {
                        return;
                    }

                    // clear timer
                    clearTimeout(infoTimer);
                    // hide all elements
                    infoTimer = setTimeout(function () {
                        $(infoTooltips).hide();
                        $('.moveable').removeClass('hover');
                    }, infoDelay * 2);
                });
                // reset hiding when entering the tooltip itself
                tree.delegate(infoTooltips, 'pointerover', function () {
                    // clear timer
                    clearTimeout(infoTimer);
                });
                tree.delegate(infoTooltips, 'pointerout', function () {
                    // hide all elements
                    infoTimer = setTimeout(function () {
                        $(infoTooltips).hide();
                        $('.moveable').removeClass('hover');
                    }, infoDelay * 2);
                });
                $('html').on('touchend', function (e) {
                    if (!$(e.target).hasClass('info')) {
                        $(infoTooltips).hide();
                        $(infoTrigger).removeClass('hover');
                        $('.moveable').removeClass('hover');
                    }
                });
            },

            setupTreePublishing: function () {
                // ADD DIRECT PUBLISHING
                var that = this;
                var tree = $('.tree');
                var langTrigger = '.col-language .trigger-tooltip';
                var langTooltips = '.language-tooltip';
                var langTimer = function () {};
                var langDelay = 100;
                // workaround for the publishing tooltip on touch devices
                var touchUsedNode;

                // show the tooltip
                tree.delegate(langTrigger, 'pointerover touchstart', function (e) {
                    var el = $(this).closest('.col-language').find('.language-tooltip');

                    // clear timer
                    clearTimeout(langTimer);

                    // cancel if tooltip already visible
                    if (el.is(':visible') && !touchUsedNode) {
                        return false;
                    }

                    // set correct position
                    el.css('right', 32 + $(this).position().left);

                    // hide all elements
                    $(langTooltips).hide();
                    $('.moveable').removeClass('hover');

                    if (e.type === 'touchstart') {
                        e.preventDefault();
                        var target = $(e.target).closest(langTrigger);
                        touchUsedNode = touchUsedNode && touchUsedNode.is(target) ? false : target;
                        if (touchUsedNode) {
                            return;
                        }
                    }

                    // use a timeout to display the tooltip
                    langTimer = setTimeout(function () {
                        el.closest('.moveable').addClass('hover');
                        el.show();
                    }, langDelay);
                });
                // hide the tooltip when leaving the area
                tree.delegate(langTrigger, 'pointerout', function () {
                    if (touchUsedNode) {
                        return;
                    }

                    // clear timer
                    clearTimeout(langTimer);
                    // hide all elements
                    langTimer = setTimeout(function () {
                        $(langTooltips).hide();
                        $('.moveable').removeClass('hover');
                    }, langDelay * 2);
                });
                // reset hiding when entering the tooltip itself
                tree.delegate(langTooltips, 'pointerover', function () {
                    // clear timer
                    clearTimeout(langTimer);
                });
                tree.delegate(langTooltips, 'pointerout', function () {
                    // hide all elements
                    langTimer = setTimeout(function () {
                        $(langTooltips).hide();
                        $('.moveable').removeClass('hover');
                    }, langDelay * 2);
                });
                // attach double check event if publish or unpublish should be triggered
                tree.delegate('.language-tooltip a', 'click touchstart', function (e) {
                    e.preventDefault();

                    // cancel if not confirmed
                    if (!CMS.API.Helpers.secureConfirm(that.options.lang.publish
                        .replace('§', $(this).text().toLowerCase()))) {
                        return false;
                    }

                    // send post request to prevent xss attacks
                    $.ajax({
                        type: 'post',
                        url: $(this).prop('href'),
                        success: function () {
                            CMS.API.Helpers.reloadBrowser();
                        },
                        error: function (request) {
                            throw new Error(request);
                        }
                    });
                });
                $('html').on('touchend', function (e) {
                    if (!$(e.target).hasClass('unpublished') ||
                        !$(e.target).hasClass('published') ||
                        !$(e.target).hasClass('dirty')) {
                        $(langTooltips).hide();
                        $('.moveable').removeClass('hover');
                    }
                });
            },

            setupUIHacks: function () {
                // adds functionality to the filter
                $('#changelist-filter-button').bind('click', function () {
                    $('#changelist-filter').toggle();
                });

                // set correct active entry
                if (window.parent && window.parent.CMS && window.parent.CMS.config) {
                    var page_id = window.parent.CMS.config.request.page_id;

                    $('div[data-page_id="' + page_id + '"]').addClass('cont-active');
                }
            },

            setupGlobals: function () {
                var that = this;
                var msg = '';
                var parent = null;

                window.moveSuccess = function (node) {
                    $.syncCols();

                    msg = $('<span class="success">' + that.options.lang.success + '</span>');
                    parent = window.parent;

                    node.after(msg);
                    node.parent().find('.col2').hide();
                    msg.fadeOut(1000, function () {
                        node.parent().find('.col2').show();
                    });
                    // check for reload changes
                    if (window.self !== window.top) {
                        window.parent.CMS.API.Helpers.reloadBrowser(false, false, true);
                        window.parent.CMS.API.Messages.open({
                            message: that.options.lang.changes,
                            delay: 0
                        });
                    }
                };

                window.moveError = function (node, message) {
                    if (message && message !== 'error') {
                        msg = $('<span class="success">' + message + '</span>');
                    } else {
                        msg = $('<span class="success">' + that.options.lang.error + '</span>');
                    }
                    node.parent().find('.col2').hide();
                    node.after(msg);
                };

            },

            setupTree: function () {
                var that = this;
                var tree;
                var origin = window.location.protocol + '//' + window.location.hostname +
                    (window.location.port ? ':' + window.location.port : '');
                // global initTree function
                window.initTree = function () {
                    // jshint newcap: false
                    // jscs:disable requireCapitalizedConstructors
                    tree = new tree_component();
                    // jscs:enable requireCapitalizedConstructors
                    // jshint newcap: true
                    var options = {
                        rules: {
                            clickable: 'all',
                            renameable: 'none',
                            deletable: 'all',
                            creatable: 'all',
                            draggable: 'all',
                            dragrules: 'all',
                            droppable: 'all',
                            metadata : 'mdata',
                            use_inline: true
                            //droppable : ['tree_drop']
                        },
                        // has to be absolute full path
                        path: origin + that.options.settings.staticPath + 'cms/js/jstree/',
                        ui: {
                            dots: true,
                            rtl: false,
                            animation: 0,
                            hover_mode: true,
                            //theme_path: script_url_path() + '/../jstree/themes/',
                            a_class: 'title',
                            context: false
                        },
                        cookies : {
                            prefix: 'djangocms_nodes'
                        },
                        callback: {
                            beforemove  : function (what, where, position) {
                                window.item_id = what.id.split('page_')[1];
                                window.target_id = where.id.split('page_')[1];
                                window.old_node = what;

                                if ($(what).parent().children('li').length > 1) {
                                    if ($(what).next('li').length) {
                                        window.old_target = $(what).next('li')[0];
                                        window.old_position = 'right';
                                    }
                                    if ($(what).prev('li').length) {
                                        window.old_target = $(what).prev('li')[0];
                                        window.old_position = 'left';
                                    }
                                } else {
                                    if ($(what).attr('rel') !== 'topnode') {
                                        window.old_target = $(what).parent().parent()[0];
                                        window.old_position = 'inside';
                                    }
                                }

                                addUndo(what, where, position);
                                return true;
                            },
                            onmove: function (what, where, position) {
                                window.item_id = what.id.split('page_')[1];
                                window.target_id = where.id.split('page_')[1];

                                if (position === 'before') {
                                    position = 'left';
                                } else if (position === 'after') {
                                    position = 'right';
                                } else if (position === 'inside') {
                                    position = 'last-child';
                                }
                                moveTreeItem(what, window.item_id, window.target_id, position, false);
                            },

                            onload: function () {
                                setTimeout(function () {
                                    reCalc();
                                }, 250);
                            }

                        }
                    };

                    if (!$($('div.tree').get(0)).hasClass('root_allow_children')) {
                        // disalow possibility for adding subnodes to main tree, user doesn't
                        // have permissions for this
                        options.rules.dragrules = ['node inside topnode', 'topnode inside topnode', 'node * node'];
                    }

                    tree.init($('div.tree'), options);
                };

                window.selected_page = false;
                action = false;

                var _oldAjax = $.ajax;

                $.ajax = function (s) {
                    // just override ajax function, so the loader message gets displayed
                    // always
                    $('#loader-message').show();

                    var callback = s.success || false;
                    s.success = function (data, status) {
                        if (callback) {
                            callback(data, status);
                        }
                        $('#loader-message').hide();
                    };

                    // just for debuging!!
                    /*s.complete = function (xhr, status) {
                        if (status == 'error' && that.options.settings.debug) {
                            $('body').before(xhr.responseText);
                        }
                    }*/
                    // end just for debuging

                    // TODO: add error state!
                    return _oldAjax(s);
                };

                // // defined but never used
                // function refresh() {
                //     window.location = window.location.href;
                // }

                // // defined but never used
                // function refreshIfChildren(pageId) {
                //     return $('#page_' + pageId).find('li[id^=page_]').length ?
                //     refresh :
                //     function () { return true; };
                // }

                /**
                 * Loads remote dialog to dialogs div.
                 *
                 * @param {String} url
                 * @param {Object} data Data to be send over post
                 * @param {Function} noDialogCallback Gets called when response is empty.
                 * @param {Function} callback Standard callback function.
                 */
                function loadDialog(url, data, noDialogCallback, callback) {
                    if (data === undefined) {
                        data = {};
                    }
                    $.post(url, data, function (response) {
                        if (response === '' && noDialogCallback) {
                            noDialogCallback();
                        }
                        $('#dialogs').empty().append(response);
                        if (callback) {
                            callback(response);
                        }
                    });
                }

                function mark_copy_node(id) {
                    $('a.move-target, span.move-target-container, span.line').show();
                    $('#page_' + id).addClass('selected');
                    $('#page_' + id).parent().parent()
                        .children('div.cont').find('a.move-target.first-child, span.second').hide();
                    $('#page_' + id).parent().parent()
                        .children('ul').children('li').children('div.cont')
                        .find('a.move-target.left, a.move-target.right, span.first, span.second').hide();
                    return 'copy';
                }


                // let's start event delegation
                $('#changelist li').on('click', function (e) {
                    // I want a link to check the class
                    if (e.target.tagName === 'IMG' || e.target.tagName === 'SPAN') {
                        window.target = e.target.parentNode;
                    } else {
                        window.target = e.target;
                    }
                    var jtarget = $(window.target);
                    var id;
                    var page_id;
                    if (jtarget.hasClass('move')) {
                        // prepare tree for move / cut paste
                        id = e.target.id.split('move-link-')[1];
                        if (!id) {
                            id = e.target.parentNode.id.split('move-link-')[1];
                        }
                        page_id = id;
                        window.selected_page = page_id;
                        action = 'move';
                        $('span.move-target-container, span.line, a.move-target').show();
                        $('#page_' + page_id).addClass('selected');
                        $('#page_' + page_id + ' span.move-target-container').hide();
                        e.stopPropagation();
                        return false;
                    }

                    if (jtarget.hasClass('copy')) {
                        // prepare tree for copy
                        id = e.target.id.split('copy-link-')[1];
                        if (!id) {
                            id = e.target.parentNode.id.split('copy-link-')[1];
                        }
                        window.selected_page = id;
                        action = mark_copy_node(id);
                        e.stopPropagation();
                        return false;
                    }

                    if (jtarget.hasClass('viewpage')) {
                        var view_page_url = $('#' + window.target.id + '-select').val();
                        if (view_page_url) {
                            window.open(view_page_url);
                        }
                    }

                    if (jtarget.hasClass('addlink')) {
                        if (!/#$/g.test(jtarget.attr('href'))) {
                            // if there is url instead of # inside href, follow this url
                            // used if user haves add_page
                            return true;
                        }

                        $('tr').removeClass('target');
                        $('#changelist table').removeClass('table-selected');
                        page_id = window.target.id.split('add-link-')[1];
                        window.selected_page = page_id;
                        action = 'add';
                        $('tr').removeClass('selected');
                        $('#page-row-' + page_id).addClass('selected');
                        $('.move-target-container').hide();
                        $('a.move-target, span.line, #move-target-' + page_id).show();
                        e.stopPropagation();
                        return false;
                    }

                    // don't assume admin site is root-level
                    // grab base url to construct full absolute URLs
                    window.admin_base_url = document.URL.split('/cms/page/')[0] + '/';

                    var pageId;
                    var language;
                    // in navigation
                    if (jtarget.hasClass('navigation-checkbox')) {
                        e.stopPropagation();

                        pageId = jtarget.attr('name').split('navigation-')[1];
                        language = jtarget.closest('.cont').find('a[lang]').attr('lang') || '';

                        // if I don't put data in the post, django doesn't get it
                        reloadItem(
                            jtarget,
                            window.admin_base_url + 'cms/page/' + pageId + '/change-navigation/?language=' + language,
                            { 1: 1 }
                        );
                    }

                    // lazy load descendants on tree open
                    if (jtarget.hasClass('closed')) {
                        // only load them once
                        if (jtarget.find('ul > li').length === 0 && !jtarget.hasClass('loading')) {
                            // keeps this event from firing multiple times before
                            // the dom as changed. it still needs to propagate for
                            // the other click event on this element to fire
                            jtarget.addClass('loading');
                            pageId = $(jtarget).attr('id').split('page_')[1];
                            language = $(jtarget)
                                .children('div.cont')
                                .children('div.col1')
                                .children('.title').attr('lang');
                            $.get(
                                window.admin_base_url + 'cms/page/' + pageId + '/' + language + '/descendants/',
                                {},
                                function (r) {
                                    jtarget.children('ul').append(r);
                                    // show move targets if needed
                                    if ($('span.move-target-container:visible').length > 0) {
                                        jtarget.children('ul')
                                            .find('a.move-target, span.move-target-container, span.line')
                                            .show();
                                    }
                                    reCalc();
                                }
                            );
                        } else {
                            reCalc();
                        }
                    }

                    if (jtarget.hasClass('move-target')) {
                        if (jtarget.hasClass('left')) {
                            window.position = 'left';
                        }
                        if (jtarget.hasClass('right')) {
                            window.position = 'right';
                        }
                        if (jtarget.hasClass('last-child')) {
                            window.position = 'last-child';
                        }
                        window.target_id = window.target.parentNode.id.split('move-target-')[1];

                        if (action === 'move') {
                            moveTreeItem(null, window.selected_page, window.target_id, window.position, tree);
                            $('.move-target-container').hide();
                        } else if (action === 'copy') {
                            window.site = $('#site-select')[0].value;
                            copyTreeItem(window.selected_page, window.target_id, window.position, window.site);
                            $('.move-target-container').hide();
                        } else if (action === 'add') {
                            window.site = $('#site-select')[0].value;
                            window.location.href = window.location.href.split('?')[0].split('#')[0] +
                                'add/?target=' + window.target_id + '&amp;position=' + window.position +
                                '&amp;site=' + window.site;
                        }
                        e.stopPropagation();
                        return false;
                    }
                    return true;
                });
                $('div#sitemap').show();

                function reCalc() {
                    $.syncCols();
                }

                $(window).bind('resize', reCalc);
                /* Site Selector */
                $('#site-select').change(function () {
                    var form = $(this).closest('form');
                    // add correct value for copy
                    if (action === 'copy') {
                        $('#site-copy').val(window.selected_page);
                    }
                    // submit form
                    form.submit();
                });

                //
                // If an A element has a data-attribute 'alt-class'. At this time,
                // this is only the edit button in the page-tree, but could be
                // more in future. It is important that the CSS be written in such
                // a manner that the alt-class is defined after the normal class,
                // so that it can be overridden when the alt-key is depressed.
                //
                // NOTE: This 'preview' part of the 'alt-click to [alternative
                // function]' feature may not work in some environments (Windows
                // in a some virtual machine environments, notably), but is only a
                // nice-'extra', not a requirement for the feature.
                //
                $(document).on('keydown keyup', function (evt) {
                    if (evt.which === 18) {
                        $('a[data-alt-class]').each(function () {
                            var self = $(this);
                            self.toggleClass(self.data('alt-class'), evt.type === 'keydown');
                        });
                    }
                });

                //
                // If the A-element has a data-attribute 'alt-href', then this
                // click-handler uses that instead of the normal href attribute as
                // the click-destination. Again, currently this is only on the
                // edit button, but could be more in future.
                //
                $('a[data-alt-href]').on('click', function (evt) {
                    var href;
                    evt.preventDefault();
                    if (evt.shiftKey) {
                        href = $(this).data('alt-href');
                    } else {
                        href = $(this).attr('href');
                    }
                    window.location = href;
                });

                var copy_splits = window.location.href.split('copy=');
                if (copy_splits.length > 1) {
                    var id = copy_splits[1].split('&')[0];
                    // jshint latedef: false
                    var action = mark_copy_node(id);
                    // jshint latedef: true
                    window.selected_page = id;
                }

                function copyTreeItem(item_id, target_id, position, site) {
                    if (that.options.settings.permission) {
                        return loadDialog('./' + item_id + '/dialog/copy/', {
                            position: position,
                            target: target_id,
                            site: site,
                            callback: $.callbackRegister(
                                '_copyTreeItem', _copyTreeItem, item_id, target_id, position, site
                            )
                        });
                    }
                    return _copyTreeItem(item_id, target_id, position, site);
                }

                function _copyTreeItem(item_id, target_id, position, site, options) {
                    var data = {
                        position: position,
                        target: target_id,
                        site: site
                    };
                    data = $.extend(data, options);

                    $.post('./' + item_id + '/copy-page/', data, function (decoded) {
                        var response = decoded.content;
                        var status = decoded.status;
                        if (status === 200) {
                            // reload tree
                            window.location = window.location.href;
                        } else {
                            alert(response);
                            window.moveError($('#page_' + item_id + ' div.col1:eq(0)'), response);
                        }
                    });
                }

                /**
                 * Reloads tree item (one line). If some filtering is found, adds
                 * filtered variable into posted data.
                 *
                 * @param {HTMLElement} el Any child element of tree item
                 * @param {String} url Requested url
                 * @param {Object} data Optional posted data
                 * @param {Function} callback Optional calback function
                 */
                function reloadItem(el, url, data, callback, errorCallback) {
                    if (data === undefined) {
                        data = {};
                    }

                    if (/\/\?/ig.test(window.location.href)) {
                        // probably some filter here, tell backend, we need a filtered
                        // version of item
                        data.fitlered = 1;
                    }

                    function onSuccess(response, textStatus) {
                        var status = true;
                        var target = null;

                        if (callback) {
                            status = callback(response, textStatus);
                        }
                        if (status) {
                            if (/page_\d+/.test($(el).attr('id'))) {
                                // one level higher
                                target = $(el).find('div.cont:first');
                            } else {
                                target = $(el).parents('div.cont:first');
                            }

                            var parent = target.parent();

                            // remove the element if something went wrong
                            if (response === 'NotFound') {
                                return parent.remove();
                            }

                            var origin = $('.messagelist');
                            target.replace(response);

                            var messages = $(parent).find('.messagelist');
                            if (messages.length) {
                                origin.remove();
                                messages.insertAfter('.breadcrumbs');
                            }
                            parent.find('div.cont:first').yft();

                            // ensure after removal everything is aligned again
                            $(window).trigger('resize');
                        }
                    }

                    $.ajax({
                        'type': 'POST',
                        'data': data,
                        'url': url,
                        'success': onSuccess,
                        'error': function (XMLHttpRequest, textStatus, errorThrown) {
                            // errorCallback is passed through the reloadItem function
                            if (errorCallback) {
                                errorCallback(XMLHttpRequest, textStatus, errorThrown);
                            }
                        },
                        'xhr': (window.ActiveXObject) ?
                            function () {
                                try {
                                    return new window.ActiveXObject('Microsoft.XMLHTTP');
                                } catch (e) {}
                            } :
                            function () {
                                return new window.XMLHttpRequest();
                            }
                    });
                }

                function moveTreeItem(jtarget, item_id, target_id, position, tree) {
                    reloadItem(
                        jtarget, './' + item_id + '/move-page/',

                        { position: position, target: target_id },

                        // on success
                        function (decoded) {
                            var response = decoded.content;
                            var status = decoded.status;
                            if (status === 200) {
                                if (tree) {
                                    var tree_pos = { 'left': 'before', 'right': 'after' }[position] || 'inside';
                                    tree.moved(
                                        '#page_' + item_id,
                                        $('#page_' + target_id + ' a.title')[0],
                                        tree_pos,
                                        false,
                                        false
                                    );
                                } else {
                                    window.moveSuccess($('#page_' + item_id + ' div.col1:eq(0)'));
                                }
                                return false;
                            } else {
                                window.moveError($('#page_' + item_id + ' div.col1:eq(0)'), response);
                                return false;
                            }
                        }
                    );
                }

                var undos = [];

                function addUndo(node, target, position) {
                    undos.push({ node: node, target: target, position: position });
                }
            },

            refreshColumns: function () {
                $('div.col2').children('div').each(function (index, item) {
                    $(item).css('display', 'block');
                });
                var min_width = 100000;
                var max_col2_width = 0;
                var max_col2 = null;
                $(this).each(function () {
                    var cont = $(this).children('div.cont');
                    if (!cont.is(':visible')) {
                        return;
                    }
                    var col1 = cont.children('div.col1').find('.title span');
                    var col2 = cont.children('div.col2');
                    var col1_width = col1.outerWidth(true);
                    var col2_width = col2.outerWidth(true);
                    var total_width = cont.outerWidth(true);

                    var dif = total_width - col1_width;
                    if (dif < min_width) {
                        min_width = dif;
                    }
                    if (col2_width > max_col2_width) {
                        max_col2_width = col2_width;
                        max_col2 = col2;
                    }
                });

                var offset = 50;
                var w = 0;
                var hidden_count = 0;
                var max_reached = false;
                if (max_col2) {
                    max_col2.children('div').each(function () {
                        if (!max_reached) {
                            w += $(this).outerWidth(true);
                        }

                        if (max_reached || w > (min_width - offset)) {
                            hidden_count = hidden_count + 1;
                            max_reached = true;
                        }
                    });

                    if (hidden_count) {
                        $(this).each(function () {
                            $(this).children('div.cont').children('div.col2').children('div')
                                .slice(-hidden_count).each(function () {
                                    $(this).css('display', 'none');
                                });
                        });
                        $('div#sitemap ul.header div.col2').children().slice(-hidden_count).each(function () {
                            $(this).css('display', 'none');
                        });
                    }
                }
            }

        });

    });
})(CMS.$);

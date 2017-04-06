/* ========================================================================
 * Bootstrap: dropdown.js v3.3.7
 * http://getbootstrap.com/javascript/#dropdowns
 * ========================================================================
 * Copyright 2011-2016 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */

/* eslint-disable complexity, semi, no-param-reassign, no-magic-numbers, require-jsdoc, curly, wrap-regex, eqeqeq,
    new-cap, no-multi-spaces, no-bitwise, no-extra-parens */
// modified for cms purposes - event names, parent resolutions, class names
var $ = require('jquery');

// DROPDOWN CLASS DEFINITION
// =========================

var backdrop = '.cms-dropdown-backdrop';
var toggle = '.cms-dropdown-toggle';
var Dropdown = function (element) {
    $(element).on('click.cms.dropdown', this.toggle);
};

function getParent($this) {
    return $this.closest('.cms-dropdown');
}

function clearMenus(e) {
    if (e && e.which === 3) return;
    $(backdrop).remove();
    $(toggle).each(function () {
        var $this = $(this)
        var $parent = getParent($this)
        var relatedTarget = { relatedTarget: this };

        if (!$parent.hasClass('cms-dropdown-open')) return;

        if (e && e.type == 'click' && (/input|textarea/i).test(e.target.tagName) && $.contains($parent[0], e.target)) {
            return;
        }

        $parent.trigger(e = $.Event('hide.cms.dropdown', relatedTarget))

        if (e.isDefaultPrevented()) {
            return;
        }

        $this.attr('aria-expanded', 'false')
        $parent.removeClass('cms-dropdown-open').trigger($.Event('hidden.cms.dropdown', relatedTarget))
    })
}

Dropdown.prototype.toggle = function (e) {
    var $this = $(this)

    if ($this.is('.cms-btn-disabled, :disabled')) return

    var $parent  = getParent($this)
    var isActive = $parent.hasClass('cms-dropdown-open')

    clearMenus()

    if (!isActive) {
        if ('ontouchstart' in document.documentElement && !$parent.closest('.navbar-nav').length) {
            // if mobile we use a backdrop because click events don't delegate
            $(document.createElement('div'))
                .addClass('cms-dropdown-backdrop')
                .insertAfter($(this))
                .on('click', clearMenus)
        }

        var relatedTarget = { relatedTarget: this }

        $parent.trigger(e = $.Event('show.cms.dropdown', relatedTarget))

        if (e.isDefaultPrevented()) return

        $this
            .trigger('focus')
            .attr('aria-expanded', 'true')

        $parent
            .toggleClass('cms-dropdown-open')
            .trigger($.Event('shown.cms.dropdown', relatedTarget))
    }

    return false
}

Dropdown.prototype.keydown = function (e) {
    if (!/(38|40|27|32)/.test(e.which) || /input|textarea/i.test(e.target.tagName)) return

    var $this = $(this)

    e.preventDefault()
    e.stopPropagation()

    if ($this.is('.cms-btn-disabled, :disabled')) return

    var $parent  = getParent($this)
    var isActive = $parent.hasClass('cms-dropdown-open')

    if (!isActive && e.which != 27 || isActive && e.which == 27) {
        if (e.which == 27) $parent.find(toggle).trigger('focus')
        return $this.trigger('click')
    }

    var desc = ' li:not(.cms-btn-disabled):visible a'
    var $items = $parent.find('.cms-dropdown-menu' + desc)

    if (!$items.length) return

    var index = $items.index(e.target)

    if (e.which == 38 && index > 0)                 index--         // up
    if (e.which == 40 && index < $items.length - 1) index++         // down
    if (!~index)                                    index = 0

    $items.eq(index).trigger('focus')
}


// DROPDOWN PLUGIN DEFINITION
// ==========================

function Plugin(option) {
    return this.each(function () {
        var $this = $(this)
        var data  = $this.data('cms.dropdown')

        if (!data) $this.data('cms.dropdown', (data = new Dropdown(this)))
        if (typeof option == 'string') data[option].call($this)
    })
}

var old = $.fn.dropdown

$.fn.dropdown             = Plugin
$.fn.dropdown.Constructor = Dropdown


// DROPDOWN NO CONFLICT
// ====================

$.fn.dropdown.noConflict = function () {
    $.fn.dropdown = old
    return this
}


$(function () {
    $(document)
        .on('click.cms.dropdown.data-api', clearMenus)
        .on('click.cms.dropdown.data-api', '.cms-dropdown form', function (e) {
            e.stopPropagation()
        })
        .on('pointerup.cms.dropdown.data-api', toggle, Dropdown.prototype.toggle)
        .on('keydown.cms.dropdown.data-api', toggle, Dropdown.prototype.keydown)
        .on('keydown.cms.dropdown.data-api', '.cms-dropdown-menu', Dropdown.prototype.keydown)
})

// $(function () {
//     $('.cms-dropdown-toggle').dropdown();
// });

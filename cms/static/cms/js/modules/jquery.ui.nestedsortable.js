/*
 * jQuery UI Nested Sortable
 * v 2.0 / 29 oct 2012
 * http://mjsarfatti.com/sandbox/nestedSortable
 *
 * Depends on:
 * jquery.ui.sortable.js 1.10+
 *
 * Copyright (c) 2010-2013 Manuele J Sarfatti
 * Licensed under the MIT License
 * http://www.opensource.org/licenses/mit-license.php
 */

(function($) {

    function isOverAxis( x, reference, size ) {
        return ( x > reference ) && ( x < ( reference + size ) );
    }

    $.widget("mjs.nestedSortable", $.extend({}, $.ui.sortable.prototype, {

        options: {
            doNotClear: false,
            expandOnHover: 700,
            isAllowed: function(placeholder, placeholderParent, originalItem) { return true; },
            isTree: false,
            listType: 'ol',
            maxLevels: 0,
            protectRoot: false,
            rootID: null,
            rtl: false,
            startCollapsed: false,
            tabSize: 20,

            branchClass: 'mjs-nestedSortable-branch',
            collapsedClass: 'mjs-nestedSortable-collapsed',
            disableNestingClass: 'mjs-nestedSortable-no-nesting',
            errorClass: 'mjs-nestedSortable-error',
            expandedClass: 'mjs-nestedSortable-expanded',
            hoveringClass: 'mjs-nestedSortable-hovering',
            leafClass: 'mjs-nestedSortable-leaf'
        },

        _create: function() {
            this.element.data('ui-sortable', this.element.data('mjs-nestedSortable'));

            // mjs - prevent browser from freezing if the HTML is not correct
            if (!this.element.is(this.options.listType))
                throw new Error('nestedSortable: Please check that the listType option is set to your actual list type');

            // mjs - force 'intersect' tolerance method if we have a tree with expanding/collapsing functionality
            if (this.options.isTree && this.options.expandOnHover) {
                this.options.tolerance = 'intersect';
            }

            $.ui.sortable.prototype._create.apply(this, arguments);

            // mjs - prepare the tree by applying the right classes (the CSS is responsible for actual hide/show functionality)
            if (this.options.isTree) {
                var self = this;
                $(this.items).each(function() {
                    var $li = this.item;
                    if ($li.children(self.options.listType).length) {
                        $li.addClass(self.options.branchClass);
                        // expand/collapse class only if they have children
                        if (self.options.startCollapsed) $li.addClass(self.options.collapsedClass);
                        else $li.addClass(self.options.expandedClass);
                    } else {
                        $li.addClass(self.options.leafClass);
                    }
                })
            }
        },

        _destroy: function() {
            this.element
                .removeData("mjs-nestedSortable")
                .removeData("ui-sortable");
            return $.ui.sortable.prototype._destroy.apply(this, arguments);
        },

        _mouseDrag: function(event) {
            var i, item, itemElement, intersection,
                o = this.options,
                scrolled = false;

            //Compute the helpers position
            this.position = this._generatePosition(event);
            this.positionAbs = this._convertPositionTo("absolute");

            if (!this.lastPositionAbs) {
                this.lastPositionAbs = this.positionAbs;
            }

            //Do scrolling
            if(this.options.scroll) {
                if(this.scrollParent[0] != document && this.scrollParent[0].tagName != 'HTML') {

                    if((this.overflowOffset.top + this.scrollParent[0].offsetHeight) - event.pageY < o.scrollSensitivity) {
                        this.scrollParent[0].scrollTop = scrolled = this.scrollParent[0].scrollTop + o.scrollSpeed;
                    } else if(event.pageY - this.overflowOffset.top < o.scrollSensitivity) {
                        this.scrollParent[0].scrollTop = scrolled = this.scrollParent[0].scrollTop - o.scrollSpeed;
                    }

                    if((this.overflowOffset.left + this.scrollParent[0].offsetWidth) - event.pageX < o.scrollSensitivity) {
                        this.scrollParent[0].scrollLeft = scrolled = this.scrollParent[0].scrollLeft + o.scrollSpeed;
                    } else if(event.pageX - this.overflowOffset.left < o.scrollSensitivity) {
                        this.scrollParent[0].scrollLeft = scrolled = this.scrollParent[0].scrollLeft - o.scrollSpeed;
                    }

                } else {

                    if(event.pageY - $(document).scrollTop() < o.scrollSensitivity) {
                        scrolled = $(document).scrollTop($(document).scrollTop() - o.scrollSpeed);
                    } else if($(window).height() - (event.pageY - $(document).scrollTop()) < o.scrollSensitivity) {
                        scrolled = $(document).scrollTop($(document).scrollTop() + o.scrollSpeed);
                    }

                    if(event.pageX - $(document).scrollLeft() < o.scrollSensitivity) {
                        scrolled = $(document).scrollLeft($(document).scrollLeft() - o.scrollSpeed);
                    } else if($(window).width() - (event.pageX - $(document).scrollLeft()) < o.scrollSensitivity) {
                        scrolled = $(document).scrollLeft($(document).scrollLeft() + o.scrollSpeed);
                    }

                }

                if(scrolled !== false && $.ui.ddmanager && !o.dropBehaviour)
                    $.ui.ddmanager.prepareOffsets(this, event);
            }

            //Regenerate the absolute position used for position checks
            this.positionAbs = this._convertPositionTo("absolute");

            // mjs - find the top offset before rearrangement,
            var previousTopOffset = this.placeholder.offset().top;

            //Set the helper position
            if(!this.options.axis || this.options.axis !== "y") {
                this.helper[0].style.left = this.position.left+"px";
            }
            if(!this.options.axis || this.options.axis !== "x") {
                this.helper[0].style.top = this.position.top+"px";
            }

            // mjs - check and reset hovering state at each cycle
            this.hovering = this.hovering ? this.hovering : null;
            this.mouseentered = this.mouseentered ? this.mouseentered : false;

            // mjs - let's start caching some variables
            var parentItem = (this.placeholder[0].parentNode.parentNode &&
                             $(this.placeholder[0].parentNode.parentNode).closest('.ui-sortable').length)
                                   ? $(this.placeholder[0].parentNode.parentNode)
                                   : null,
                level = this._getLevel(this.placeholder),
                childLevels = this._getChildLevels(this.helper);

            var newList = document.createElement(o.listType);

            //Rearrange
            for (i = this.items.length - 1; i >= 0; i--) {

                //Cache variables and intersection, continue if no intersection
                item = this.items[i];
                itemElement = item.item[0];
                intersection = this._intersectsWithPointer(item);
                if (!intersection) {
                    continue;
                }

                // Only put the placeholder inside the current Container, skip all
                // items form other containers. This works because when moving
                // an item from one container to another the
                // currentContainer is switched before the placeholder is moved.
                //
                // Without this moving items in "sub-sortables" can cause the placeholder to jitter
                // beetween the outer and inner container.
                if (item.instance !== this.currentContainer) {
                    continue;
                }

                // cannot intersect with itself
                // no useless actions that have been done before
                // no action if the item moved is the parent of the item checked
                if (itemElement !== this.currentItem[0] &&
                    this.placeholder[intersection === 1 ? "next" : "prev"]()[0] !== itemElement &&
                    !$.contains(this.placeholder[0], itemElement) &&
                    (this.options.type === "semi-dynamic" ? !$.contains(this.element[0], itemElement) : true)
                ) {

                    // mjs - we are intersecting an element: trigger the mouseenter event and store this state
                    if (!this.mouseentered) {
                        $(itemElement).mouseenter();
                        this.mouseentered = true;
                    }

                    // mjs - if the element has children and they are hidden, show them after a delay (CSS responsible)
                    if (o.isTree && $(itemElement).hasClass(o.collapsedClass) && o.expandOnHover) {
                        if (!this.hovering) {
                            $(itemElement).addClass(o.hoveringClass);
                            var self = this;
                            this.hovering = window.setTimeout(function() {
                                $(itemElement).removeClass(o.collapsedClass).addClass(o.expandedClass);
                                self.refreshPositions();
                                self._trigger("expand", event, self._uiHash());
                            }, o.expandOnHover);
                        }
                    }

                    this.direction = intersection == 1 ? "down" : "up";

                    // mjs - rearrange the elements and reset timeouts and hovering state
                    if (this.options.tolerance == "pointer" || this._intersectsWithSides(item)) {
                        $(itemElement).mouseleave();
                        this.mouseentered = false;
                        $(itemElement).removeClass(o.hoveringClass);
                        this.hovering && window.clearTimeout(this.hovering);
                        this.hovering = null;

                        // mjs - do not switch container if it's a root item and 'protectRoot' is true
                        // or if it's not a root item but we are trying to make it root
                        if (o.protectRoot
                            && ! (this.currentItem[0].parentNode == this.element[0] // it's a root item
                                  && itemElement.parentNode != this.element[0]) // it's intersecting a non-root item
                        ) {
                            if (this.currentItem[0].parentNode != this.element[0]
                                   && itemElement.parentNode == this.element[0]
                            ) {

                                if ( ! $(itemElement).children(o.listType).length) {
                                    itemElement.appendChild(newList);
                                    o.isTree && $(itemElement).removeClass(o.leafClass).addClass(o.branchClass + ' ' + o.expandedClass);
                                }

                                var a = this.direction === "down" ? $(itemElement).prev().children(o.listType) : $(itemElement).children(o.listType);
                                if (a[0] !== undefined) {
                                    this._rearrange(event, null, a);
                                }

                            } else {
                                this._rearrange(event, item);
                            }
                        } else if ( ! o.protectRoot) {
                            this._rearrange(event, item);
                        }
                    } else {
                        break;
                    }

                    // Clear emtpy ul's/ol's
                    this._clearEmpty(itemElement);

                    this._trigger("change", event, this._uiHash());
                    break;
                }
            }

            // mjs - to find the previous sibling in the list, keep backtracking until we hit a valid list item.
            var previousItem = this.placeholder[0].previousSibling ? $(this.placeholder[0].previousSibling) : null;
            if (previousItem != null) {
                while (previousItem[0].nodeName.toLowerCase() != $(o.listType)[0].nodeName.toLowerCase() || previousItem[0] == this.currentItem[0] || previousItem[0] == this.helper[0]) {
                    if (previousItem[0].previousSibling) {
                        previousItem = $(previousItem[0].previousSibling);
                    } else {
                        previousItem = null;
                        break;
                    }
                }
            }

            // mjs - to find the next sibling in the list, keep stepping forward until we hit a valid list item.
            var nextItem = this.placeholder[0].nextSibling ? $(this.placeholder[0].nextSibling) : null;
            if (nextItem != null) {
                while (nextItem[0].nodeName.toLowerCase() != $(o.listType)[0].nodeName.toLowerCase() || nextItem[0] == this.currentItem[0] || nextItem[0] == this.helper[0]) {
                    if (nextItem[0].nextSibling) {
                        nextItem = $(nextItem[0].nextSibling);
                    } else {
                        nextItem = null;
                        break;
                    }
                }
            }

            this.beyondMaxLevels = 0;

            // mjs - if the item is moved to the left, send it one level up but only if it's at the bottom of the list
            if (parentItem != null
                && nextItem == null
                && ! (o.protectRoot && parentItem[0].parentNode == this.element[0])
                &&
                    (o.rtl && (this.positionAbs.left + this.helper.outerWidth() > parentItem.offset().left + parentItem.outerWidth())
                     || ! o.rtl && (this.positionAbs.left < parentItem.offset().left))
            ) {

                parentItem.after(this.placeholder[0]);
                if (o.isTree && parentItem.children(o.listItem).children(o.listItem + ':visible:not(.ui-sortable-helper)').length < 1) {
                    parentItem.removeClass(this.options.branchClass + ' ' + this.options.expandedClass)
                              .addClass(this.options.leafClass);
                }
                this._clearEmpty(parentItem[0]);
                this._trigger("change", event, this._uiHash());
            }
            // mjs - if the item is below a sibling and is moved to the right, make it a child of that sibling
            else if (previousItem != null
                     && ! previousItem.hasClass(o.disableNestingClass)
                     &&
                        (previousItem.children(o.listType).length && previousItem.children(o.listType).is(':visible')
                         || ! previousItem.children(o.listType).length)
                     && ! (o.protectRoot && this.currentItem[0].parentNode == this.element[0])
                     &&
                        (o.rtl && (this.positionAbs.left + this.helper.outerWidth() < previousItem.offset().left + previousItem.outerWidth() - o.tabSize)
                         || ! o.rtl && (this.positionAbs.left > previousItem.offset().left + o.tabSize))
            ) {

                this._isAllowed(previousItem, level, level+childLevels+1);

                if (!previousItem.children(o.listType).length) {
                    previousItem[0].appendChild(newList);
                    o.isTree && previousItem.removeClass(o.leafClass).addClass(o.branchClass + ' ' + o.expandedClass);
                }

                // mjs - if this item is being moved from the top, add it to the top of the list.
                if (previousTopOffset && (previousTopOffset <= previousItem.offset().top)) {
                    previousItem.children(o.listType).prepend(this.placeholder);
                }
                // mjs - otherwise, add it to the bottom of the list.
                else if(previousItem.children(o.listType).length) {
                    previousItem.children(o.listType)[0].appendChild(this.placeholder[0]);
                }

                this._trigger("change", event, this._uiHash());
            }
            else {
                this._isAllowed(parentItem, level, level+childLevels);
            }

            //Post events to containers
            this._contactContainers(event);

            //Interconnect with droppables
            if($.ui.ddmanager) {
                $.ui.ddmanager.drag(this, event);
            }

            //Call callbacks
            this._trigger('sort', event, this._uiHash());

            this.lastPositionAbs = this.positionAbs;
            return false;

        },

        _mouseStop: function(event, noPropagation) {

            // mjs - if the item is in a position not allowed, send it back
            if (this.beyondMaxLevels) {

                this.placeholder.removeClass(this.options.errorClass);

                if (this.domPosition.prev) {
                    $(this.domPosition.prev).after(this.placeholder);
                } else {
                    $(this.domPosition.parent).prepend(this.placeholder);
                }

                this._trigger("revert", event, this._uiHash());

            }


            // mjs - clear the hovering timeout, just to be sure
            $('.'+this.options.hoveringClass).mouseleave().removeClass(this.options.hoveringClass);
            this.mouseentered = false;
            this.hovering && window.clearTimeout(this.hovering);
            this.hovering = null;

            $.ui.sortable.prototype._mouseStop.apply(this, arguments);

        },

        // mjs - this function is slightly modified to make it easier to hover over a collapsed element and have it expand
        _intersectsWithSides: function(item) {

            var half = this.options.isTree ? .8 : .5;

            var isOverBottomHalf = isOverAxis(this.positionAbs.top + this.offset.click.top, item.top + (item.height*half), item.height),
                isOverTopHalf = isOverAxis(this.positionAbs.top + this.offset.click.top, item.top - (item.height*half), item.height),
                isOverRightHalf = isOverAxis(this.positionAbs.left + this.offset.click.left, item.left + (item.width/2), item.width),
                verticalDirection = this._getDragVerticalDirection(),
                horizontalDirection = this._getDragHorizontalDirection();

            if (this.floating && horizontalDirection) {
                return ((horizontalDirection == "right" && isOverRightHalf) || (horizontalDirection == "left" && !isOverRightHalf));
            } else {
                return verticalDirection && ((verticalDirection == "down" && isOverBottomHalf) || (verticalDirection == "up" && isOverTopHalf));
            }

        },

        _contactContainers: function(event) {

            if (this.options.protectRoot && this.currentItem[0].parentNode == this.element[0] ) {
                return;
            }

            $.ui.sortable.prototype._contactContainers.apply(this, arguments);

        },

        _clear: function(event, noPropagation) {

            $.ui.sortable.prototype._clear.apply(this, arguments);

            // mjs - clean last empty ul/ol
            for (var i = this.items.length - 1; i >= 0; i--) {
                var item = this.items[i].item[0];
                this._clearEmpty(item);
            }

        },

        serialize: function(options) {

            var o = $.extend({}, this.options, options),
                items = this._getItemsAsjQuery(o && o.connected),
                str = [];

            $(items).each(function() {
                var res = ($(o.item || this).attr(o.attribute || 'id') || '')
                        .match(o.expression || (/(.+)[-=_](.+)/)),
                    pid = ($(o.item || this).parent(o.listType)
                        .parent(o.items)
                        .attr(o.attribute || 'id') || '')
                        .match(o.expression || (/(.+)[-=_](.+)/));

                if (res) {
                    str.push(((o.key || res[1]) + '[' + (o.key && o.expression ? res[1] : res[2]) + ']')
                        + '='
                        + (pid ? (o.key && o.expression ? pid[1] : pid[2]) : o.rootID));
                }
            });

            if(!str.length && o.key) {
                str.push(o.key + '=');
            }

            return str.join('&');

        },

        toHierarchy: function(options) {

            var o = $.extend({}, this.options, options),
                sDepth = o.startDepthCount || 0,
                ret = [];

            $(this.element).children(o.items).each(function () {
                var level = _recursiveItems(this);
                ret.push(level);
            });

            return ret;

            function _recursiveItems(item) {
                var id = ($(item).attr(o.attribute || 'id') || '').match(o.expression || (/(.+)[-=_](.+)/));
                if (id) {
                    var currentItem = {"id" : id[2]};
                    if ($(item).children(o.listType).children(o.items).length > 0) {
                        currentItem.children = [];
                        $(item).children(o.listType).children(o.items).each(function() {
                            var level = _recursiveItems(this);
                            currentItem.children.push(level);
                        });
                    }
                    return currentItem;
                }
            }
        },

        toArray: function(options) {

            var o = $.extend({}, this.options, options),
                sDepth = o.startDepthCount || 0,
                ret = [],
                left = 1;

            if (!o.excludeRoot) {
                ret.push({
                    "item_id": o.rootID,
                    "parent_id": null,
                    "depth": sDepth,
                    "left": left,
                    "right": ($(o.items, this.element).length + 1) * 2
                });
                left++
            }

            $(this.element).children(o.items).each(function () {
                left = _recursiveArray(this, sDepth + 1, left);
            });

            ret = ret.sort(function(a,b){ return (a.left - b.left); });

            return ret;

            function _recursiveArray(item, depth, left) {

                var right = left + 1,
                    id,
                    pid;

                if ($(item).children(o.listType).children(o.items).length > 0) {
                    depth ++;
                    $(item).children(o.listType).children(o.items).each(function () {
                        right = _recursiveArray($(this), depth, right);
                    });
                    depth --;
                }

                id = ($(item).attr(o.attribute || 'id')).match(o.expression || (/(.+)[-=_](.+)/));

                if (depth === sDepth + 1) {
                    pid = o.rootID;
                } else {
                    var parentItem = ($(item).parent(o.listType)
                                             .parent(o.items)
                                             .attr(o.attribute || 'id'))
                                             .match(o.expression || (/(.+)[-=_](.+)/));
                    pid = parentItem[2];
                }

                if (id) {
                        ret.push({"item_id": id[2], "parent_id": pid, "depth": depth, "left": left, "right": right});
                }

                left = right + 1;
                return left;
            }

        },

        _clearEmpty: function(item) {
            var o = this.options;

            var emptyList = $(item).children(o.listType);

            if (emptyList.length && !emptyList.children().length && !o.doNotClear) {
                o.isTree && $(item).removeClass(o.branchClass + ' ' + o.expandedClass).addClass(o.leafClass);
                emptyList.remove();
            } else if (o.isTree && emptyList.length && emptyList.children().length && emptyList.is(':visible')) {
                $(item).removeClass(o.leafClass).addClass(o.branchClass + ' ' + o.expandedClass);
            } else if (o.isTree && emptyList.length && emptyList.children().length && !emptyList.is(':visible')) {
                $(item).removeClass(o.leafClass).addClass(o.branchClass + ' ' + o.collapsedClass);
            }

        },

        _getLevel: function(item) {

            var level = 1;

            if (this.options.listType) {
                var list = item.closest(this.options.listType);
                while (list && list.length > 0 &&
                        !list.is('.ui-sortable')) {
                    level++;
                    list = list.parent().closest(this.options.listType);
                }
            }

            return level;
        },

        _getChildLevels: function(parent, depth) {
            var self = this,
                o = this.options,
                result = 0;
            depth = depth || 0;

            $(parent).children(o.listType).children(o.items).each(function (index, child) {
                    result = Math.max(self._getChildLevels(child, depth + 1), result);
            });

            return depth ? result + 1 : result;
        },

        _isAllowed: function(parentItem, level, levels) {
            var o = this.options,
                maxLevels = this.placeholder.closest('.ui-sortable').nestedSortable('option', 'maxLevels'); // this takes into account the maxLevels set to the recipient list

            // mjs - is the root protected?
            // mjs - are we nesting too deep?
            if ( ! o.isAllowed(this.placeholder, parentItem, this.currentItem)) {
                    this.placeholder.addClass(o.errorClass);
                    if (maxLevels < levels && maxLevels != 0) {
                        this.beyondMaxLevels = levels - maxLevels;
                    } else {
                        this.beyondMaxLevels = 1;
                    }
            } else {
                if (maxLevels < levels && maxLevels != 0) {
                    this.placeholder.addClass(o.errorClass);
                    this.beyondMaxLevels = levels - maxLevels;
                } else {
                    this.placeholder.removeClass(o.errorClass);
                    this.beyondMaxLevels = 0;
                }
            }
        }

    }));

    $.mjs.nestedSortable.prototype.options = $.extend({}, $.ui.sortable.prototype.options, $.mjs.nestedSortable.prototype.options);
})(jQuery);
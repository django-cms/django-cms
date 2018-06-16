import $ from 'jquery';
import { debounce } from 'lodash';

// taken from https://tympanus.net/codrops/2014/01/09/sticky-table-headers-columns/
export function initFixedHeaderTables(selector = '.js-table') {
    $(selector).each(function() {
        if ($(this).find('thead').length > 0 && $(this).find('th').length > 0) {
            // Clone <thead>
            var $w = $(window),
                $t = $(this),
                $thead = $t.find('thead').clone(),
                $col = $t.find('thead, tbody').clone();

            // Add class, remove margins, reset width and wrap table
            $t.addClass('sticky-enabled')
                .css({
                    margin: 0,
                    width: '100%',
                })
                .wrap('<div class="sticky-wrap" />');

            if ($t.hasClass('overflow-y')) {
                $t.removeClass('overflow-y')
                    .parent()
                    .addClass('overflow-y');
            }

            // Create new sticky table head (basic)
            $t.after('<table class="table sticky-thead" />');

            // If <tbody> contains <th>, then we create sticky column and intersect (advanced)
            if ($t.find('tbody th').length > 0) {
                $t.after('<table class="table sticky-col" /><table class="table sticky-intersect" />');
            }

            // Create shorthand for things
            var $stickyHead = $(this).siblings('.sticky-thead'),
                $stickyCol = $(this).siblings('.sticky-col'),
                $stickyInsct = $(this).siblings('.sticky-intersect'),
                $stickyWrap = $(this).parent('.sticky-wrap');

            $stickyHead.append($thead);

            $stickyCol
                .append($col)
                .find('thead th:gt(0)')
                .remove()
                .end()
                .find('tbody td')
                .remove();

            $stickyInsct.html('<thead><tr><th>' + $t.find('thead th:first-child').html() + '</th></tr></thead>');

            // Set widths
            var setWidths = function() {
                    $t.find('thead th')
                        .each(function(i) {
                            $stickyHead
                                .find('th')
                                .eq(i)
                                .width($(this).width());
                        })
                        .end()
                        .find('tr')
                        .each(function(i) {
                            $stickyCol
                                .find('tr')
                                .eq(i)
                                .height($(this).height());
                        });

                    // Set width of sticky table head
                    $stickyHead.width($t.width());

                    // Set width of sticky table col
                    $stickyCol
                        .find('th')
                        .add($stickyInsct.find('th'))
                        .width($t.find('thead th').width());
                },
                repositionStickyHead = function() {
                    // Return value of calculated allowance
                    var allowance = calcAllowance();
                    var extraOffset = (window.innerWidth >= 992 ? 40 : 0) + ($('.cms-toolbar').length ? 46 : 0);

                    // If it is not overflowing (basic layout)
                    // Position sticky header based on viewport scrollTop
                    if (
                        $w.scrollTop() > $t.offset().top - extraOffset &&
                        $w.scrollTop() < $t.offset().top + $t.outerHeight() - allowance
                    ) {
                        // When top of viewport is in the table itself
                        $stickyHead.add($stickyInsct).css({
                            opacity: 1,
                            top: $w.scrollTop() - $t.offset().top + extraOffset,
                        });
                    } else {
                        // When top of viewport is above or below table
                        $stickyHead.add($stickyInsct).css({
                            opacity: 0,
                            top: 0,
                        });
                    }
                },
                repositionStickyCol = function() {
                    if ($stickyWrap.scrollLeft() > 0) {
                        // When left of wrapping parent is out of view
                        $stickyCol.add($stickyInsct).css({
                            opacity: 1,
                            left: $stickyWrap.scrollLeft(),
                        });
                    } else {
                        // When left of wrapping parent is in view
                        $stickyCol
                            .css({ opacity: 0 })
                            .add($stickyInsct)
                            .css({ left: 0 });
                    }
                },
                calcAllowance = function() {
                    var a = 0;
                    // Calculate allowance
                    $t.find('tbody tr:lt(3)').each(function() {
                        a += $(this).height();
                    });

                    // Set fail safe limit (last three row might be too tall)
                    // Set arbitrary limit at 0.25 of viewport height, or you can use an arbitrary pixel value
                    if (a > $w.height() * 0.25) {
                        a = $w.height() * 0.25;
                    }

                    // Add the height of sticky header
                    a += $stickyHead.height();
                    return a;
                };

            setWidths();

            $t.parent('.sticky-wrap').on('scroll', function() {
                repositionStickyHead();
                repositionStickyCol();
            });

            $w.on(
                'resize load',
                debounce(function() {
                    setWidths();
                    repositionStickyHead();
                    repositionStickyCol();
                }, 200)
            ).on('scroll', repositionStickyHead);
        }
    });
}

export function initTableCrossHover(selector = '.js-table') {
    const wrapper = $(selector).closest('.sticky-wrap');

    wrapper
        .on('mouseover', 'td, th', e => {
            const cell = $(e.currentTarget);
            const row = cell.parent();

            const cellIndex = cell.index();
            const rowIndex = row.index();

            if (!cellIndex && !rowIndex && !row.closest('.sticky-col').length) {
                return;
            }

            if (rowIndex >= 0 && !row.closest('.sticky-thead').length) {
                wrapper.find('table').each((i, el) =>
                    $(el)
                        .find(`tr:eq(${rowIndex + 1})`)
                        .addClass('hover')
                );
            }

            if (cellIndex >= 1) {
                wrapper.find('tr').each((i, el) => {
                    $(el)
                        .find(`td:eq(${cellIndex - 1})`)
                        .addClass('hover');
                });

                wrapper.find('tr').each((i, el) => {
                    $(el)
                        .find(`th:eq(${cellIndex})`)
                        .addClass('hover');
                });
            }
        })
        .on('mouseout', 'td, th', () => {
            wrapper.find('tr, td, th').removeClass('hover');
        });
}

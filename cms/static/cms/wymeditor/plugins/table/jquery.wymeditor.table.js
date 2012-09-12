/**
 * Copyright (c) 2011 PolicyStat LLC.
 * MIT licensed (MIT-license.txt)
 *
 * @author Wes Winham (winhamwr@gmail.com)
 */

// Fugue icons by Yusuke Kamiyamane http://p.yusukekamiyamane.com/
// and licensed under Creative Commons Attribution

/**
 * A Table editing plugin that gives the user ability to add and remove
 * rows and columns as well as merge rows and columns.
 *
 * @param options A configuration object.
 * @param wym The WYMeditor instance to which the TableEditor should attach.
 * @class
 */
function TableEditor(options, wym) {
    options = jQuery.extend({
        sMergeRowButtonHtml: String() +
            '<li class="wym_tools_merge_row">' +
                '<a name="merge_row" href="#" title="Merge Cells" ' +
                    'style="background-image: ' +
                        "url('" + wym._options.basePath +
                            "plugins/table/table_join_row.png')" + '">' +
                    'Merge Table Row' +
                '</a>' +
            '</li>',

        sMergeRowButtonSelector: "li.wym_tools_merge_row a",

        sAddRowButtonHtml: String() +
            "<li class='wym_tools_add_row'>" +
                "<a name='add_row' href='#' " +
                    "title='Add Row' " +
                    "style='background-image:" +
                        " url(" + wym._options.basePath +
                            "plugins/table/table_insert_row.png)'>" +
                    "Add Table Row" +
                "</a>" +
            "</li>",
        sAddRowButtonSelector: "li.wym_tools_add_row a",

        sRemoveRowButtonHtml: String() +
            "<li class='wym_tools_remove_row'>" +
                "<a name='remove_row' href='#' " +
                    "title='Remove Row' " +
                    "style='background-image: " +
                        "url(" + wym._options.basePath +
                            "plugins/table/table_delete_row.png)'>" +
                    "Remove Table Row" +
                "</a>" +
            "</li>",
        sRemoveRowButtonSelector: "li.wym_tools_remove_row a",

        sAddColumnButtonHtml: String() +
            "<li class='wym_tools_add_column'>" +
                "<a name='add_column' href='#' " +
                    "title='Add Column' " +
                    "style='background-image: " +
                        "url(" + wym._options.basePath +
                            "plugins/table/table_insert_column.png)'>" +
                    "Add Table Column" +
                "</a>" +
            "</li>",
        sAddColumnButtonSelector: "li.wym_tools_add_column a",

        sRemoveColumnButtonHtml: String() +
            "<li class='wym_tools_remove_column'>" +
                "<a name='remove_column' href='#' " +
                    "title='Remove Column' " +
                    "style='background-image: " +
                        "url(" + wym._options.basePath +
                            "plugins/table/table_delete_column.png)'>" +
                    "Remove Table Column" +
                "</a>" +
            "</li>",
        sRemoveColumnButtonSelector: "li.wym_tools_remove_column a",

        enableCellTabbing: true

    }, options);

    this._options = options;
    this._wym = wym;

    this.init();
}

/**
 * Construct and return a table objects using the given options object.
 *
 * @param options The configuration object.
 */
WYMeditor.editor.prototype.table = function (options) {
    var tableEditor = new TableEditor(options, this);
    this.tableEditor = tableEditor;

    return tableEditor;
};

/**
 * Initialize the TableEditor object by adding appropriate toolbar buttons and
 * binding any required event listeners.
 */
TableEditor.prototype.init = function () {
    var wym = this._wym,
        tableEditor = this,
    // Add the tool panel buttons
        tools = $(wym._box).find(
            wym._options.toolsSelector + wym._options.toolsListSelector
        );

    tools.append(tableEditor._options.sMergeRowButtonHtml);
    tools.append(tableEditor._options.sAddRowButtonHtml);
    tools.append(tableEditor._options.sRemoveRowButtonHtml);
    tools.append(tableEditor._options.sAddColumnButtonHtml);
    tools.append(tableEditor._options.sRemoveColumnButtonHtml);

    tableEditor.bindEvents();
    rangy.init();
};

/**
 * Bind all required event listeners, including button listeners and support for
 * tabbing through table cells if enableCellTabbing is true.
 */
TableEditor.prototype.bindEvents = function () {
    var wym = this._wym,
        tableEditor = this;

    // Handle tool button click
    $(wym._box).find(tableEditor._options.sMergeRowButtonSelector).click(function () {
        var sel = rangy.getIframeSelection(wym._iframe);
        tableEditor.mergeRow(sel);
        return false;
    });
    $(wym._box).find(tableEditor._options.sAddRowButtonSelector).click(function () {
        return tableEditor.addRow(wym.selected());
    });
    $(wym._box).find(tableEditor._options.sRemoveRowButtonSelector).click(function () {
        return tableEditor.removeRow(wym.selected());
    });
    $(wym._box).find(tableEditor._options.sAddColumnButtonSelector).click(function () {
        return tableEditor.addColumn(wym.selected());
    });
    $(wym._box).find(tableEditor._options.sRemoveColumnButtonSelector).click(function () {
        return tableEditor.removeColumn(wym.selected());
    });

    // Handle tab clicks
    if (tableEditor._options.enableCellTabbing) {
        $(wym._doc).bind('keydown', tableEditor.keyDown);
    }
};

/**
 * Get the number of columns in a given tr element, accounting for colspan and
 * rowspan. This function assumes that the table structure is valid, and will
 * return incorrect results for uneven tables.
 *
 * @param tr The <tr> node whose number of columns we need to count.
 *
 * @returns {Number} The number of columns in the given tr, accounting for
 * colspan and rowspan.
 */
TableEditor.prototype.getNumColumns = function (tr) {
    var wym = this._wym,
        numColumns = 0,
        table,
        firstTr;

    table = wym.findUp(tr, 'table');
    firstTr = $(table).find('tr:eq(0)');

    // Count the tds and ths in the FIRST ROW of this table, accounting for
    // colspan. We count the first td because it won't have any rowspan's before
    // it to complicate things
    $(firstTr).children('td,th').each(function (index, elmnt) {
        numColumns += TableEditor.GET_COLSPAN_PROP(elmnt);
    });

    return numColumns;
};

/**
    TableEditor.GET_COLSPAN_PROP
    ============================

    Get the integer value of the inferred colspan property on the given cell in
    a cross-browser compatible way that's also compatible across jquery versions.

    jquery 1.6 changed the way .attr works, which affected certain browsers
    differently with regard to colspan and rowspan for cells that didn't explcility
    have that attribue set.
*/
TableEditor.GET_COLSPAN_PROP = function (cell) {
    var colspan = $(cell).attr('colspan');
    if (typeof colspan === 'undefined') {
        colspan = 1;
    }
    return parseInt(colspan, 10);
};

/**
    TableEditor.GET_ROWSPAN_PROP
    ============================

    Get the integer value of the inferred rowspan property on the given cell in
    a cross-browser compatible way that's also compatible across jquery versions.

    See GET_COLSPAN_PROP for details
*/
TableEditor.GET_ROWSPAN_PROP = function (cell) {
    var rowspan = $(cell).attr('rowspan');
    if (typeof rowspan === 'undefined') {
        rowspan = 1;
    }
    return parseInt(rowspan, 10);
};
/**
 * Get the X grid index of the given td or th table cell (0-indexed). This takes
 * in to account all colspans and rowspans.
 *
 * @param cell The td or th node whose X index we're returning.
 */
TableEditor.prototype.getCellXIndex = function (cell) {
    var tableEditor = this,
        i,
        parentTr,
        baseRowColumns,
        rowColCount,
        missingCells,
        rowspanIndexes,
        checkTr,
        rowOffset,
        trChildren,
        elmnt,
        colspan,
        indexCounter,
        cellIndex;
    parentTr = $(cell).parent('tr')[0];

    baseRowColumns = this.getNumColumns(parentTr);

    // Figure out how many explicit cells are missing which is how many rowspans
    // we're affected by
    rowColCount = 0;
    $(parentTr).children('td,th').each(function (index, elmnt) {
        rowColCount += TableEditor.GET_COLSPAN_PROP(elmnt);
    });

    missingCells = baseRowColumns - rowColCount;
    rowspanIndexes = [];
    checkTr = parentTr;
    rowOffset = 1;

    // If this cell is affected by a rowspan from farther up the table,
    // we need to take in to account any possible colspan attributes on that
    // cell. Store the real X index of the cells to the left of our cell to use
    // in the colspan calculation.
    while (missingCells > 0) {
        checkTr = $(checkTr).prev('tr');
        rowOffset += 1;
        trChildren = $(checkTr).children('td,th');
        for (i = 0; i < trChildren.length; i++) {
            elmnt = trChildren[i];
            if (TableEditor.GET_ROWSPAN_PROP(elmnt) >= rowOffset) {
                // Actually affects our source row
                missingCells -= 1;
                colspan = TableEditor.GET_COLSPAN_PROP(elmnt);
                rowspanIndexes[tableEditor.getCellXIndex(elmnt)] = colspan;
            }
        }
    }

    indexCounter = 0;
    cellIndex = null;
    // Taking in to account the real X indexes of all of the columns to the left
    // of this cell, determine the real X index.
    $(parentTr).children('td,th').each(function (index, elmnt) {
        if (cellIndex !== null) {
            // We've already iterated to the cell we're checking
            return;
        }
        // Account for an inferred colspan created by a rowspan from above
        while (typeof rowspanIndexes[indexCounter] !== 'undefined') {
            indexCounter += parseInt(rowspanIndexes[indexCounter], 10);
        }
        if (elmnt === cell) {
            // We're at our cell, no need to keep moving to the right.
            // Signal this by setting the cellIndex
            cellIndex = indexCounter;
            return;
        }
        // Account for an explicit colspan on this cell
        indexCounter += TableEditor.GET_COLSPAN_PROP(elmnt);
    });

    if (cellIndex === null) {
        // Somehow, we never found the cell when iterating over its row.
        throw "Cell index not found";
    }
    return cellIndex;
};

/**
 * Get the number of columns represented by the given array of contiguous cell
 * (td/th) nodes.
 * Accounts for colspan and rowspan attributes.
 *
 * @param cells An array of td/th nodes whose total column span we're checking.
 *
 * @return {Number} The number of columns represented by the "cells"
 */
TableEditor.prototype.getTotalColumns = function (cells) {
    var tableEditor = this,
        rootTr = this.getCommonParentTr(cells),
        baseRowColumns,
        colspanCount,
        rowColCount;

    if (rootTr === null) {
        // Non-contiguous columns
        throw "getTotalColumns only allowed for contiguous cells";
    }

    baseRowColumns = this.getNumColumns(rootTr);

    // Count the number of simple columns, not accounting for rowspans
    colspanCount = 0;
    $(cells).each(function (index, elmnt) {
        colspanCount += TableEditor.GET_COLSPAN_PROP(elmnt);
    });

    // Determine if we're affected by rowspans. If the number of simple columns
    // in the row equals the number of columns in the first row, we don't have
    // any rowspans
    rowColCount = 0;
    $(rootTr).children('td,th').each(function (index, elmnt) {
        rowColCount += TableEditor.GET_COLSPAN_PROP(elmnt);
    });

    if (rowColCount === baseRowColumns) {
        // Easy case. No rowspans to deal with
        return colspanCount;
    } else {
        if (cells.length === 1) {
            // Easy. Just the colspan
            return TableEditor.GET_COLSPAN_PROP(cells[0]);
        } else {
            var lastCell = $(cells).eq(cells.length - 1)[0],
                firstCell = $(cells).eq(0)[0];
            // On jQuery 1.4 upgrade, $(cells).eq(-1)
            return 1 + tableEditor.getCellXIndex(lastCell) -
                tableEditor.getCellXIndex(firstCell);
        }
    }
};

/**
 * Merge the table cells in the given selection using a colspan.
 *
 * @param sel A rangy selection object across which to row merge.
 *
 * @return {Boolean} true if changes are made, false otherwise
 */
TableEditor.prototype.mergeRow = function (sel) {
    var wym = this._wym,
        tableEditor = this,
        i,
        // Get all of the affected nodes in the range
        nodes = [],
        range = null,
        cells,
        rootTr,
        mergeCell,
        $elmnt,
        rowspanProp;

    for (i = 0; i < sel.rangeCount; i++) {
        range = sel.getRangeAt(i);
        nodes = nodes.concat(range.getNodes(false));
    }

    // Just use the td and th nodes
    cells = $(nodes).filter('td,th');
    if (cells.length === 0) {
        return false;
    }

    // If the selection is across multiple tables, don't merge
    rootTr = tableEditor.getCommonParentTr(cells);
    if (rootTr === null) {
        return false;
    }

    mergeCell = cells[0];
    // If any of the cells have a rowspan, create the inferred cells
    $(cells).each(function (i, elmnt) {
        $elmnt = $(elmnt);
        rowspanProp = TableEditor.GET_ROWSPAN_PROP(elmnt);
        if (rowspanProp <= 1) {
            // We don't care about cells without a rowspan
            return;
        }

        // This cell has an actual rowspan, we need to account for it
        // Figure out the x index for this cell in the table grid
        var prevCells = $elmnt.prevAll('td,th'),
            index = tableEditor.getCellXIndex(elmnt),
            // Create the previously-inferred cell in the appropriate index
            // with one less rowspan
            newRowspan = rowspanProp - 1,
            newTd;
        if (newRowspan === 1) {
            newTd = '<td>' + $elmnt.html() + '</td>';
        } else {
            newTd = String() +
                '<td rowspan="' + newRowspan + '">' +
                $elmnt.html() +
                '</td>';
        }
        if (index === 0) {
            $elmnt.parent('tr')
                .next('tr')
                .prepend(newTd);
        } else {
            // TODO: account for colspan/rowspan with insertion
            // Account for colspan/rowspan by walking from right to left looking
            // for the cell closest to the desired index to APPEND to
            var insertionIndex = index - 1,
                insertionCells = $elmnt.parent('tr').next('tr')
                    .find('td,th'),
                cellInserted = false;
            for (i = insertionCells.length - 1; i >= 0; i--) {
                var xIndex = tableEditor.getCellXIndex(insertionCells[i]);
                if (xIndex <= insertionIndex) {
                    $(insertionCells[i]).append(newTd);
                    cellInserted = true;
                    break;
                }
            }
            if (!cellInserted) {
                // Bail out now before we clear HTML and break things
                throw "Cell rowspan invalid";
            }
        }

        // Clear the cell's html, since we just moved it down
        $elmnt.html('');
    });

    // Remove any rowspan from the mergecell now that we've shifted rowspans
    // down
    // ie fails when we try to remove a rowspan for some reason
    try {
        $(mergeCell).removeAttr('rowspan');
    } catch (err) {
        $(mergeCell).attr('rowspan', 1);
    }

    // Build the content of the new combined cell from all of the included cells
    var newContent = '';
    $(cells).each(function (index, elmnt) {
        newContent += $(elmnt).html();
    });

    // Add a colspan to the farthest-left cell
    var combinedColspan = this.getTotalColumns(cells);
    if ($.browser.msie) {
        // jQuery.attr doesn't work for colspan in ie
        mergeCell.colSpan = combinedColspan;
    } else {
        $(mergeCell).attr('colspan', combinedColspan);
    }

    // Delete the rest of the cells
    $(cells).each(function (index, elmnt) {
        if (index !== 0) {
            $(elmnt).remove();
        }
    });

    // Change the content in our newly-merged cell
    $(mergeCell).html(newContent);

    tableEditor.selectElement(mergeCell);

    return true;
};

/**
 * Add a row to the given elmnt (representing a <tr> or a child of a <tr>).
 *
 * @param The node which will have a row appended after its parent row.
 */
TableEditor.prototype.addRow = function (elmnt) {
    var wym = this._wym,
        tr = this._wym.findUp(elmnt, 'tr'),
        numColumns,
        tdHtml,
        i;

    if (tr === null) {
        return false;
    }

    numColumns = this.getNumColumns(tr);

    tdHtml = '';
    for (i = 0; i < numColumns; i++) {
        tdHtml += '<td>&nbsp;</td>';
    }
    $(tr).after('<tr>' + tdHtml + '</tr>');

    return false;
};

/**
 * Remove the given table if it doesn't have any rows/columns.
 *
 * @param table The table to delete if it is empty.
 */
TableEditor.prototype.removeEmptyTable = function (table) {
    var cells = $(table).find('td,th');
    if (cells.length === 0) {
        $(table).remove();
    }
};

/**
 * Remove the row for the given element (representing a <tr> or a child
 * of a <tr>).
 *
 * @param elmnt The node whose parent tr will be removed.
 */
TableEditor.prototype.removeRow = function (elmnt) {
    var wym = this._wym,
        tr = this._wym.findUp(elmnt, 'tr'),
        table;

    if (tr === null) {
        return false;
    }
    table = wym.findUp(elmnt, 'table');
    $(tr).remove();
    this.removeEmptyTable(table);

    return false;
};

/**
 * Add a column to the given elmnt (representing a <td> or a child of a <td>).
 *
 * @param elmnt The node which will have a column appended afterward.
 */
TableEditor.prototype.addColumn = function (elmnt) {
    var wym = this._wym,
        td = this._wym.findUp(elmnt, ['td', 'th']),
        prevTds,
        tdIndex,
        tr,
        newTd = '<td>&nbsp;</td>',
        newTh = '<th>&nbsp;</th>',
        insertionElement;

    if (td === null) {
        return false;
    }
    prevTds = $(td).prevAll();
    tdIndex = prevTds.length;

    tr = wym.findUp(td, 'tr');
    $(tr).siblings('tr').andSelf().each(function (index, element) {
        insertionElement = newTd;
        if ($(element).find('th').length > 0) {
            // The row has a TH, so insert a th
            insertionElement = newTh;
        }

        $(element).find('td,th').eq(tdIndex).after(insertionElement);
    });

    return false;
};

/**
 * Remove the column to the right of the given elmnt (representing a <td> or a
 * child of a <td>).
 */
TableEditor.prototype.removeColumn = function (elmnt) {
    var wym = this._wym,
        td = this._wym.findUp(elmnt, ['td', 'th']),
        table,
        prevTds,
        tdIndex,
        tr;
    if (td === null) {
        return false;
    }
    table = wym.findUp(elmnt, 'table');
    prevTds = $(td).prevAll();
    tdIndex = prevTds.length;

    tr = wym.findUp(td, 'tr');
    $(tr).siblings('tr').each(function (index, element) {
        $(element).find('td,th').eq(tdIndex).remove();
    });
    $(td).remove();
    this.removeEmptyTable(table);

    return false;
};

/**
 * keyDown event handler used for consistent tab key cell movement.
 */
TableEditor.prototype.keyDown = function (evt) {
    //'this' is the doc
    var wym = WYMeditor.INSTANCES[this.title],
        tableEditor = wym.tableEditor;

    if (evt.keyCode === WYMeditor.KEY.TAB) {
        return tableEditor.selectNextCell(wym.selected());
    }

    return null;
};

/**
 * Move the focus to the next cell.
 */
TableEditor.prototype.selectNextCell = function (elmnt) {
    var wym = this._wym,
        tableEditor = this,
        cell = wym.findUp(elmnt, ['td', 'th']),
        nextCells,
        tr,
        nextRows;

    if (cell === null) {
        return null;
    }

    // Try moving to the next cell to the right
    nextCells = $(cell).next('td,th');
    if (nextCells.length > 0) {
        tableEditor.selectElement(nextCells[0]);
        return false;
    }

    // There was no cell to the right, use the first cell in the next row
    tr = wym.findUp(cell, 'tr');
    nextRows = $(tr).next('tr');
    if (nextRows.length !== 0) {
        nextCells = $(nextRows).children('td,th');
        if (nextCells.length > 0) {
            tableEditor.selectElement(nextCells[0]);
            return false;
        }
    }

    // There is no next row. Do a normal tab
    return null;
};

/**
 * Select the given element using rangy selectors.
 */
TableEditor.prototype.selectElement = function (elmnt) {
    var sel = rangy.getIframeSelection(this._wym._iframe),
        range = rangy.createRange(this._wym._doc);

    range.setStart(elmnt, 0);
    range.setEnd(elmnt, 0);
    range.collapse(false);

    try {
        sel.setSingleRange(range);
    } catch (err) {
        // ie8 can raise an "unkown runtime error" trying to empty the range
    }
    // IE selection hack
    if ($.browser.msie) {
        this._wym.saveCaret();
    }
};

/**
 * Get the common parent tr for the given table cell nodes. If the closest parent
 * tr for each cell isn't the same, returns null.
 */
TableEditor.prototype.getCommonParentTr = function (cells) {
    var firstCell,
        parentTrList,
        rootTr;

    cells = $(cells).filter('td,th');
    if (cells.length === 0) {
        return null;
    }
    firstCell = cells[0];
    parentTrList = $(firstCell).parent('tr');

    if (parentTrList.length === 0) {
        return null;
    }
    rootTr = parentTrList[0];

    // Ensure that all of the cells have the same parent tr
    $(cells).each(function (index, elmnt) {
        parentTrList = $(elmnt).parent('tr');
        if (parentTrList.length === 0 || parentTrList[0] !== rootTr) {
            return null;
        }
    });

    return rootTr;
};

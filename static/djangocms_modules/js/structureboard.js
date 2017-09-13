import $ from 'jquery';
import StructureBoard from 'cms.structureboard';

const once = CMS.API.Helpers.once;
const originalShowBoard = StructureBoard.prototype._showBoard;

const removeDisallowedItems = once(() => {
    if ($('.cms-modules-page').length) {
        $('.cms-dragarea > .cms-dragbar > .cms-submenu-add').remove();
        // $('.cms-dragarea > .cms-dragbar > .cms-submenu-dropdown .cms-submenu-item:has(a[data-rel=paste])').remove();
        $('.cms-dragarea > .cms-dragbar > .cms-submenu-dropdown .cms-submenu-item:has(a[href*=alias_plugin])').remove();
    }
});

export function overrideStructureBoard () {
    StructureBoard.prototype._showBoard = function (...args) {
        originalShowBoard.apply(this, args);

        removeDisallowedItems();
    };

    CMS.StructureBoard = StructureBoard;
}


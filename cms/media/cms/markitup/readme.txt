markItUp! 1.1.3

CHANGE LOG
markItUp! 1.1.3 2008-09-12
- Fixed: IE7 preview problem

markItUp! 1.1.2 2008-07-17
- Fixed: Quick fix for Opera 9.5 caret position problem after insertion

markItUp! 1.1.1 2008-06-02
- Fixed: Key events status are passed to callbacks properly
- Improved: ScrollPosition is kept in the preview when its refreshed

markItUp! 1.1.0 2008-05-04
- Modified: Textarea's id is no more moved to the main container
- Modified: NameSpace Span become a Div to remain strict
- Added: Relative path to the script is computed
- Added: Relative path to the script passed to callbacks
- Added: Global instance ID property
- Added: $(element).markItUpRemove() to remove markItUp!
- Added: Resize handle is now optional with resizeHandle property
- Added: Property previewInWindow is added and accept window parameter
- Added: Property previewPosition is added
- Modified: Resize handle is no more displayed in Safari to avoid repetition with the native handle
- Modified: Property previewIframeRefresh become previewAutorefresh
- Modified: Built-in Html Preview call a template file
- Improved: Autorefreshing is now apply for preview in window too
- Improved: Cancel button in prompt window cancel now the whole insertion process
- Improved: Cleaner markItUp! code added to the DOM
- Removed: Depreciated preview properties as previewBaseUrl, previewCharset, previewCssPath, previewBodyId, previewBodyClassName
- Removed: Property previewIframe not longer exists
- Fixed: "Magic markups" works with line feeds
- Fixed: Key events are initialized after insertion
- Fixed: Internet Explorer line feed offset bug
- Fixed: Shortcut keys on Mac OS
- Fixed: Ctrl+click works and doesn't open Mac context menu anymore
- Fixed: Ctrl+click works and doesn't open the page in a new tab anymore
- Fixed: Minor Css modifications

markItUp! 1.0.3 2008-04-04
- Fixed: IE7 Preview empty baseurl problem
- Fixed: IE7 external targeted insertion
- Added: Property scrollPosition is passed to callbacks functions

markItUp! 1.0.2 2008-03-31
- Fixed: IE7 Html preview problems
- Fixed: Selection is kept if nothing is inserted
- Improved: Code minified

markItUp! 1.0.1 2008-03-21
- Removed: Global PlaceHolder
- Modified: Property previewCharset is setted to "utf-8" by default

markItUp! 1.0.0 2008-03-01
- First public release

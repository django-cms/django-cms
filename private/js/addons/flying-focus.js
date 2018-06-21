import $ from 'jquery';

// this was taken from swiss.com

function getBounds(element) {
    var rect = element.getBoundingClientRect();
    var documentElement = document.documentElement;
    var documentView = document.defaultView;
    var body = document.body;
    var topOffset = documentElement.clientTop || body.clientTop || 0;
    var leftOffset = documentElement.clientLeft || body.clientLeft || 0;
    var scrollTop = documentView.pageYOffset || documentElement.scrollTop || body.scrollTop;
    var scrollLeft = documentView.pageXOffset || documentElement.scrollLeft || body.scrollLeft;
    var top = rect.top + scrollTop - topOffset;
    var left = rect.left + scrollLeft - leftOffset;

    return {
        top: top,
        left: left,
        width: rect.width,
        height: rect.height,
        bottom: top + rect.height,
        right: left + rect.width,
    };
}

function getBoundsOfFocusedElements(el) {
    var elementsToFocus = $(el);
    var id = elementsToFocus.attr('id');
    var label = $('label[for="' + id + '"]:visible');

    if (label.length) {
        elementsToFocus = elementsToFocus.add(label.closest('.custom-control'));
    }
    elementsToFocus = elementsToFocus.add(label);
    var bounds = {
        top: 1000000,
        left: 1000000,
        bottom: -10000,
        right: -10000,
    };
    elementsToFocus.each(function() {
        var el = getBounds(this);

        bounds.top = Math.min(bounds.top, el.top);
        bounds.left = Math.min(bounds.left, el.left);
        bounds.bottom = Math.max(bounds.bottom, el.bottom);
        bounds.right = Math.max(bounds.right, el.right);
    });
    bounds.width = bounds.right - bounds.left;
    bounds.height = bounds.bottom - bounds.top;
    return bounds;
}

function addEvent(element, event, callback) {
    if (element.addEventListener) {
        element.addEventListener(event, callback, false);
    } else {
        element.attachEvent('on' + event, callback);
    }
}

function onFocusOut() {
    if (!initialFocus) {
        clearTimeout(showTimeout);
        clearTimeout(hideTimeout);
        hideTimeout = setTimeout(hide, 10);
    }
}
function hide() {
    $(focusElement).removeClass('flying-focus_visible');
    initialFocus = true;
    clearTimeout(resizeTimeout);
}
function show() {
    clearTimeout(hideTimeout);
    clearTimeout(resizeTimeout);
    var e = initialFocus ? 0 : '0.15';

    focusElement.style.transitionDuration = focusElement.style.WebkitTransitionDuration = e + 's';
    checks = 0;
    resizeTimeout = setTimeout(resize, 100);

    if (initialFocus) {
        $(focusElement).addClass('flying-focus_visible');
        initialFocus = false;
    }
}
function resize() {
    var bounds = setDimensions(lastFocusedElement);

    if (bounds.top != currentBounds.top || bounds.left != currentBounds.left || bounds.width != currentBounds.width || bounds.height != currentBounds.height) {
        currentBounds = bounds;
        checks = 0;
    } else {
        checks++;
    }

    if (checks < 3) {
        resizeTimeout = setTimeout(resize, 100);
    } else {
        resizeTimeout = setTimeout(resize, 1000);
    }
}
function setDimensions(focusedElement) {
    if (!initialFocus) {
        var bounds = getBoundsOfFocusedElements(focusedElement);
        if (bounds.top != currentBounds.top || bounds.left != currentBounds.left || bounds.width != currentBounds.width || bounds.height != currentBounds.height) {
            focusElement.style.left = bounds.left + 'px';
            focusElement.style.top = bounds.top + 'px';
            focusElement.style.width = bounds.width + 'px';
            focusElement.style.height = bounds.height + 'px';
        }
        return bounds;
    }
}

var namespace = '.flying-focus';
var justPressed = true;

if (!document.getElementById('flying-focus') && document.documentElement.addEventListener) {
    var focusElement = document.createElement('flying-focus');
    focusElement.id = 'flying-focus';

    $(function() {
        document.body.appendChild(focusElement);
    });

    var lastFocusedElement;
    var showTimeout;
    var initialFocus = true;
    var keyDownTime = 0;
    var currentBounds = {};

    var hideTimeout;
    var resizeTimeout;
    var checks = 0;

    addEvent(document.documentElement, 'keydown', function(e) {
        // all of control keys are before the "a" which is 65. arrows, enter, tab, etc
        if (e.keyCode < 65) {
            keyDownTime = new Date();
            justPressed = true;
        }
    });
    $(document).on('focusin' + namespace, function(e) {
        clearTimeout(hideTimeout);
        showTimeout = setTimeout(function() {
            if (justPressed) {
                var focusedElement = e.target;
                if ('flying-focus' !== focusedElement.id) {
                    var now = new Date();

                    if (!initialFocus || now - keyDownTime < 100) {
                        show();
                        currentBounds = setDimensions(focusedElement);
                        lastFocusedElement = focusedElement;
                    }
                }
            }
        }, 1);
    });
    $(document).on('focusout' + namespace, function() {
        onFocusOut();
    });
    var onMouseClick = function() {
        onFocusOut();
        justPressed = false;
    };
    addEvent(document.documentElement, 'mousedown', onMouseClick);
    addEvent(document.documentElement, 'mouseup', onMouseClick);
    addEvent(window, 'resize', function() {
        setDimensions(lastFocusedElement);
    });
}

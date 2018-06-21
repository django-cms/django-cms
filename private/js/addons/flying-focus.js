import t from 'jquery';

// this was taken from swiss.com

function e() {
    return !1;
}
function getBounds(t) {
    var e = t.getBoundingClientRect(),
        i = document.documentElement,
        n = document.defaultView,
        s = document.body,
        o = i.clientTop || s.clientTop || 0,
        a = i.clientLeft || s.clientLeft || 0,
        r = n.pageYOffset || i.scrollTop || s.scrollTop,
        l = n.pageXOffset || i.scrollLeft || s.scrollLeft,
        h = e.top + r - o,
        u = e.left + l - a;
    return {
        top: h,
        left: u,
        width: e.width,
        height: e.height,
        bottom: h + e.height,
        right: u + e.width,
    };
}
function n(el) {
    var elementsToFocus = t(el),
        id = elementsToFocus.attr('id'),
        label = t('label[for="' + id + '"]:visible');

    if (label.length) {
        elementsToFocus = elementsToFocus.add(label.closest('.custom-control'));
    }
    elementsToFocus = elementsToFocus.add(label);
    var bounds = {
        top: 1e6,
        left: 1e6,
        bottom: -1e4,
        right: -1e4,
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
function s(t, e, i) {
    t.addEventListener ? t.addEventListener(e, i, !1) : t.attachEvent('on' + e, i);
}
function o() {
    g || (clearTimeout(m), clearTimeout(w), (w = setTimeout(a, 10)));
}
function a() {
    t(c).removeClass('flying-focus_visible'), (g = !0), clearTimeout($);
}
function r() {
    clearTimeout(w), clearTimeout($);
    var e = g ? 0 : p / 1e3;
    (c.style.transitionDuration = c.style.WebkitTransitionDuration = e + 's'),
        (k = 0),
        ($ = setTimeout(l, 100)),
        g && (t(c).addClass('flying-focus_visible'), (g = !1));
}
function l() {
    var t = h(f);
    t.top != y.top || t.left != y.left || t.width != y.width || t.height != y.height ? ((y = t), (k = 0)) : k++,
        ($ = 3 > k ? setTimeout(l, 100) : setTimeout(l, 1e3));
}
function h(t) {
    if (!g) {
        var e = n(t);
        return (
            (e.top != y.top || e.left != y.left || e.width != y.width || e.height != y.height) &&
                ((c.style.left = e.left + 'px'),
                (c.style.top = e.top + 'px'),
                (c.style.width = e.width + 'px'),
                (c.style.height = e.height + 'px')),
            e
        );
    }
}
var u = '.flying-focus',
    d = !0;
if (!document.getElementById('flying-focus') && document.documentElement.addEventListener) {
    var c = document.createElement('flying-focus');
    (c.id = 'flying-focus'),
        t(function() {
            document.body.appendChild(c);
        });
    var p = 150;
    !!navigator.userAgent.match(/gecko/i) && !navigator.userAgent.match(/webkit/i);
    var f,
        m,
        g = !0,
        v = 0,
        y = {};
    s(
        document.documentElement,
        'keydown',
        function(t) {
            t.keyCode < 65 && ((v = new Date()), (d = !0));
        },
        !0
    ),
        t(document).on('focusin' + u, function(t) {
            clearTimeout(w),
                (m = setTimeout(function() {
                    var i = e(t.target);
                    if (i || d) {
                        var n = t.target;
                        if ('flying-focus' !== n.id) {
                            var s = new Date();
                            (!i && g && s - v > 100) || (r(), (y = h(n)), (f = n));
                        }
                    }
                }, 1));
        }),
        t(document).on('focusout' + u, function() {
            o();
        });
    var b = function() {
        o(), (d = !1);
    };
    s(document.documentElement, 'mousedown', b),
        s(document.documentElement, 'mouseup', b),
        s(window, 'resize', function() {
            h(f);
        });
    var w,
        $,
        k = 0;
}

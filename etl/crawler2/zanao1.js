function get_m(e) {
    for (var t = "", r = 0; r < e; r++)
        t += Math.floor(10 * Math.random());
    return t
}

m = get_m(20)


function get_h() {
    var e = (new Date).getTime().toString().substr(0, 10);
    return parseInt(e, 10)
}

td = get_h()


function n(n, r) {
    var t = (65535 & n) + (65535 & r);
    return (n >> 16) + (r >> 16) + (t >> 16) << 16 | 65535 & t
}

function r(r, t, e, o, u, c) {
    return n((f = n(n(t, r), n(o, c))) << (i = u) | f >>> 32 - i, e);
    var f, i
}

function t(n, t, e, o, u, c, f) {
    return r(t & e | ~t & o, n, t, u, c, f)
}

function e(n, t, e, o, u, c, f) {
    return r(t & o | e & ~o, n, t, u, c, f)
}

function o(n, t, e, o, u, c, f) {
    return r(t ^ e ^ o, n, t, u, c, f)
}

function u(n, t, e, o, u, c, f) {
    return r(e ^ (t | ~o), n, t, u, c, f)
}

function c(r, c) {
    var f, i, a, h, g;
    r[c >> 5] |= 128 << c % 32,
        r[14 + (c + 64 >>> 9 << 4)] = c;
    var l = 1732584193
        , v = -271733879
        , d = -1732584194
        , C = 271733878;
    for (f = 0; f < r.length; f += 16)
        i = l,
            a = v,
            h = d,
            g = C,
            l = t(l, v, d, C, r[f], 7, -680876936),
            C = t(C, l, v, d, r[f + 1], 12, -389564586),
            d = t(d, C, l, v, r[f + 2], 17, 606105819),
            v = t(v, d, C, l, r[f + 3], 22, -1044525330),
            l = t(l, v, d, C, r[f + 4], 7, -176418897),
            C = t(C, l, v, d, r[f + 5], 12, 1200080426),
            d = t(d, C, l, v, r[f + 6], 17, -1473231341),
            v = t(v, d, C, l, r[f + 7], 22, -45705983),
            l = t(l, v, d, C, r[f + 8], 7, 1770035416),
            C = t(C, l, v, d, r[f + 9], 12, -1958414417),
            d = t(d, C, l, v, r[f + 10], 17, -42063),
            v = t(v, d, C, l, r[f + 11], 22, -1990404162),
            l = t(l, v, d, C, r[f + 12], 7, 1804603682),
            C = t(C, l, v, d, r[f + 13], 12, -40341101),
            d = t(d, C, l, v, r[f + 14], 17, -1502002290),
            l = e(l, v = t(v, d, C, l, r[f + 15], 22, 1236535329), d, C, r[f + 1], 5, -165796510),
            C = e(C, l, v, d, r[f + 6], 9, -1069501632),
            d = e(d, C, l, v, r[f + 11], 14, 643717713),
            v = e(v, d, C, l, r[f], 20, -373897302),
            l = e(l, v, d, C, r[f + 5], 5, -701558691),
            C = e(C, l, v, d, r[f + 10], 9, 38016083),
            d = e(d, C, l, v, r[f + 15], 14, -660478335),
            v = e(v, d, C, l, r[f + 4], 20, -405537848),
            l = e(l, v, d, C, r[f + 9], 5, 568446438),
            C = e(C, l, v, d, r[f + 14], 9, -1019803690),
            d = e(d, C, l, v, r[f + 3], 14, -187363961),
            v = e(v, d, C, l, r[f + 8], 20, 1163531501),
            l = e(l, v, d, C, r[f + 13], 5, -1444681467),
            C = e(C, l, v, d, r[f + 2], 9, -51403784),
            d = e(d, C, l, v, r[f + 7], 14, 1735328473),
            l = o(l, v = e(v, d, C, l, r[f + 12], 20, -1926607734), d, C, r[f + 5], 4, -378558),
            C = o(C, l, v, d, r[f + 8], 11, -2022574463),
            d = o(d, C, l, v, r[f + 11], 16, 1839030562),
            v = o(v, d, C, l, r[f + 14], 23, -35309556),
            l = o(l, v, d, C, r[f + 1], 4, -1530992060),
            C = o(C, l, v, d, r[f + 4], 11, 1272893353),
            d = o(d, C, l, v, r[f + 7], 16, -155497632),
            v = o(v, d, C, l, r[f + 10], 23, -1094730640),
            l = o(l, v, d, C, r[f + 13], 4, 681279174),
            C = o(C, l, v, d, r[f], 11, -358537222),
            d = o(d, C, l, v, r[f + 3], 16, -722521979),
            v = o(v, d, C, l, r[f + 6], 23, 76029189),
            l = o(l, v, d, C, r[f + 9], 4, -640364487),
            C = o(C, l, v, d, r[f + 12], 11, -421815835),
            d = o(d, C, l, v, r[f + 15], 16, 530742520),
            l = u(l, v = o(v, d, C, l, r[f + 2], 23, -995338651), d, C, r[f], 6, -198630844),
            C = u(C, l, v, d, r[f + 7], 10, 1126891415),
            d = u(d, C, l, v, r[f + 14], 15, -1416354905),
            v = u(v, d, C, l, r[f + 5], 21, -57434055),
            l = u(l, v, d, C, r[f + 12], 6, 1700485571),
            C = u(C, l, v, d, r[f + 3], 10, -1894986606),
            d = u(d, C, l, v, r[f + 10], 15, -1051523),
            v = u(v, d, C, l, r[f + 1], 21, -2054922799),
            l = u(l, v, d, C, r[f + 8], 6, 1873313359),
            C = u(C, l, v, d, r[f + 15], 10, -30611744),
            d = u(d, C, l, v, r[f + 6], 15, -1560198380),
            v = u(v, d, C, l, r[f + 13], 21, 1309151649),
            l = u(l, v, d, C, r[f + 4], 6, -145523070),
            C = u(C, l, v, d, r[f + 11], 10, -1120210379),
            d = u(d, C, l, v, r[f + 2], 15, 718787259),
            v = u(v, d, C, l, r[f + 9], 21, -343485551),
            l = n(l, i),
            v = n(v, a),
            d = n(d, h),
            C = n(C, g);
    return [l, v, d, C]
}

function f(n) {
    var r, t = "", e = 32 * n.length;
    for (r = 0; r < e; r += 8)
        t += String.fromCharCode(n[r >> 5] >>> r % 32 & 255);
    return t
}

function i(n) {
    var r, t = [];
    for (t[(n.length >> 2) - 1] = void 0,
        r = 0; r < t.length; r += 1)
        t[r] = 0;
    var e = 8 * n.length;
    for (r = 0; r < e; r += 8)
        t[r >> 5] |= (255 & n.charCodeAt(r / 8)) << r % 32;
    return t
}

function a(n) {
    var r, t, e = "";
    for (t = 0; t < n.length; t += 1)
        r = n.charCodeAt(t),
            e += "0123456789abcdef".charAt(r >>> 4 & 15) + "0123456789abcdef".charAt(15 & r);
    return e
}

function h(n) {
    return unescape(encodeURIComponent(n))
}

function g(n) {
    return function (n) {
        return f(c(i(n), 8 * n.length))
    }(h(n))
}

function l(n, r) {
    return function (n, r) {
        var t, e, o = i(n), u = [], a = [];
        for (u[15] = a[15] = void 0,
            o.length > 16 && (o = c(o, 8 * n.length)),
            t = 0; t < 16; t += 1)
            u[t] = 909522486 ^ o[t],
                a[t] = 1549556828 ^ o[t];
        return e = c(u.concat(i(r)), 512 + 8 * r.length),
            f(c(a.concat(e), 640))
    }(h(n), h(r))
}

function get_b(n, r, t) {
    return r ? t ? l(r, n) : a(l(r, n)) : t ? g(n) : a(g(n))
}


b = get_b("zzu" + "_" + m + "_" + td + "_1b6d2514354bc407afdd935f45521a8c")

function get_result() {
    result = {
        "X-Sc-Ah": b,
        "X-Sc-Alias": "nankai",
        "X-Sc-Nd": m,
        "X-Sc-Od": "azl6TDJyZG1nWlcxbG9PYmxIbktmWnFsckxXV3pwZk9sMkp3a2NtZGY5T0V6YXFYeFgycnM4YXJmdHlGWXQ2dGpLTEsySmltaVphWG5YeVR1SW1MdDREYm5hK3pqYWVZdU5DbGxvV2dxNldJanNEUGdjMkYxNGhsaVpMR2lZdXdsS3F5ck1sK2dkUzlwNlhQaDNqT2pJNk1xNStEczFpV2VWZHFwUT09",
        "X-Sc-Td": td
    }
    return result
}
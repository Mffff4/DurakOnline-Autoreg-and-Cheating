const crypto = require("crypto")

const Groups = {
    2048: {
        N: "AC6BDB41 324A9A9B F166DE5E 1389582F AF72B665 1987EE07 FC319294 3DB56050 A37329CB B4A099ED 8193E075 7767A13D D52312AB 4B03310D CD7F48A9 DA04FD50 E8083969 EDB767B0 CF609517 9A163AB3 661A05FB D5FAAAE8 2918A996 2F0B93B8 55F97993 EC975EEA A80D740A DBF4FF74 7359D041 D5C33EA7 1D281E44 6B14773B CA97B43A 23FB8016 76BD207A 436C6481 F1D2B907 8717461A 5B9D32E6 88F87748 544523B5 24B0D57D 5EA77A27 75D2ECFA 032CFBDB F52FB378 61602790 04E57AE6 AF874E73 03CE5329 9CCC041C 7BC308D8 2A5698F3 A8D0C382 71AE35F8 E9DBFBB6 94B5C803 D89F7AE4 35DE236D 525F5475 9B65E372 FCD68EF2 0FA7111F 9E4AFF73",
        g: "02"
    }
}

function i(t) {
    return new TextEncoder("utf-8").encode(t)
}

function cFunc(t, r) {
    return t + r
}

function uFunc(t, r) {
    return t * r
}

function sFunc(t, r){
    var e = function(t, r) {
        return t % r
    }(t, r);
    return function(t) {
        return t < BigInt(0)
    }(e) && (e = cFunc(e, r)),
    e
}

function S(t){
    var r = t.B
      , e = t.k
      , n = t.x
      , o = t.a
      , i = t.u
      , a = t.N
      , h = t.g
      , l = cFunc(uFunc(i.bi(), n.bi()), o.bi())
      , p = sFunc(uFunc(fFunc(h.bi(), n.bi(), a.bi()), e.bi()), a.bi())
      , v = fFunc(sFunc(function(t, r) {
        return t - r
    }(r.bi(), p), a.bi()), l, a.bi());
    return new objectManager(v)
}

function getRandomBits() {
    const randomBits = crypto.getRandomValues(new Uint8Array(256));
    return new objectManager(randomBits);
}

function base64ToUint8Array(base64String) {
    const binaryString = atob(base64String);
    const length = binaryString.length;
    const uint8Array = new Uint8Array(length);

    for (let i = 0; i < length; i++) {
        uint8Array[i] = binaryString.charCodeAt(i);
    }

    return uint8Array;
}

function initGroup(t){
    if (!Groups[t]){
        throw new Error("group ".concat(t, " not supported."));
    }
    const group = Groups[t];
    const groupHex = group.N;
    const groupGenerator = group.g;

    return {
        N: new objectManager(groupHex.split(/\s/).join("")),
        g: new objectManager(groupGenerator)
    }
}

function fFunc(base, exponent, modulus) {
    if (modulus === BigInt(1)) {
        return BigInt(0);
    }

    let result = BigInt(1);
    base %= modulus;

    while (exponent > BigInt(0)) {
        if (exponent % BigInt(2) === BigInt(1)) {
            result = (result * base) % modulus;
        }

        exponent >>= BigInt(1);
        base = (base * base) % modulus;
    }

    return result;
}

class AccountManager{
    constructor(account_name) {
        this._privateValue = undefined;
        this._publicValue = undefined;
        this.accountName = account_name
    }

    privateValue() {
        if (typeof this._privateValue === "undefined") {
            this._privateValue = getRandomBits()
        }
        return this._privateValue;
    }

    publicValue(){
        if (typeof this._publicValue === "undefined"){
            const N = initGroup("2048");
            const j = N.N;
            const D = N.g;

            this._publicValue = j.pad(new objectManager(fFunc(D.bi(), this.privateValue().bi(), j.bi())))
        }
        return this._publicValue
    }

    async getEvidenceMessage(r){
        const e = r.iterations;
        const n = r.serverPublicValue;
        const o = r.salt;
        const a = r.password;
        const u = r.protocol;
        const c = void 0 === u ? "s2k" : u;
        const s = this.privateValue();
        const f = this.publicValue();
        const h = new objectManager(n);
        const l = e;
        const p = new objectManager(o)
        const v = new objectManager(i(this.accountName.toLowerCase()))
        let params1 = {
            password: new objectManager(i(a)),
            s: p,
            i: l,
            protocol: c
        }
        let result = await Encrypter.I(params1).then(d1 => {
            const d = new objectManager(d1)

            const SMTH = initGroup("2048");
            const j = SMTH.N;
            const D = SMTH.g;
            const k = j;
            const g = (objectManager.concat(k, k.pad(D))).getHash()

            let params2 = {
                s: p,
                I: v,
                P: d
            }

            const y = Encrypter.A(params2)
            const b = Encrypter.E({
                A: f,  // the only random value
                B: h,
                N: j
            });
            const w = S({
                B: h,  // static
                k: g,  // static
                x: y,  // static
                a: s,  // random
                u: b,  // random
                N: j,  // static
                g: D  // static
            })

            const x = Encrypter.R({
                S: w,
                N: j
            })

            // console.log(x)
            let params3 = {
                I: v,
                s: p,
                A: f,  // random
                B: h,  // serverKey
                K: x,  // random
                N: j,
                g: D
            }

            const M = Encrypter.T(params3)

            const _ = Encrypter.O({
                A: f,
                M1: M,
                K: x
            })

            const result = {
                M1: M.getBase64(),
                M2: _.getBase64()
            }
            return result
        })
        return result
    }
}



class Encrypter {
    static async I(r){
        const e = r.password;
        const n = r.s;
        const o = r.i;
        const a = r.protocol;
        const u = void 0 === a ? "s2k" : a;

        const c = e.getHash();
        //  <7d 13 ab 1e 75 6f 1e fc 19 0f 0a 43 f1 31 55 2d 10 ff 54 78 9f 7b b2 29 90 60 e2 f6 de 56 40 cd>,
        const key = await crypto.subtle.importKey("raw", "s2k" === u ? c.buffer() : i(c.hex()), "PBKDF2", !1, ["deriveBits"]);

        const hashed =  crypto.subtle.deriveBits({
            name: "PBKDF2",
            salt: n.buffer(),
            iterations: o,
            hash: {
                name: "SHA-256"
            }
        }, key, 256);
        return hashed
    }

    static O(r){
        const e = r.A;
        const n = r.M1;
        const o = r.K;
        const i = objectManager.concat(e, n, o).getHash()
        return i
    }

    static T(r){
        const e = r.I;
        const n = r.s;
        const o = r.A;
        const i = r.B;
        const a = r.K;
        const u = r.N;
        const c = r.g;

        const s = (u.pad(c)).getHash()
        const f = u.getHash()

        const p = f.bi();
        const v = s.bi();

        const h = new objectManager(p ^ v)

        const l = e.getHash()
        return (objectManager.concat(h, l, n, o, i, a)).getHash()
    }

    static A(r){
        const e = r.s;
        r.I;
        const o = r.P;
        const i = new objectManager(new Uint8Array([":".charCodeAt(0)]))
        const n = new objectManager("");
        const a = objectManager.concat(n, i, o)
        const u = a.getHash()
        const c = objectManager.concat(e, u)
        return c.getHash()
    }

    static E(t) {
        var r = t.A
          , e = t.B
          , n = t.N;
        return objectManager.concat(n.pad(r), n.pad(e)).getHash()
    }

    static R(t) {
        var r = t.S;
        return t.N.pad(r).getHash()
    }
}

class objectManager {
    constructor(r) {
        this._bi = undefined;
        this._buffer = undefined;
        this._hex = undefined;
        this._hash = undefined;
        this._base64 = undefined;

        if (typeof r === "string") {
            this._hex = r;
        } else if (r instanceof ArrayBuffer) {
            this._buffer = new Uint8Array(r);
        } else if (r instanceof Uint8Array) {
            this._buffer = r;
        } else {
            this._bi = r;
        }
    }

    bi() {
        if (typeof this._bi === "undefined") {
            this._bi = BigInt("0x" + this.hex());
        }
        return this._bi;
    }

    buffer() {
        if (typeof this._buffer === "undefined") {
            this._buffer = this.hexToBuffer(this.hex());
        }
        return this._buffer;
    }

    hex() {
        if (typeof this._hex === "undefined") {
            if (typeof this._bi !== "undefined") {
                let hexString = this._bi.toString(16);
                if (hexString.length % 2 !== 0) {
                    hexString = "0" + hexString;
                }
                this._hex = hexString;
            } else {
                this._hex = this._buffer.reduce((acc, val) => acc + val.toString(16).padStart(2, "0"), "");
            }
        }
        return this._hex;
    }

    getHash() {
        if (typeof this._hash === "undefined"){
            this._hash = new objectManager(crypto.createHash("sha256").update(this.buffer()).digest("hex"))
        }
        return this._hash
    }

    pad(r) {
        function smthf(t, r) {
            for (var e = new Uint8Array(r), n = r - t.length, o = 0; o < t.length; o++)
                e[o + n] = t[o];
            return e
        }

        return new objectManager(smthf(r.buffer(), this.buffer().length));
    }

    getBase64() {
        if (typeof this._base64 === "undefined") {
            this._base64 = btoa(String.fromCharCode.apply(String, Array.from(this.buffer())));
        }
        return this._base64;
    }

    static concat() {
        let e = new Array(r);
        for (let r = arguments.length, n = 0; n < r; n++)
            e[n] = arguments[n];
        let o = e.map((function(ww) {
            return ww.buffer()
        }
        ));

        const concatenatedArray = o.reduce((acc, curr) => {
          const combinedArray = new Uint8Array(acc.length + curr.length);
          combinedArray.set(acc, 0);
          combinedArray.set(curr, acc.length);
          return combinedArray;
        });
        return new objectManager(concatenatedArray)
    }

    hexToBuffer(hexString) {
        if (hexString.length % 2 === 1) {
            hexString = "0" + hexString;
        }
        let length = hexString.length / 2;
        let buffer = new Uint8Array(length);
        for (let i = 0; i < length; i++) {
            let hexByte = hexString.substr(2 * i, 2);
            let byte = parseInt(hexByte, 16);
            if (isNaN(byte)) {
                throw new Error("String contains non hexadecimal value: '" + hexString + "'");
            }
            buffer[i] = byte;
        }
        return buffer;
    }
}

let r = null
function get_encrypted_a(EMAIL) {
    r = new AccountManager(EMAIL)
    const c = r.publicValue()
    const arr = new Uint8Array(c.buffer())
    const encrypted_a = btoa(String.fromCharCode.apply(String, arr))
    return encrypted_a
}

async function get_complete_data(s) {
    const f = s.iterations
    const h = s.serverPublicValue
    const l = s.salt
    const p = s.c
    const v = s.password
    const d = s.protocol

    let data = await r.getEvidenceMessage({
       iterations: f,
       serverPublicValue: new Uint8Array(base64ToUint8Array(h)),
       salt: new Uint8Array(base64ToUint8Array(l)),
       password: v,
       protocol: d
    })
    return data
}

module.exports = {
    get_encrypted_a,
    get_complete_data
};
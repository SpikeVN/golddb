# golddb
scrapes gold price for research and archival purposes. most prices are scraped using html, but some endpoints has json which can be easily fetched instead.

## doji
doji prices uses a json api but encrypted for obfuscation. however, obscurity is never security. so in that spirit, here is in-depth documentation of how doji does their obfuscation.

```js
decrypt(base64EncodedData) {
    // the data field in /api/TablePrice/GetTablePrice is base64 encrypted.
    // let's decode that first.
    let decoded = Base64.parse(base64EncodedData);  
    // the cipher is AES-256. the first 16 bytes of the encoded data is the IV.
    let iv = decoded.words.slice(0, 4);
    // the rest is ciphertext.
    let ciphertext = decoded.words.slice(4);
    // this is their hardcoded encyrption key.
    // it was originally split into 8 piecies like this in the js:
    // chunks = ['7a4b8c3d','1e9f2a5b','6c0d4e8f','3a7b1c5d','9e2f6a0b','4c8d3e7f','1a5b9c2d','6e0f4a8b']
    let key = Hex.parse("22ea3986b2msh4cb9edf36095d68p19ce07jsnd508f634d98d");
    // get our juice
    let result = AES.decrypt({ciphertext}, key, {iv, mode: CBC, padding: PKCS7});

    return JSON.parse(result.toString(Utf8));
}
```

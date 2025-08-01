import CryptoJS from 'crypto-js';
import fs from 'fs';
import https from 'https';
const key = CryptoJS.enc.Utf8.parse("1234123412ABCDEF");
const iv = CryptoJS.enc.Utf8.parse("ABCDEF1234123412");
const path = 'https://jc.pep.com.cn/js/chunk-a4502b30.d47163c2.js.map';
let str = '';
const cookie = 'acw_sc__v3=example'; // 请根据实际情况设置cookie
https.get(path, { headers: { Cookie: cookie } }, (res) => {
    const filePath = path.split('/').pop();
    const writeStream = fs.createWriteStream(filePath!);
    res.pipe(writeStream);
    writeStream.on('finish', () => {
        writeStream.close();
        console.log(`Downloaded ${filePath}`);
        let content = fs.readFileSync(path.split('/').pop()!, 'utf8');
        let start = content.indexOf('"var str = \\"') + '"var str = \\"'.length;
        while (start < content.length && content[start] !== '\\') {
            str += content[start];
            start++;
        }
        let encryptedHexStr = CryptoJS.enc.Hex.parse(str);
        let srcs = CryptoJS.enc.Base64.stringify(encryptedHexStr);
        let decrypt = CryptoJS.AES.decrypt(srcs, key, {
            iv: iv,
            mode: CryptoJS.mode.CBC,
            padding: CryptoJS.pad.Pkcs7,
        });
        let decryptedStr = decrypt.toString(CryptoJS.enc.Utf8);
        let data = JSON.parse(decryptedStr.toString()).data;
        let list: Array<Data> = [];
        let xklist: Data | undefined = undefined;
        for (let item of data) {
            if (item.xd == "高中") {
                xklist = list.find(x => x.xk == item.xk);
                if (!xklist) {
                    list.push({
                        xk: item.xk,
                        xklist: [{
                            title: item.title,
                            id: item.id
                        }]
                    });
                }
                else {
                    xklist.xklist.push({
                        title: item.title,
                        id: item.id
                    });
                }
            }
        }
        content = JSON.stringify(list, null, 2);
        fs.writeFileSync('data.json', content, 'utf8');
        console.log('Data processed and saved to data.json');
    });
});
class Item {
    constructor(title, id) {
        this.title = title;
        this.id = id;
    }
    title: string;
    id: string;
}
class Data {
    constructor(xk, xklist) {
        this.xk = xk;
        this.xklist = xklist;
    }
    xk: string;
    xklist: Array<Item>;
}